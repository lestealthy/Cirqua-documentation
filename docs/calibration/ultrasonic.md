---

title: Ultrasonic Calibration

description: Tank geometry, the Node 1 volume doubling factor, mounting offset error and a verification procedure for the HC-SR04 volume channels.

---

# Ultrasonic Calibration

Three nodes measure liquid level with an HC-SR04 ultrasonic sensor and convert the

echo time into litres using a cylinder formula. All three implementations are

independent sketches, so they do **not** share constants even where they happen to

agree.

Claim types used throughout: **Firmware implementation**, **Engineering

interpretation**, **Recommendation**.

## Tank geometry, per node

**Firmware implementation.** `TANK_HEIGHT` and `TANK_RADIUS` are separate `const float`

declarations in each sketch. They are not shared and they are not identical.

| Node | Role | `TANK_HEIGHT` (cm) | `TANK_RADIUS` (cm) | `pulseIn` timeout (µs) | Sketch |

|---|---|---|---|---|---|

| 1 | Collection Tank A (`TAV`) | 260.0 | 110.0 | 30000 | `Node1.ino` |

| 2 | Feeding Tank B (`TBV`) | 178.0 | 59.5 | 20000 | `Node2.ino` |

| 4 | Effluent (`TCV` / `EV`) | 178.0 | 59.5 | 25000 | `Node4.ino` |

The differing timeouts are a real behaviour difference in the field. Node 1 will keep

listening for an echo nearly 1.5× longer than Node 2 before declaring failure, so a

marginal sensor may appear healthy on Node 1 and invalid on Node 2.

## The measurement chain

**Firmware implementation.** Every node performs the same four steps, in-line, with no

shared helper:

1. Drive TRIG low 2–3 µs, high 10 µs, low.

2. `pulseIn(ECHO, HIGH, <node timeout>)`.

3. `distance = duration * 0.0343f / 2.0f` — centimetres, the `/ 2` for the round trip.

4. `waterHeight = TANK_HEIGHT - distance`, clamped to `[0, TANK_HEIGHT]` on Nodes 1, 2

   and 4.

5. `volume = (3.14159f * TANK_RADIUS * TANK_RADIUS * waterHeight) / 1000.0f` — litres.

`0.0343f` cm/µs corresponds to approximately 343 m/s in air. It is a hard-coded

constant, not a measured value, and it does not account for the substantial

systematic error that HC-SR04 units have when the transducers are not at normal

operating temperature. See [Maintained accuracy](../sensors/ultrasonic.md).

Node 4 additionally rejects physically impossible distances before doing any

arithmetic: `distance < 0 || distance > TANK_HEIGHT + 20` returns invalid. Nodes 1 and

2 do **not** apply this rejection — they rely on the height clamp alone. This is a

behavioural difference worth knowing when a Node 1 or Node 2 reading looks odd.

### Node 1

```cpp

--8<-- "assets/snippets/node1-ultrasonic-measurement.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>Task_Sensors_Node1</code> ·

lines 77–116 · commit <code>db6d9b8</code>
</div>

Note the inline comment `// True 0-offset ultrasonic calculation`, and then, three lines

later, the multiplication by `2.0f`.

### Node 4

```cpp

--8<-- "assets/snippets/node4-tank-volume.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>readTankVolume</code> ·

lines 313–368 · commit <code>db6d9b8</code>
</div>

## The Node 1 ×2 factor — an empirical fudge with no geometric justification

**Firmware implementation.** After computing the cylinder volume, Node 1 does:

```cpp

currentRead.volumeLiters = (int)(volumeLiters * 2.0f);

```

**Engineering interpretation.** This is not derivable from geometry. Nothing in the

cylinder formula, the radius, or the height could produce a factor of two. It is an

empirical compensation for something the author observed — most plausibly a mismatch

between the assumed 110 cm radius and the actual tank radius, a cross-sectional

asymmetry, or an under-reading sensor. The source does not say which, and no comment

explains it.

The consequences are worth stating plainly:

- The `TAV` value on the Node 1 LCD and in the upstream frame is **twice** the volume

  the geometry says it should be.

- Node 2 and Node 4 do **not** apply any such factor. `TBV` and `EV`/`TCV` are direct

  cylinder volumes. Do not compare `TAV` with `TBV` without accounting for this.

- The low-volume alarms on Node 1 (`TAV < 5000` → `LOW TAV`) are therefore evaluated

  against the doubled figure. The effective geometric threshold is 2500 L of real

  volume, not 5000 L.

- The factor is a **hard-coded literal**. Correcting it requires editing `Node1.ino`,

  rebuilding and re-flashing. There is no serial command, no NVS key and no runtime

  path to change it.

**Recommendation.** Treat the ×2 as unverified until an independent fill–drain

comparison is performed. Do not present `TAV` as a metrologically traceable volume.

### Procedure to determine the true factor empirically

**Recommendation.** This requires physical access to Collection Tank A and a known

volume of water. It is destructive of time, not of equipment.

1. Record the tank's true internal dimensions: measure the internal diameter at three

   heights and take the mean radius. Record the internal height from the sensor

   mounting face to the tank floor. Write these down; they are the only independent

   reference available.

2. Empty the tank fully and read the Node 1 LCD. Record the `C…L` value. A non-zero

   reading on an empty tank indicates the sensor is seeing a floor or wall return

   inside `TANK_HEIGHT` metres — this is a mounting problem, not a scale problem.

3. Add a known volume of water (a metered bowser, a calibrated vessel, or a full

   known-capacity container). Record the true litres added and the LCD value.

4. Repeat at three or more levels spanning the working range.

5. Compute the ratio at each level:

   ```text

   ratio = LCD litres / true litres

   ```

6. If the ratio is consistent across levels, the discrepancy is a pure scale error.

   The correct literal replaces `2.0f`:

   ```text

   true_factor = 2.0f / mean_ratio

   ```

   For example, if the LCD consistently reads 1.25× the true volume, the required

   literal is `2.0f / 1.25 = 1.6f`.

7. If the ratio is **not** consistent across levels, a single multiplicative constant

   cannot fix the tank. The problem is almost certainly sensor offset (see below), tank

   shape, or the radius value. Do not compensate with a fudge factor; change the

   geometry constants instead.

8. Record the result, edit `Node1.ino`, rebuild, re-flash, and repeat the procedure

   against the modified firmware to confirm.

> **Not verified from the current source.** The origin, date and author of the ×2

> factor. There is no calibration record, no commit comment and no test data in the

> repository that explains it.

## Sensor mounting offset — a systematic error with no compensation

**Firmware implementation.** All three nodes compute:

```cpp

float waterHeight = TANK_HEIGHT - distance;

```

There is no `SENSOR_OFFSET` constant anywhere in the codebase. The source comment in

Node 1 calls this a "True 0-offset ultrasonic calculation".

**Engineering interpretation.** This formula is only correct if the acoustic

reference point is exactly the top of the tank wall. In practice the HC-SR04

transducers sit in a waterproof housing some distance below the rim, and the face of

the tank is not perfectly flat.

If the sensor face is `d` cm **below** the top of the tank, then for every reading:

```text

reported height = true height + d

```

because the sensor measures from its own face, not from the rim, and the firmware

subtracts that distance from the full `TANK_HEIGHT`. The error is a constant offset in

centimetres which becomes a much larger error in litres as the tank fills — for the Node

4/Node 2 geometry (radius 59.5 cm) the cross-sectional area is about 11 120 cm², so

every 1 cm of offset is roughly 111 L of systematic error.

Two practical consequences:

- A dry tank will report a non-zero height, and possibly a large litre figure.

- An offset can be partially *masked* by the ×2 factor on Node 1, which makes diagnosis

  harder.

**Recommendation.** Measure and record the offset `d` at installation. If `d` is not

negligible relative to the accuracy you need, the only correct fix in the current

firmware is to change `TANK_HEIGHT` to the true distance from the sensor face to the

tank floor and treat the tank height as an effective height. That is a re-flash.

> **Not verified from the current source.** The as-built mounting depth of any sensor.

> No enclosure drawings, photographs or wiring records exist in the repository.

## Step-by-step verification procedure

**Recommendation.** Applicable to Nodes 1, 2 and 4. Allow 30–60 minutes per tank.

1. **Check the physical state first.** Inspect the transducer face for condensation,

   biofilm, dust or a cracked epoxy face. Clean it. Do not calibrate through a dirty

   lens — the reading will drift again within days.

2. **Confirm the node is healthy first.** Node 1 must not be showing `ERROR` or

   `WAITING`; Node 4's `EV:` field must be updating. A stale LCD tells you nothing about

   the sensor. See the

   [startup checklist](../field-service/startup-checklist.md).

3. **Establish an empty-tank datum.** Empty the tank as far as practicable. Note the

   LCD value and the time. Repeat three times to confirm the reading is stable, not

   fluctuating.

4. **Measure the true height** with a tape or dip stick from the water surface to the

   tank floor, and cross-check against the sensor face position.

5. **Compute the expected litres** independently:

   ```text

   expected_litres = 3.14159 * r_cm * r_cm * true_height_cm / 1000

   ```

   Using the radius you measured in step 1, not the 110.0 / 59.5 constants.

6. **Compare.** For Node 2 and Node 4 the LCD value should match the independent

   calculation within your measurement uncertainty. For Node 1, compare against the

   independent calculation multiplied by the factor you intend to keep.

7. **Add a known volume and repeat** at two further levels.

8. **Decide the correction:**

   - Constant offset, consistent ratio → adjust the relevant `const float`

     (geometry or the Node 1 factor) and re-flash.

   - Offset error, varying ratio → fix the mounting or the geometry constants; do not

     add a multiplier.

   - No discrepancy within tolerance → record "verified, no change required".

9. **Re-verify after any firmware change** by repeating steps 3–7.

10. **Record the outcome** in the maintenance log

    ([Maintenance](../field-service/maintenance.md)), including the readings before

    and after, because there is no in-firmware calibration history.

## What this calibration does not cover

- No temperature compensation. `0.0343f` is fixed; sound speed in air varies with

  temperature and humidity.

- No averaging, median filtering or hysteresis on the level value. A single spurious

  echo is published immediately.

- No plausibility check on Node 1 or Node 2 beyond the height clamp.

- No tank shape other than a right circular cylinder is supported. A conical, elliptical

  or partially obstructed tank will read wrong and no constant can express it.

## Related pages

- [Calibration index](index.md)

- [Ultrasonic sensor](../sensors/ultrasonic.md)

- [Node 1](../nodes/node1.md) · [Node 2](../nodes/node2.md) · [Node 4](../nodes/node4.md)

- [Troubleshooting: volume readings](../field-service/troubleshooting.md)

- [Hardware validation](../validation/hardware-validation.md)
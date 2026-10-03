---

title: Ultrasonic Level

description: HC-SR04 time-of-flight tank level and volume measurement on Nodes 1, 2 and 4 — pins, trigger timing, per-node geometry and the Node 1 volume doubling.

---

# Ultrasonic Level

The CIRQUA cluster measures liquid level in three tanks with an ultrasonic

time-of-flight rangefinder and converts the result to litres using a

cylindrical tank model. The same sensor type is instantiated three times,

independently configured, with different pins, different echo timeouts and —

importantly — different tank geometry.

| Role | Node | Frame field | Meaning |

|---|---|---|---|

| Collection Tank A | Node 1 | `TAV` | Volume in litres, integer |

| Feeding Tank B | Node 2 | `TBV` | Volume in litres, 2 decimal places |

| Effluent tank | Node 4 | `TCV` (Node 4) / `EV` (Node 4 SMTP) | Volume in litres, integer |

<div class="cirqua-identity">

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Nodes</span>

    <span class="cirqua-identity__value">1, 2, 4</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">GPIO</span>

    <span class="cirqua-identity__value">N1 TRIG <code>2</code> / ECHO <code>17</code><br>N2 TRIG <code>16</code> / ECHO <code>17</code><br>N4 TRIG <code>4</code> / ECHO <code>2</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Interface</span>

    <span class="cirqua-identity__value">Digital time-of-flight (trigger out, echo in)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Signal type</span>

    <span class="cirqua-identity__value">Pulse-width measurement, `pulseIn()`</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware reading function</span>

    <span class="cirqua-identity__value"><code>Task_Sensors_Node1</code>, <code>Task_Sensors_Node2</code>, <code>readTankVolume()</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Status</span>

    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--verified">verified in source</span></span>

  </div>

</div>

## Purpose and measured quantity

The ultrasonic head performs a **non-contact distance measurement** from the

transducer down to the liquid surface. The firmware subtracts that distance

from a configured tank height to obtain water height, then converts height to

volume assuming a right circular cylinder.

The quantity that leaves the node is **volume in litres**, not a raw distance

or a depth in centimetres. Distance and height are intermediate values and

never appear on the wire.

## Physical principle

> **Manufacturer specification.** `HC-SR04` is the part name written in a

> firmware source comment. This documentation has not been checked against a

> HC-SR04 datasheet, and no range, beam angle, accuracy, resolution or supply

> specification is asserted here. The exact fitted part number and its

> manufacturer are **Not verified from the current source.**

Generic principle, independent of any particular part: a piezoelectric

transducer emits a short burst of ultrasound when its trigger line is pulsed,

and then acts as a receiver for the echo returned from the liquid surface. The

round-trip travel time is measured and converted to distance using the speed of

sound in air, `d = t x c / 2`, where the division by two accounts for the fact

that the pulse travels to the surface and back.

The relationship relies on the speed of sound being approximately constant over

the expected temperature range. The firmware uses a single fixed constant and

applies no temperature correction to it — see

[Limitations](#limitations).

## Electrical interface

Not an ADC channel. This is a **digital, two-wire time-of-flight interface**:

* One output pin (TRIG) driven by the firmware.

* One input pin (ECHO) read by `pulseIn()` with a hardware-independent busy

  wait and an explicit timeout.

What the firmware configures:

```cpp

pinMode(PIN_N1_TRIG, OUTPUT);

pinMode(PIN_N1_ECHO, INPUT);

digitalWrite(PIN_N1_TRIG, LOW);

```

The trigger sequence is the same on all three nodes: a short low period, a

10 µs high pulse, then low again.

| Node | TRIG pin | ECHO pin | Trigger low | Trigger high | Echo timeout |

|---|---|---|---|---|---|

| 1 | GPIO 2 | GPIO 17 | 2 µs | 10 µs | 30000 µs |

| 2 | GPIO 16 | GPIO 17 | 2 µs | 10 µs | 20000 µs |

| 4 | GPIO 4 | GPIO 2 | 3 µs | 10 µs | 25000 µs |

!!! WARNING

    Node 1 and Node 2 both use **GPIO 17 for ECHO**, and Node 4 uses GPIO 2 for

    ECHO while Node 1 uses GPIO 2 for TRIG. Pin numbers do **not** carry across

    nodes. Never wire two nodes' transducers together by number. See

    [GPIO Map](../hardware/gpio-map.md).

## How CIRQUA uses it

### Distance from echo width

All three nodes use the same speed-of-sound constant, expressed in centimetres

per microsecond, and halve it for the round trip:

```text

distance_cm = pulse_us * 0.0343 / 2

```

`0.0343f` is the value in the firmware. It is a compile-time constant with no

per-node override and no temperature compensation.

### Node 1 — Collection Tank A

Node 1 runs the measurement in `Task_Sensors_Node1` on a 500 ms period.

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

### Node 2 — Feeding Tank B

Node 2 runs the measurement inside `Task_Sensors_Node2` on a 1000 ms period,

alongside the DS18B20, dissolved oxygen and DHT11 acquisitions.

```cpp

--8<-- "assets/snippets/node2-sensor-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>Task_Sensors_Node2</code> ·

lines 98–220 · commit <code>db6d9b8</code>
</div>

### Node 4 — Effluent tank

Node 4 factors the measurement into a separate function so that it can return

a validity result to the caller.

```cpp

--8<-- "assets/snippets/node4-tank-volume.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>readTankVolume()</code> ·

lines 313–368 · commit <code>db6d9b8</code>
</div>

### Cylinder volume model

Every node converts height to volume with the same expression, using the

literal `3.14159f` rather than a mathematical constant:

```text

volume_litres = (3.14159 * radius_cm * radius_cm * height_cm) / 1000

```

The `/ 1000` converts cubic centimetres to litres.

### Per-node tank geometry

The geometry is **not shared**. Each sketch carries its own `TANK_HEIGHT` and

`TANK_RADIUS` constants, and they differ:

| Node | Role | `TANK_HEIGHT` cm | `TANK_RADIUS` cm | Echo timeout µs |

|---|---|---|---|---|

| 1 | Collection Tank A (`TAV`) | 260.0 | 110.0 | 30000 |

| 2 | Feeding Tank B (`TBV`) | 178.0 | 59.5 | 20000 |

| 4 | Effluent (`TCV` / `EV`) | 178.0 | 59.5 | 25000 |

Nodes 2 and 4 therefore use identical geometry constants, but still differ in

trigger low time, timeout and post-processing.

### Node 1 doubles the result — read this before trusting `TAV`

```cpp

currentRead.volumeLiters = (int)(volumeLiters * 2.0f);

```

> **Engineering interpretation, flagged deliberately.** Node 1 multiplies the

> geometrically computed litres by `2.0f` and truncates to an integer. This is

> **not** derivable from the cylinder formula. It is a hard-coded empirical

> compensation factor that the firmware author presumably added to reconcile

> the calculated volume with a measured or expected quantity. Its physical

> justification is **not documented in the source**, and it is not accounted

> for by any geometry constant. Treat `TAV` as requiring empirical calibration,

> and treat the factor of two as an unexplained empirical fudge rather than a

> physical model.

Nodes 2 and 4 apply **no** such multiplier. Node 2 reports a floating-point

value; Node 4 truncates to `int`.

### Clamping and validity differ per node

The three nodes do not treat out-of-range measurements the same way:

| Node | Failure condition | Height clamping | Reported |

|---|---|---|---|

| 1 | `duration == 0` (no echo) | Lower clamp at 0 only; no upper clamp | Invalid |

| 2 | `duration == 0` (no echo) | Clamped to `[0, TANK_HEIGHT]` | Invalid |

| 4 | `duration <= 0`, or `distance < 0`, or `distance > TANK_HEIGHT + 20` | Clamped to `[0, TANK_HEIGHT]` | Invalid |

Node 4 is the only node that performs an **explicit plausibility rejection** of

the distance itself, refusing anything further than 20 cm above the configured

tank height. Node 1 and Node 2 will accept an implausibly short echo and turn

it into a near-full tank.

## Calibration

| What | Where | How |

|---|---|---|

| Tank height and radius | Compile-time constants, per node sketch | Edit and re-flash; not field-adjustable |

| Speed of sound `0.0343f` | Compile-time constant, identical on all nodes | Edit and re-flash |

| Echo timeout | Compile-time constant, per node | Edit and re-flash |

| Node 1 volume doubling | Compile-time literal `2.0f` | Edit and re-flash |

There is **no runtime calibration path** for level. Nothing about the

ultrasonic measurement is adjustable over the serial link; the only runtime

calibration console in the firmware belongs to

[Node 4](../nodes/node4.md) and covers pH and EC only.

Procedure reference: [Ultrasonic Volume Calibration](../calibration/ultrasonic.md).

## Expected values and typical ranges

The following bounds are **derived from the firmware constants only** and are

not field-verified performance figures:

| Node | Maximum volume the constants can produce | Firmware low-volume alert |

|---|---|---|

| 1 | `pi x 110² x 260 / 1000` ≈ **9879.0 L**, doubled by the Node 1 factor to a reported maximum of **19758 L** | `TAV < 5000 L` → `LOW TAV` |

| 2 | `pi x 59.5² x 178 / 1000` ≈ **1979.7 L** | `TBV < 500 L` → `LOW TBV` |

| 4 | `pi x 59.5² x 178 / 1000` ≈ **1979.7 L** | none |

The low-volume alert thresholds are Node 1 constants (`TAV_LOW_ALERT_TH`,

`TBV_LOW_ALERT_TH`), evaluated in Node 1's LCD status logic, not by the

measuring nodes.

Expected working distance range, beam pattern, minimum detectable level change

and accuracy:

> **Not verified from the current source.** No such figure appears in the

> firmware or in any document available to this documentation set. Do not quote

> an accuracy or range figure for this sensor without a datasheet.

## Failure modes

What the firmware treats as invalid:

* **No echo within the timeout.** `pulseIn()` returns 0 and the node marks the

  reading invalid. On Nodes 1 and 2 this is the *only* invalid condition. A

  disconnected or reversed transducer, a transducer fouled with solids, or a

  liquid surface too rough or too close to produce a return all present this

  way.

* **Node 4 only:** a distance above `TANK_HEIGHT + 20` is rejected outright.

What a field technician should look for when a level reading is implausible

but the node reports it as valid:

* **Height pinned at maximum.** A short or spurious echo produces

  `distance ≈ 0`, `height ≈ TANK_HEIGHT` and a full-tank volume. On Node 1 this

  reads as 19758 L, well above the 9879 L the geometry can actually hold.

* **Height pinned at zero.** An echo that arrives late, or a surface that the

  beam grazes rather than strikes, gives a large distance and a near-empty

  tank. Node 1 and Node 2 clamp this to zero and report `0` as a *valid*

  reading.

* **Constant value.** A transducer disconnected mid-run will tend towards a

  stable, implausible number rather than to an invalid flag.

* **Systematic offset.** A tilted transducer, condensation on the face, or a

  probe mounted at the wrong height above the maximum water line shifts every

  reading by a constant. The firmware has no way to detect this.

Note that the node health flags in the frame (`|node1:`, `|node2:`, `|node4:`)

only reflect these validity flags. A physically wrong but structurally valid

reading is reported as healthy.

## Environmental considerations

* **Speed of sound varies with air temperature and humidity.** The firmware

  uses a single fixed constant, so the conversion carries a temperature-

  dependent bias. The magnitude is **not quantified here** — the firmware

  applies no correction and the documentation set contains no measurement to

  derive one from.

* **Foam, aeration and suspended solids.** A turbulent or foaming surface

  scatters the echo. Very fine bubbles can reflect ultrasound as effectively as

  a solid surface, so the level may be read too low or too high relative to

  the actual liquid body.

* **Condensation on the transducer face.** Reduces coupling and can cause

  intermittent loss of echo. Node 1's alert thresholds include a humidity

  threshold of 80 % on Node 2's DHT11, which is a proxy for enclosure

  condensation risk — but the humidity is measured at Node 2, not at the

  Node 1 tank.

* **Direct sun and enclosure temperature.** A hot enclosure raises the air

  temperature around the transducer and biases the speed-of-sound constant.

* **Nearby hard surfaces.** Walls and tank internals close to the beam path can

  produce spurious early returns.

* **Aeration from inflow.** A falling inlet jet will disturb the surface

  directly under a downward-looking transducer.

## Limitations

Firmware-level limitations, stated plainly:

* **No temperature compensation** for the speed-of-sound constant.

* **No filtering.** There is one measurement per cycle, used directly. Node 1

  samples at 2 Hz (500 ms), Nodes 2 and 4 at 1 Hz. No median, no moving

  average, no outlier rejection.

* **No plausibility check on Nodes 1 and 2.** Only a zero-length echo is

  rejected. Node 4 is the only node that bounds the distance.

* **Node 1 applies an unexplained factor of two** to the computed volume.

  Until this is characterised, `TAV` should not be compared directly against a

  dip stick or a tank data sheet.

* **`pulseIn()` blocks the calling task.** The echo wait is a busy wait, so the

  sensor task occupies its core for the duration of the echo. This is a

  deliberate trade for timing simplicity and matters on Node 1, which samples

  at twice the rate of the other nodes.

* **Assumes a right circular cylinder.** Any taper, baffle, sump, internal

  partition or non-cylindrical section will produce a volume error that grows

  with level. Nothing in the firmware or the constants accounts for this.

* **Tank geometry is per-sketch, not shared.** Editing Node 2's constants has

  no effect on Node 4, even though the two are identical today. Divergence

  between physically identical tanks is possible and would be silent.

* **No units or provenance on the wire.** A consumer cannot tell from the

  `TAV`, `TBV` or `TCV` field whether a compensation factor has been applied.

* **No trend, totalising or alarm output from the sensor itself.** Low-volume

  alerting is a Node 1 LCD status string only; it is not transmitted as a

  distinct signal.

## Maintenance and replacement

Level heads are the components most exposed to fouling and to accidental

damage during tank cleaning. Replacement is a wiring-and-flash operation, not

a calibration one, provided the new device is mounted at the same height above

the maximum water line as the old one.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md).

Routine checks: [Maintenance](../field-service/maintenance.md).

Wiring and connector details: [Wiring](../hardware/wiring.md).

> **Not verified from the current source.** Cable types, lengths, gauges and

> connector pinouts are not documented in the repository, and no schematic or

> wiring diagram exists there.

## Where it is used

| Node | GPIO TRIG | GPIO ECHO | Reading function | Frame field | Valid flag |

|---|---|---|---|---|---|

| 1 | 2 | 17 | `Task_Sensors_Node1` | `TAV` | `node1` |

| 2 | 16 | 17 | `Task_Sensors_Node2` | `TBV` | `node2` |

| 4 | 4 | 2 | `readTankVolume()` | `TCV` (`Node4`) / `EV` (`Node4_SMTP`) | `node4` |

Frame format detail: [Message Format](../communication/message-format.md).

Node-level detail: [Node 1](../nodes/node1.md),

[Node 2](../nodes/node2.md), [Node 4](../nodes/node4.md).

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),

branch `main`, commit

[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)

(short `db6d9b8`).

Snippets used on this page:

| Snippet | Source path | Symbol | Lines |

|---|---|---|---|

| `node1-ultrasonic-measurement` | `FreeRTOS_Implementation/Node1/Node1.ino` | `Task_Sensors_Node1` | 77–116 |

| `node2-sensor-task` | `FreeRTOS_Implementation/Node2/Node2.ino` | `Task_Sensors_Node2` | 98–220 |

| `node4-tank-volume` | `FreeRTOS_Implementation/Node4/Node4.ino` | `readTankVolume()` | 313–368 |

| `node1-pin-definitions` | `FreeRTOS_Implementation/Node1/Node1.ino` | — | 5–35 |

| `node2-pin-definitions` | `FreeRTOS_Implementation/Node2/Node2.ino` | — | 10–32 |

| `node4-pin-definitions` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 10–41 |

Everything on this page is *firmware implementation* unless explicitly labelled

otherwise. Statements about the sensor device itself are *unverified*: the part

name `HC-SR04` is taken from a firmware source comment and no manufacturer

specification is asserted.

Related: [Sensors overview](index.md) ·

[Ultrasonic Volume Calibration](../calibration/ultrasonic.md) ·

[Known Limitations](../validation/known-limitations.md) ·

[Sensor Replacement](../field-service/sensor-replacement.md)


---
title: Sensor Replacement
description: Per-sensor replacement procedure with the GPIO pin differences between nodes, post-replacement actions and level-shift warnings.
---

# Sensor Replacement

This page gives the procedure for replacing a failed sensor on any node.

!!! danger

    **Do not swap peripherals between nodes by pin number.** The GPIO assignments are
    *not* consistent across nodes. Node 1 uses **GPIO 2 for ultrasonic TRIG**; Node 4 uses
    **GPIO 2 for ultrasonic ECHO**. Node 1 and Node 2 both use **GPIO 17** for ECHO.
    Node 2 uses **GPIO 27 for the DHT11**; Node 4 uses **GPIO 27 for the DS18B20**.
    Always identify the node first, then use *that node's* table:
    [Node identification](node-identification.md).

!!! warning

    Isolate the power source before opening any enclosure. There is no published
    schematic — see the safety admonition on the
    [Field service index](index.md#safety-first).

Claim types used throughout: **Firmware implementation**, **Engineering
interpretation**, **Recommendation**.

## The rule that matters

**Firmware implementation.** GPIO 16 and GPIO 17 are used on Node 2 for the ultrasonic.
Node 1 uses GPIO 2 and 17. Node 4 uses GPIO 4 and 2. There is no bootloader or jumper
that reassigns pins — the assignment is a `#define` in the sketch, fixed at compile time.

**Engineering interpretation.** **Re-flashing is required if the replacement sensor
needs a different pin.** The table below answers "does this need a re-flash?" per
sensor/node combination. In the common case — replacing like with like on the same node —
no re-flash is needed and calibration can be preserved.

## Replacement matrix

| Sensor | Node | GPIO | Re-flash needed? | Post-replacement action |
|---|---|---|---|---|
| **HC-SR04 ultrasonic** | 1 | TRIG **2**, ECHO **17** | Only if pins change | Re-verify geometry; **re-check the ×2 volume factor** |
| **HC-SR04 ultrasonic** | 2 | TRIG **16**, ECHO **17** | Only if pins change | Re-verify geometry |
| **HC-SR04 ultrasonic** | 4 / SMTP | TRIG **4**, ECHO **2** | Only if pins change | Re-verify geometry; confirm the distance-rejection gate (`<= TANK_HEIGHT + 20`) still behaves |
| **DS18B20 water temperature** | 2 | **4** (1-Wire) | Only if pins change | Confirm 1-Wire bus integrity; Node 2 reads non-blocking |
| **DS18B20 submerged** | 4 / SMTP | **27** (1-Wire) | Only if pins change | Confirm `getDeviceCount() > 0`; resolution is fixed at 10-bit, blocking |
| **DHT11 ambient** | 2 | **27** | Only if pins change | Confirm readings; Node 2 has no range gate, only a `NaN` check |
| **DHT11 ambient** | 4 / SMTP | **5** | Only if pins change | Confirm readings; Node 4 range-gates −20…80 °C and 0…100 % |
| **pH module** | 4 / SMTP | **13** (ADC2) | Only if pins change | **Re-run the full pH calibration** |
| **Turbidity module** | 4 / SMTP | **14** (ADC2) | Only if pins change | Re-verify against the visual cross-check; there is no calibration constant to restore |
| **EC module** | 4 / SMTP | **12** (ADC2) | Only if pins change | **Re-run the K-factor determination** |
| **Dissolved oxygen module** | 2 | **34** (ADC1, input only) | Only if pins change | Re-check against an independent reference; no constants are stored |
| **Flow sensor** | 3 | **23** (input, `INPUT_PULLUP`, ISR on FALLING) | Only if pins change | Confirm pulses are counted; `FLM:0` is never reported as invalid |

**Firmware implementation.** There is no sensor auto-detection, no device address
configuration, no EEPROM record of which sensor was fitted and no per-sensor serial
number handling anywhere in the firmware.

> **Not verified from the current source.** Part numbers, connector pinouts, cable types,
> lengths and gauges for any sensor. Only HC-SR04, DS18B20 and DHT11 are named in the
> source; the DO, flow, pH and EC modules are unnamed.

## Level-shift warning — ultrasonic Echo

**Firmware implementation.** Every node reads the HC-SR04 Echo pin **directly** into an
ESP32 GPIO. There is no divider, buffer, level shifter or series resistor anywhere in the
firmware, and no such component is documented in the repository.

**Engineering interpretation.** The HC-SR04 is conventionally operated from 5 V and its
Echo output is a 5 V logic level. The ESP32 GPIO inputs are **not 5 V tolerant**. Reading
Echo directly into the ESP32 relies on the input's internal clamp and the module's actual
output behaviour, which is outside the ESP32's specified operating range.

**Recommendation.**

- If you are replacing the controller or the ultrasonic module, check the Echo output
  level against the ESP32's permitted input range before reconnecting.
- If the Echo level exceeds the ESP32's limit and the node behaves erratically — random
  resets, or an ultrasonic reading that only fails in some conditions — a divider or level
  shifter on the Echo line is the thing to try. Note that a divider attenuates the signal,
  so re-verify the distance readings afterwards; the firmware has no calibration for it.
- Record whatever arrangement you find, because **no wiring diagram exists in the
  repository** and the current state is not documented anywhere.

> **Not verified from the current source.** The supply voltage of the fitted HC-SR04
> modules, and whether any level shifting is present in the as-built hardware.

## General procedure

**Recommendation.**

1. **Identify the node** with certainty — label, QR sticker, or the methods on
   [Node identification](node-identification.md).
2. **Record the state before you touch anything.** Send `STATUS` on Node 4 and copy the
   output verbatim; photograph the Node 1 and Node 4 displays. This gives you the
   calibration state and a before/after comparison.
3. **Isolate the power.**
4. **Photograph the existing wiring** before disconnecting anything. There is no schematic
   — your photograph may be the only record.
5. **Disconnect the sensor**, noting which conductor goes where.
6. **Fit the replacement**, matching the pin roles for *this* node from the matrix above.
7. **Restore power and confirm the node boots** — follow
   [Startup checklist](startup-checklist.md).
8. **Confirm the channel is valid**, using `STATUS` on Node 4 rather than the LCD. Node 4's
   display prints values without checking the validity flags.
9. **Perform the post-replacement actions** for that sensor below.
10. **Record** everything in the maintenance log
    ([Maintenance](maintenance.md)).

## Post-replacement actions by sensor

### Ultrasonic (all three nodes)

**Recommendation.**

- [ ] Re-verify against an independent height measurement — the full procedure is in
      [Ultrasonic calibration](../calibration/ultrasonic.md#step-by-step-verification-procedure).
- [ ] **On Node 1 specifically, re-check the ×2 volume factor.** The hard-coded `2.0f`
      multiplier is not adjusted for the new unit, and a replacement module may have a
      different zero-offset or a different face geometry. Establish the ratio
      (`LCD litres / true litres`) at two or more levels before accepting the reading.
- [ ] On Node 4, confirm distances beyond `TANK_HEIGHT + 20` cm are rejected — a new
      module with a longer range can return spurious far echoes in a large tank.
- [ ] If the replacement has a different pinout or the Echo level differs, treat the
      first reading as unverified until step 8 of the general procedure is complete.

### DS18B20 water/submerged temperature

**Firmware implementation.** Node 2 calls `setWaitForConversion(false)` and re-requests
conversions each cycle (non-blocking). Node 4 calls `setResolution(10)` and
`setWaitForConversion(true)` — **blocking by design**, with a source comment noting that
about 187.5 ms at 10-bit resolution is acceptable at 1 Hz. Node 4 also warns at boot if
`getDeviceCount() == 0`.

**Recommendation.**

- [ ] Confirm the probe count is seen. On Node 4, a warning at boot means the bus is not
      enumerating.
- [ ] Confirm the temperature is plausible for the water.
- [ ] Seal and strain-relieve the cable at the new entry point. A 1-Wire bus is
      sensitive to ingress and strain; see [Maintenance](maintenance.md).
- [ ] Node 4's resolution is fixed at 10-bit (0.25 °C steps) in the firmware. You cannot
      change it without a re-flash.
- [ ] Node 4's temperature feeds the pH and EC compensation, so re-check those channels
      after replacing this probe.

### DHT11 ambient temperature and humidity

**Recommendation.**

- [ ] Confirm readings appear within about 2 s (the firmware paces DHT11 reads to at least
      2000 ms) and that Node 1's status word leaves `OVERTEMP` / `HI HUMID` / `HOT+HUM`
      if the new probe reads normally.
- [ ] Note the validation asymmetry: Node 2 accepts any non-`NaN` reading with no range
      gate; Node 4 rejects ambient temperature outside −20…80 °C and humidity outside
      0…100 %; `Node4_SMTP` uses the ungated Node 2-style check. A DHT11 that returns
      out-of-range values will therefore behave differently on different builds.
- [ ] Allow the replacement to settle in its installed position before judging accuracy.

### pH module

**Recommendation.**

- [ ] **The stored calibration is no longer valid for the new electrode.** The slope and
      offset in NVS were derived for the old unit.
- [ ] Note the buffer procedure uses **two** points — see
      [pH calibration](../calibration/ph.md#full-two-point-buffer-calibration).
- [ ] After changing `SET:PH_S=` or `SET:PH_O=`, **power-cycle** the node and send
      `STATUS` to confirm the values survived.
- [ ] If the new module has a different output scaling, re-derive both constants from
      scratch; do not assume the old values transfer.
- [ ] On `Node4_SMTP` there is no console — the constants can only be changed by editing
      the sketch defaults and re-flashing, or by NVS contents carried over. Plan for that
      before you open the enclosure.

### Turbidity module

**Recommendation.**

- [ ] There is no calibration constant to restore, so nothing is lost — but there is also
      nothing to correct. Re-run the visual cross-check in
      [Turbidity calibration](../calibration/turbidity.md#verification-procedure).
- [ ] First confirm that **clear water reads well below 3.20 V**. If clear water does not,
      the channel reports `0` NTU by saturation and the readings are meaningless.
- [ ] Clean the optical window before judging the new unit.
- [ ] If the node runs `Node4_SMTP`, note that the variant reconstructs a synthetic 5 V
      voltage and applies different thresholds — the NTU values are not interchangeable
      with `Node4`.

### EC module

**Recommendation.**

- [ ] **Re-determine the K-factor.** The stored value was measured for the old cell.
      See [Conductivity calibration](../calibration/conductivity.md#determining-the-k-factor-against-a-standard-solution).
- [ ] Verify the cell condition and fill level before adjusting anything — a fouled or
      poorly filled cell drifts in a way no constant corrects.
- [ ] Power-cycle and confirm the K-factor survived in NVS.
- [ ] Confirm the reported unit suffix: `uS` on `Node4`, `mS` on `Node4_SMTP`.
- [ ] Remember zero EC is treated as a **valid** measurement by the firmware, so `EC:0` is
      not evidence of a fault.

### Dissolved oxygen module (Node 2)

**Recommendation.**

- [ ] There is **no stored calibration to restore** — every constant is in the sketch.
- [ ] Confirm the channel is no longer reading raw zero: `DO--` on Node 1's LCD means
      `rawDO == 0`.
- [ ] If the new module has a different output scaling, the reported mg/L will be wrong
      and **only a firmware change can fix it** — see
      [Dissolved oxygen calibration](../calibration/dissolved-oxygen.md#there-is-no-runtime-calibration).
- [ ] Record the replacement in the log, including the reported DO in air-saturated water
      at a known temperature.

### Flow sensor (Node 3)

**Recommendation.**

- [ ] Confirm the input is still on GPIO 23, configured `INPUT_PULLUP`, with the ISR on
      **FALLING**. The firmware expects a hall-effect output that pulls low on each pulse.
- [ ] Check for debris in the impeller bore and that the impeller spins freely.
- [ ] Confirm `FLM:` appears in the downstream frame and is non-zero with flow running.
- [ ] **`FLM:0` is never reported as invalid** — Node 3 always sets the validity flag true.
      Verify physically rather than trusting the value.
- [ ] The K-factor is `FLOW_CAL_FACTOR 5.5f` pulses per litre and is a compile-time
      constant. If the new sensor has a different pulses-per-litre rating, a re-flash is
      required — there is no runtime adjustment.

## After any replacement

- [ ] Run the full [Startup checklist](startup-checklist.md).
- [ ] Confirm the node's contribution to the chain is healthy — a node that reports
      `node<n>:0` makes every upstream node's status word misleading.
- [ ] Record: date, node, sensor, part identity if known, readings before and after,
      whether the NVS calibration survived, and the technician.
- [ ] If the replacement could not be completed successfully, say so in the log. A
      half-fitted sensor is worse than a documented failure.

## Related pages

- [Field service index](index.md)
- [Maintenance](maintenance.md)
- [Startup checklist](startup-checklist.md)
- [Hardware: GPIO map](../hardware/gpio-map.md) · [Hardware: wiring](../hardware/wiring.md)
- [Calibration index](../calibration/index.md)
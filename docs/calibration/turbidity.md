---

title: Turbidity Calibration

description: The Node 4 SEN0189 turbidity curve, the corrected ADC reference that makes old data incomparable, and why no runtime calibration exists.

---

# Turbidity Calibration

This is the shortest calibration page in the project, because there is almost nothing to

calibrate. The turbidity channel on Node 4 applies a fixed published-style curve to the

measured voltage. There are no offset constants, no gain constants, no stored values and

no serial command.

Claim types used throughout: **Firmware implementation**, **Engineering

interpretation**, **Manufacturer specification** (where cited), **Recommendation**.

## The formula

**Firmware implementation.** On GPIO 14 with `ADC_11db` attenuation, 12-bit, evaluated

once per second in `Task_Sensors_Node4`:

| Condition | Result |

|---|---|

| `V >= 3.20` | `ntu = 0` NTU |

| `V <= 0.50` | `ntu = 3000` NTU |

| otherwise | `ntu = -1120.4 * V² + 5742.3 * V - 4353.8`, clamped to `[0, 3000]` |

`V` is the calibrated pin voltage from `readSensorVoltage()` — an average of 16

`analogReadMilliVolts()` samples — in volts. Validity: the reading is accepted whenever

`0.0 <= V <= 3.30`.

**Engineering interpretation.** The two thresholds are extrapolation guards, not

measurements. Above 3.20 V the quadratic would return a large negative number and below

0.50 V a large positive one, so the code substitutes the range endpoints instead. The

`[0, 3000]` clamp is a second layer of the same guard.

The code deliberately does **not** invalidate the reading at either end of the range. The

source comment is explicit: saturation is a valid physical condition. So a turbid sample

that saturates the sensor is reported as a confident `3000`, not as a fault.

## The ADC reference correction — read this before comparing any data

**Firmware implementation.** The source carries this engineering note in the turbidity

block:

```cpp

--8<-- "assets/snippets/node4-turbidity-processing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_Sensors_Node4</code> (turbidity block) ·

lines 511–582 · commit <code>db6d9b8</code>
</div>

The note, in the source's own words, is that the **original code used 5.0 V as the ADC

reference, that this is incorrect for the ESP32 ADC measurement, and that the voltage

used now is the actual voltage measured at the ESP32 ADC input.**

### Why this makes historical data incomparable

**Engineering interpretation.** The SEN0189/DFRobot relationship the coefficients come

from is specified in terms of a voltage on a nominally 5 V supply and a 5 V ADC

reference. If the count-to-voltage conversion is done against 5.0 V when the true pin

voltage is only 3.3 V, every computed NTU is wrong — and wrong in a way that varies with

the reading, because the quadratic is non-linear. Fixing the reference changes the whole

curve, not a scale factor.

**Consequence: turbidity data captured from an `_OLD` build is not comparable with data

from the current `FreeRTOS_Implementation` build.** Any historical record, chart or

dataset produced before this correction must be treated as belonging to a different

instrument. Do not trend across that boundary without re-baselining.

Historical / legacy — not the current firmware architecture. See

[Legacy firmware](../historical/legacy-firmware.md).

### The SMTP variant does it differently again

**Firmware implementation.** `Node4_SMTP.ino` converts the ADC count to volts against

`ESP32_VREF 3.3f`, then multiplies by `5.0f / 3.3f` to reconstruct a 5 V-equivalent

voltage (`turbVolt5V`), applies different thresholds (`>= 4.2` → 0 NTU, `< 2.5` → 3000

NTU) and then applies the same quadratic. It also uses raw `analogRead()` rather than

`analogReadMilliVolts()`.

**Engineering interpretation.** The two Node 4 variants therefore implement three

different voltage domains for the same sensor: `Node4` uses the true 3.3 V pin voltage,

`Node4_SMTP` reconstructs a synthetic 5 V-equivalent, and the legacy code used 5.0 V as

if it were real. NTU values are **not interchangeable between the variants** either.

This is a genuine divergence and is documented rather than smoothed over.

## There is no runtime calibration

**Firmware implementation.** Concretely, for the turbidity channel:

- No `Preferences` entry. `node4_cal` contains `phSlope`, `phOffset`, `ecKFactor` and

  nothing else.

- No `SET:` command for turbidity.

- No offset, gain, span or zero constant anywhere in `Node4.ino`.

- No ambient or dark reference subtraction. The sensor is read as-is.

There is nothing to adjust. If the readings are wrong, the only options are a firmware

change or a physical/electrical fix.

## Temperature is not used to compensate turbidity

**Firmware implementation.** Node 4 reads two temperature probes — the submerged

DS18B20 (GPIO 27) and the DHT11 ambient (GPIO 5). Both are used: the submerged probe

feeds the pH and EC temperature compensation, and the ambient probe is displayed and

forwarded. **Neither is referenced in the turbidity block.** The turbidity calculation is

a pure function of `turbVolt`.

**Engineering interpretation.** Optical turbidity measurements are temperature sensitive

in several ways — the LED output drifts, the photodiode dark current drifts, and the

scattering medium itself changes. The current firmware compensates for none of it. A

turbidity trend taken across a season confounds real water-quality change with sensor

temperature drift, and the two cannot be separated from the telemetry alone.

## A formazin-based calibration is not implemented

**Engineering interpretation.** The referenced curve is an empirical

voltage-to-NTU relationship published for the SEN0189 module family. It is **not** a

traceable calibration against a turbidity standard.

Specifically, the firmware has no formazin standard, no reference-blank measurement, no

multi-point fit and no calibration record. The `Turb:` value is a module-derived

estimate, not a measurement traceable to any standard. Any statement implying

formazin-based calibration has been performed would be false.

> **Not verified from the current source.** The sensor brand, exact part number and

> batch; whether the fitted module is genuinely an SEN0189/DFRobot unit or a

> functionally similar clone; the manufacturer version and date of the coefficient set;

> and any measured accuracy for the channel.

## Verification procedure

**Recommendation.** This is a cross-check, not a calibration. It establishes whether the

installed sensor behaves as the curve predicts.

1. **Establish the baseline.** Power Node 4 and send `STATUS` on the 115200-baud debug

   UART. Record the `Turb -> Raw ADC` and `Voltage` values and confirm the pH and EC

   channels are also sane — a shared ground or supply fault shows up on several

   channels at once. See

   [Troubleshooting](../field-service/troubleshooting.md).

2. **Check the DC operating point first.** With the sensor immersed in **clear,

   dechlorinated water** and the optical surface clean and dry-facing, record the voltage.

   **Engineering interpretation:** if clear water does not produce a voltage well below

   3.20 V, the channel will report `0` NTU by saturation rather than by measurement, and

   every subsequent reading is meaningless. This is the single most useful diagnostic.

3. **Compute the expected value from the recorded voltage** using the firmware's own

   piecewise rule, and compare it with the `TU:` figure on the LCD row 1. They must

   agree exactly; if they do not, the LCD is showing a stale or invalid value rather than

   the computed one.

4. **Prepare three visually distinct samples** — clear, moderately turbid (for example a

   dilute soil suspension), and highly turbid — using water from the same source so the

   temperature is comparable.

5. **For each sample:** stir or let settle to a steady state, note the water temperature,

   send `STATUS`, record the voltage, and read the `TU:` value. Compute the expected NTU

   from the recorded voltage with the firmware rule.

6. **Cross-check visually.** Hold the sample against a black surface and look through it

   as the sensor's datasheet instructs. Record your visual judgement (clear / slightly

   hazy / opaque) next to the NTU figure.

7. **Interpret:**

   - Monotonic increase across the three samples, roughly matching visual categories →

     the channel is behaving as intended. Record as verified.

   - Stuck at `0` for clear and moderate samples → check the wiring, the supply, and

     step 2. This is an electrical fault, not a calibration issue.

   - Stuck at `3000` for the clear sample → the sensor is saturated, obstructed or

     miswired. Not a calibration issue.

   - Monotonic but the ordering disagrees with the visual judgement → the sensor is out

     of its useful range for that sample. No firmware constant can help.

8. **Repeat with the optical surface inspected.** Lint, biofilm and mineral deposit change

   the reading much more than any constant would. Cleaning is the first action, not

   calibration.

9. **Record the result** in the maintenance log

   ([Maintenance](../field-service/maintenance.md)) with the raw voltages, so a future

   drift can be detected against a known starting point.

**Recommendation.** If a traceable turbidity value is needed, it must come from an

external reference measurement taken alongside the node. The node cannot provide it.

## Related pages

- [Calibration index](index.md)

- [Turbidity sensor](../sensors/turbidity.md)

- [Node 4](../nodes/node4.md) · [Node 4 SMTP](../nodes/node4-smtp.md)

- [ADC handling and validity ranges](ph.md) — how `readSensorVoltage()` behaves

- [Known limitations](../validation/known-limitations.md)
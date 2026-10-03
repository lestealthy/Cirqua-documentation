---
title: Turbidity
description: Effluent turbidity measurement on Node 4 (GPIO 14, ADC2) — the SEN0189/DFRobot piecewise NTU conversion and the corrected ADC voltage reference.
---

# Turbidity

Turbidity is measured on **Node 4 only**, in the effluent stream. The firmware
applies a piecewise conversion from measured pin voltage to nephelometric
turbidity units (NTU), following the relationship attributed in the source to
SEN0189 / DFRobot.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Node</span>
    <span class="cirqua-identity__value">4 (only)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">GPIO</span>
    <span class="cirqua-identity__value"><code>PIN_TURB_ANALOG</code> <code>14</code> (ADC2)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Interface</span>
    <span class="cirqua-identity__value">Analogue, single-ended, 16-sample averaging, measured in millivolts at the pin</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Signal type</span>
    <span class="cirqua-identity__value">Analogue voltage, 12-bit ADC with 11 dB attenuation</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Firmware reading function</span>
    <span class="cirqua-identity__value"><code>Task_Sensors_Node4</code> → <code>readSensorVoltage(PIN_TURB_ANALOG)</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Frame field</span>
    <span class="cirqua-identity__value"><code>Turb:%d</code> — integer NTU</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Status</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--historical">reference corrected vs `_OLD`</span></span>
  </div>
</div>

## Manufacturer specification

The Node 4 firmware attributes its turbidity relationship to **SEN0189 / DFRobot**
in a source comment. The following is the manufacturer specification for that part,
taken from the official DFRobot documentation and recorded with an access date in
[the source registry](../references/source-registry.md). It is stated separately
from the CIRQUA implementation below because **the two do not agree on the voltage
range**.

| Parameter | Manufacturer value |
|---|---|
| Operating voltage | 5 V DC |
| Operating current | 40 mA maximum |
| Analogue output | 0 – 4.5 V |
| Digital output | High/low level, threshold set by an on-board potentiometer |
| Response time | < 500 ms |
| Operating temperature | 5 °C to 90 °C |
| Storage temperature | −10 °C to 90 °C |
| Waterproofing | Top of probe is **not** waterproof |

Two further manufacturer statements matter for the firmware:

* the analogue output **decreases** as turbidity increases — the direction the
  CIRQUA firmware implements is therefore correct;
* in pure water, below 0.5 NTU, the manufacturer states the sensor outputs
  **4.1 ± 0.3 V** at 10–50 °C.

!!! warning "The manufacturer publishes a curve, not an equation"
    DFRobot documents the voltage-to-NTU relationship as a **reference chart that
    varies with temperature**. It does not publish the quadratic used by the
    CIRQUA firmware. The polynomial in the source must therefore be treated as an
    empirical fit and **not** quoted as a datasheet relationship.

### The voltage range does not fit

This is the most important finding in this page, and it is a conflict between two
manufacturer specifications and the firmware as written.

| | Value | Source |
|---|---|---|
| Sensor analogue output | 0 – 4.5 V | DFRobot SEN0189 |
| Sensor output for clear water (< 0.5 NTU) | 4.1 ± 0.3 V | DFRobot SEN0189 |
| ESP32 ADC measurable input at `ADC_11db` | 150 mV – **3100 mV** | Espressif ADC documentation |
| Attenuation selected by the firmware | `ADC_11db` | `Node4.ino` |
| Firmware validity window | `0.0 <= V <= 3.30` | `Node4.ino` |
| Firmware zero-turbidity branch | `V >= 3.20 → 0 NTU` | `Node4.ino` |

**Manufacturer fact.** The module drives up to 4.5 V, and outputs about 4.1 V in
clear water.

**Manufacturer fact.** With the attenuation the firmware selects, the ESP32 ADC can
only measure up to 3100 mV.

**WattLab engineering interpretation.** Three consequences follow, and they
compound:

1. The top of the sensor's output span — roughly 3.1 V to 4.5 V — lies outside the
   ESP32's measurable input range with `ADC_11db`. Those voltages cannot be read
   faithfully.
2. The clear-water reference point of 4.1 ± 0.3 V is above that ceiling. In clear
   water the signal is out of range, and the firmware's own validity window
   (`V <= 3.30`) rejects it as invalid. **The best-case water condition is the one
   condition reported as a sensor fault.**
3. The firmware's `ntu = 0.0f` branch requires `V >= 3.20`, which is above both the
   3100 mV ADC ceiling and the 3100 mV point Espressif specifies. Under the
   configured attenuation that branch is **effectively unreachable**, so the
   conversion never returns 0 NTU from the quadratic path.

!!! danger "Requires a hardware check before this channel is trusted"
    If external attenuation is fitted — a resistive divider or similar — that is
    not recorded anywhere in the firmware or in any wiring document, and it would
    change every conclusion above. Nothing in the repository shows one.
    **Confirm on the physical board** what voltage is actually present at GPIO 14
    with the probe in clear water and in turbid water. Until that is measured, the
    turbidity channel should be treated as unvalidated.

!!! note "No firmware change is proposed here"
    This page documents reality. Selecting a different attenuation, fitting a
    divider, or recalibrating the curve is a hardware and firmware decision for
    the project, not a documentation change, so none has been made.

## Purpose and measured quantity

The sensor reports the turbidity of the effluent water at Node 4. The value is:

* carried downstream as `Turb:%d` in the frame from Node 4 to the controller,
  in both variants;
* displayed on the Node 4 LCD, row 1, as `TU:%d`.

Note the format: the frame and the LCD both render turbidity as an **integer**,
so the reported resolution is 1 NTU. The internal computation is
floating-point.

## Physical principle

> **Manufacturer specification.** The firmware source comment names
> **SEN0189 / DFRobot** as the basis of the conversion polynomial. This
> documentation has not been checked against a SEN0189 datasheet, and no beam
> geometry, output range, response time, accuracy figure or measurement
> principle is asserted on this page. The fitted part number and its exact
> manufacturer are **Not verified from the current source**; the name in the
> comment is treated here as an attribution, not as a verified fit.

Generic principle: a nephelometric turbidity sensor measures the light
**scattered** at an angle by suspended particles. A light source illuminates the
sample through one window and a detector views the scattering volume through
another. As the concentration of scattering particles rises, the detected
scattered light rises. NTU is defined against a reference standard such as
formazin, so that readings are comparable between instruments only when their
optical geometry is comparable.

Turbidity is therefore an optical measurement of particle load, not of any
particular substance. Fines, precipitates and biofilm scatter as effectively as
mineral or organic solids.

## Electrical interface

| Property | Value |
|---|---|
| Pin | GPIO 14 |
| ADC bank | ADC2 |
| Attenuation | `ADC_11db`, set by `configureADC()` |
| Resolution | 12-bit |
| Pin mode | `INPUT` |
| Samples per reading | 16, plus one discarded sample after channel switching |
| Measurement method | `analogReadMilliVolts()` average, in volts |

Configuration is identical to the [pH](ph.md) and
[conductivity](conductivity.md) channels — `configureADC()` sets the same
attenuation on all three analogue pins and sets the resolution once:

```cpp
--8<-- "assets/snippets/node4-adc-configuration.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>configureADC</code> · lines 161–189 · commit <code>db6d9b8</code>
</div>

### The ADC reference correction — material if you are comparing with `_OLD`

!!! WARNING
    **The original code used 5.0 V as the ADC reference. That is incorrect for
    the ESP32 ADC measurement. The voltage used now is the actual voltage
    measured at the ESP32 ADC input.** This is stated in the firmware's own
    source comment, in the code that performs this conversion.

The current implementation obtains its voltage from `analogReadMilliVolts()`
through `readSensorVoltage()`, which returns the ESP32's own millivolt reading
at the pin. No assumed reference voltage appears in this channel.

This matters practically:

* Any voltage fed into the quadratic below is now roughly **1.52× smaller** for
  a given physical signal than it would have been under a 5.0 V assumption, since
  the ESP32's range is about 3.3 V.
* The voltage therefore moves to a **different part of the polynomial**, and
  because the polynomial is strongly nonlinear, the resulting NTU figures
  change materially — not by a constant factor.
* **A turbidity value recorded from `_OLD/` code is not comparable with a value
  from the current firmware without re-deriving it through the correct
  reference.** Do not treat historical and current NTU figures as the same
  quantity when building a time series or comparing against laboratory data.

The historical code is labelled
<span class="cirqua-badge cirqua-badge--historical">historical</span> and is
never the current architecture. See
[Legacy Firmware](../historical/legacy-firmware.md).

## How CIRQUA uses it

### The piecewise conversion

```text
if V >= 3.20          ->  ntu = 0            // very clear water
else if V <= 0.50     ->  ntu = 3000         // below useful formula range
else                  ->  ntu = -1120.4*V^2 + 5742.3*V - 4353.8
                          ntu clamped to [0, 3000]
```

The quadratic is the SEN0189 / DFRobot relationship named in the source
comment. The two thresholds exist because the polynomial is only useful over a
restricted voltage span, and because extrapolating it beyond that span produces
nonsense.

### Where the polynomial is flat or reversing

It is worth noting, as a property of the polynomial rather than of any
particular water, that the quadratic has a turning point where
`dNTU/dV = -2240.8*V + 5742.3 = 0`, at **V ≈ 2.56 V**, at which NTU is at a
maximum. Between roughly 0.5 V and 2.56 V the curve rises steeply; above about
2.56 V it falls again, which is why the `V >= 3.20` branch returns 0 rather
than following the polynomial down. Readings near the top of the useful band
are therefore highly sensitive to small voltage changes.

### Reading the source

```cpp
--8<-- "assets/snippets/node4-turbidity-processing.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
turbidity to NTU conversion and saturation handling · lines 511–582 · commit <code>db6d9b8</code>
</div>

### Validity gating — and why saturation is not invalidated

```text
valid  <=>  0.0 <= V <= 3.30
```

The source is explicit about the design intent:

> *"Don't automatically invalidate the turbidity sensor just because it is
> reading near one end of its range. Saturation is a valid physical
> condition."*

This is a deliberate choice and it is worth stating plainly, because it is
unusual. Many implementations invalidate at the range ends and report a fault;
this one reports `0 NTU` or `3000 NTU` as **valid** data.

The practical consequence for a field technician:

* A reading of exactly **0 NTU** means the input voltage was **at or above
  3.20 V**. It does **not** mean the firmware believes the water is clear — it
  could equally mean the sensor output has saturated high, the board has
  failed high, or the sensor is not properly immersed.
* A reading of exactly **3000 NTU** means the input voltage was **at or below
  0.50 V**. It could mean genuinely extremely turbid water, or a saturated or
  failed output.
* Neither end of the range carries a fault indication. A technician
  distinguishing clear water from a failed sensor must use `STATUS` on the
  serial console to read the actual pin voltage, and must reason about the
  water independently.

The only invalid conditions are a negative voltage — which should be
impossible — and a voltage above 3.30 V, which indicates a saturated or
over-range input.

## Calibration

**There is no calibration mechanism for turbidity in the firmware.** The
polynomial coefficients, the two branch thresholds and the clamp limits are all
compile-time constants. Unlike pH and conductivity, turbidity has **no entry in
the NVS calibration structure and no `SET:` command** in the serial console.

| Item | Adjustable? | Mechanism |
|---|---|---|
| Quadratic coefficients | No | Compile-time literals |
| `3.20` / `0.50` thresholds | No | Compile-time literals |
| `[0, 3000]` clamp | No | Compile-time literals |
| Any offset, span or dark-reference trim | Not implemented | — |

`STATUS` on the Node 4 console **does** print raw ADC counts and volts for
turbidity, which makes it the appropriate instrument for verifying the input
side of a reading, even though there is no way to persist a correction.

Procedure reference: [Turbidity Calibration](../calibration/turbidity.md).

## Expected values and typical ranges

Derivable **strictly from the firmware**:

* Output unit: **NTU**, reported as an **integer** (`Turb:%d`, LCD `TU:%d`).
* Range: **0 to 3000 NTU**, clamped.
* `V >= 3.20 V` → **0 NTU**.
* `V <= 0.50 V` → **3000 NTU**.
* Quadratic branch applies over **0.50 < V < 3.20 V**.
* Validity window: **0.0 to 3.30 V**.

Some illustrative evaluations of the polynomial, to make the shape concrete:

| Input voltage | NTU |
|---|---|
| 1.00 V | 268.1 |
| 1.50 V | 1688.6 |
| 2.00 V | 2493.0 |
| 2.56 V | 2996.8 (near the turning point) |

Typical effluent turbidity for the water in question, and achievable accuracy:

> **Not verified from the current source.** No field data, no datasheet and no
> verified device specification is available to this documentation set. The
> values above are arithmetic on the firmware's own constants, not
> measurements of water.

## Failure modes

What the firmware treats as invalid:

* **Voltage above 3.30 V.** Only this, plus the physically impossible negative
  case.

What a field technician should look for:

* **`Turb` reading exactly 0 with `node4` healthy.** The input was at or above
  3.20 V. Check `STATUS`: if the voltage is pegged high with clear water, the
  sensor output has saturated or the board has failed high. This is the most
  common misleading state for this channel.
* **`Turb` reading exactly 3000.** The input was at or below 0.50 V. Genuine
  severe turbidity, or a saturated low output, or a probe not properly in the
  water.
* **Stuck at one integer value.** 1 NTU granularity means small changes are
  invisible; a channel that never leaves, say, 0 or never leaves 3000 needs
  investigating with `STATUS` rather than being accepted at face value.
* **Biofouling on the optical windows.** Progressive loss of sensitivity,
  typically reading low, with no fault indication.
* **Bubbles on the sensor face.** Air in the optical path scatters light and
  reads as increased turbidity.
* **A reading that does not correlate with the rest of the water parameters.**
  A cross-check against [pH](ph.md) and
  [conductivity](conductivity.md) on the same node, in the same sample, is
  the practical sanity test available.

Field verification note: `STATUS` is the intended diagnostic and prints the raw
voltage for this pin. Use it whenever a reported NTU value needs to be trusted.

## Environmental considerations

* **Light exclusion.** Nephelometric sensors are sensitive to ambient light.
  Readings taken in direct sun, or with an inadequately enclosed sensor, can be
  significantly biased. The enclosure specification is
  **Not verified from the current source**.
* **Air bubbles.** Both on the optical windows and entrained in the sample.
* **Sediment and biofilm on the windows.** Slow, progressive and undetectable by
  the firmware.
* **Sediment settling in still water.** A sample that has stood will give a
  lower reading than one that is well mixed, purely from sampling position.
* **Sensor immersion depth and orientation.** Optical geometry matters; a probe
  partially out of the water reads high.
* **Temperature.** No temperature compensation is applied to this channel, and
  none is claimed. Some optical turbidity designs are temperature dependent,
  but no firmware correction exists and no device specification is available.
* **Particulate composition.** NTU is a light-scattering measure, not a mass
  concentration. Equal NTU can represent very different solids loading
  depending on particle size and refractive index. Do not convert NTU to
  suspended solids by any fixed factor.

## Limitations

Firmware-level limitations, stated plainly:

* **No calibration storage and no console command.** The coefficients cannot
  be adjusted, trimmed or re-derived in the field.
* **Integer reporting only.** The frame carries `Turb:%d`. Sub-NTU resolution
  is discarded in transmission, so a channel that varies by a few NTU between
  cycles will appear quantised or static.
* **Saturation is reported as valid data.** A failed-high or failed-low sensor
  is indistinguishable from extreme water conditions without checking `STATUS`.
  This is a deliberate design decision, recorded here so that it is not
  mistaken for an oversight.
* **A voltage difference of millivolts produces a large NTU difference** across
  the steep part of the polynomial. Small offsets in supply, cable routing or
  grounding between sensors can therefore show up as significant NTU shifts.
* **No temperature compensation.**
* **16-sample averaging with no outlier rejection.**
* **No cross-checking against another parameter** in the firmware; the channel
  is reported entirely on its own.
* **No trend or event detection.** A slowly fouling sensor produces a slowly
  falling series of valid values with nothing to indicate a problem.
* **Comparability with historical `_OLD` data is broken** by the ADC reference
  correction described above.
* **The polynomial is empirical and bounded.** Its accuracy is a property of the
  SEN0189 device it was fitted to, and the firmware cannot compensate for a
  different fitted sensor.

## Maintenance and replacement

Turbidity sensors of this type accumulate fouling quickly and need cleaning far
more often than they need replacing. Cleaning the optical windows and
re-checking the pin voltage with `STATUS` is the routine intervention. Because
there is no calibration storage, a replacement sensor may produce a different
baseline even when functionally identical — establish the new baseline rather
than assuming continuity with the old series.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md).
Routine checks: [Maintenance](../field-service/maintenance.md).

> **Not verified from the current source.** Fitted sensor part number, cable
> type, length, gauge and connector pinout, and enclosure optical
> characteristics. No schematic or hardware photograph exists in the
> repository.

## Where it is used

| Node | GPIO | ADC bank | Reading function | Frame field | Valid flag |
|---|---|---|---|---|---|
| 4 | 14 (`PIN_TURB_ANALOG`) | ADC2 | `Task_Sensors_Node4` | `Turb` (`%d`, integer NTU) | `node4` |

Consumers:

* Node 4's UART task, which appends `|Turb:%d` before forwarding to the
  controller, in both the standard and SMTP variants;
* the Node 4 LCD, row 1: `TU:%d`.

Full pin table: [GPIO Map](../hardware/gpio-map.md).
Node detail: [Node 4](../nodes/node4.md),
[Node 4 SMTP](../nodes/node4-smtp.md).

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),
branch `main`, commit
[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)
(short `db6d9b8`).

| Snippet | Source path | Symbol | Lines |
|---|---|---|---|
| `node4-turbidity-processing` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 511–582 |
| `node4-sensor-task` | `FreeRTOS_Implementation/Node4/Node4.ino` | `Task_Sensors_Node4` | 374–712 |
| `node4-sensor-voltage` | `FreeRTOS_Implementation/Node4/Node4.ino` | `readSensorVoltage` | 246–266 |
| `node4-adc-configuration` | `FreeRTOS_Implementation/Node4/Node4.ino` | `configureADC` | 161–189 |
| `node4-pin-definitions` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 10–41 |

Everything on this page is *firmware implementation* unless explicitly labelled
otherwise. `SEN0189 / DFRobot` is named in a source comment and is reported here
as an attribution of the polynomial, not as a verified device specification.

Related: [Sensors overview](index.md) ·
[Turbidity Calibration](../calibration/turbidity.md) ·
[Legacy Firmware](../historical/legacy-firmware.md) ·
[Sensor Replacement](../field-service/sensor-replacement.md)

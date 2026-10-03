---
title: pH
description: Effluent pH measurement on Node 4 (GPIO 13, ADC2) — the linear slope/offset model, the 25 °C-anchored compensation, validity gating and live NVS calibration.
---

# pH

pH is measured on **Node 4 only**, in the effluent stream. It is the one sensor
in the cluster whose calibration can be adjusted in the field without
reflashing: Node 4 hosts a serial console that persists a slope and an offset
to NVS.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Node</span>
    <span class="cirqua-identity__value">4 (only)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">GPIO</span>
    <span class="cirqua-identity__value"><code>PIN_PH_ANALOG</code> <code>13</code> (ADC2)</span>
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
    <span class="cirqua-identity__value"><code>Task_Sensors_Node4</code> → <code>readSensorVoltage(PIN_PH_ANALOG)</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Frame field</span>
    <span class="cirqua-identity__value"><code>pH:%.1f</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Status</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--verified">field-calibrable</span> <span class="cirqua-badge cirqua-badge--unknown">device unverified</span></span>
  </div>
</div>

## Purpose and measured quantity

The sensor reports the pH of the effluent water at Node 4. The value is:

* carried downstream as `pH:%.1f` in the frame from Node 4 to the controller,
  in both the standard and the SMTP variant;
* displayed on the Node 4 LCD, row 0, as `EV:%dL pH:%.1f`.

The value is dimensionless and is reported to one decimal place.

## Physical principle

> **Manufacturer specification.** **Not verified from the current source.** The
> firmware contains no manufacturer name or part number for the pH sensor or
  its amplifier board. No electrode type, reference type, impedance, response
  time, drift rate, wet range or accuracy figure is asserted on this page.

Generic principle: pH is a measure of hydrogen ion activity. In an aqueous
solution it relates to electrical potential through the Nernst equation, which
makes the relationship logarithmic in concentration and dependent on
temperature. A practical probe pairs a glass membrane electrode, whose
potential varies with the hydrogen ion activity in the sample, with a reference
electrode held at a fixed potential. The difference between the two, amplified
and offset to a mid-scale voltage, is what an analogue pH board presents to a
microcontroller.

!!! WARNING
    **The CIRQUA firmware does not implement the Nernst relationship.** It
    applies a straight-line model in volts. This is stated in full below and is
    the single most important thing to understand about this channel.

## Electrical interface

| Property | Value |
|---|---|
| Pin | GPIO 13 |
| ADC bank | ADC2 |
| Attenuation | `ADC_11db`, set by `configureADC()` |
| Resolution | 12-bit (`analogReadResolution(12)`) |
| Pin mode | `INPUT` |
| Samples per reading | 16 |
| Measurement method | `analogReadMilliVolts()` average, in **volts** |
| Acquisition time per cycle | 16 × (100 µs settle + 150 µs spacing), plus a discarded first sample |

```cpp
--8<-- "assets/snippets/node4-adc-configuration.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>configureADC</code> · lines 161–189 · commit <code>db6d9b8</code>
</div>

### How the voltage is obtained

```cpp
--8<-- "assets/snippets/node4-sensor-voltage.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>readSensorVoltage</code> · lines 246–266 · commit <code>db6d9b8</code>
</div>

Two details matter:

* `analogReadMilliVolts()` returns the voltage **measured at the ESP32 pin**,
  after attenuation and after the ESP32's own internal calibration. No
  assumed reference voltage is used. This is the same quantity discussed — and
  deliberately changed — on the [turbidity](turbidity.md) page.
* The first sample after a channel switch is discarded, then 16 samples are
  averaged with 150 µs spacing.

## How CIRQUA uses it

### The complete computation

```text
compensationCoefficient = 1.0 + 0.02 * (T - 25.0)

pHcalculated = phSlope * voltage + phOffset

pH = 7.0 + (pHcalculated - 7.0) / compensationCoefficient
```

where `T` is the submerged [DS18B20](temperature.md) reading, or **25.0 °C**
if that reading is invalid.

### Step by step

**Step 1 — temperature compensation coefficient.**

```cpp
float phCompensationCoefficient =
    1.0f +
    0.02f *
    (validTempForComp - 25.0f);
```

The coefficient is **1.0 at 25 °C and grows with temperature**: at 35 °C it is
1.2, at 45 °C it is 1.4.

**Step 2 — linear conversion from volts.**

```cpp
float calculatedPh =
    (calData.phSlope * phVolt) +
    calData.phOffset;
```

With the shipped defaults, `3.5 × V − 1.75`. At the ADC mid-point of about
1.65 V this yields 4.03, which is why the default offset is not zero.

**Step 3 — compensation about pH 7.**

```cpp
float finalPh =
    7.0f +
    ((calculatedPh - 7.0f) /
     phCompensationCoefficient);
```

The compensation is applied to the *deviation from neutrality*, not to the
absolute value. Dividing by a coefficient greater than 1 pulls the result
**towards 7** as temperature rises.

### Reading the source

```cpp
--8<-- "assets/snippets/node4-ph-processing.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
pH computation, compensation and gating · lines 458–509 · commit <code>db6d9b8</code>
</div>

### Validity gating

```text
valid  <=>  0.02 <= V <= 3.30
       AND  0.0  <= pH <= 14.0
```

Both conditions must hold. The source comment states the intent: a completely
saturated or disconnected ADC signal should not be reported as a valid pH
measurement. The lower bound of 0.02 V rejects a dead-low input; the upper bound
of 3.30 V rejects a saturated input.

### This is a linear model, not an electrochemical one

Stated directly, because it matters for interpreting the data:

* The firmware maps voltage to pH with a **straight line**, `slope × V +
  offset`. A pH probe amplifier with a Nernst-law output is **logarithmic** in
  hydrogen ion activity: equal voltage steps correspond to equal *logarithmic*
  pH steps, and a linear transfer function is a reasonable approximation to
  that over a limited span.
* There is no Nernst slope of approximately 59 mV per pH unit anywhere in the
  code, no electrode offset-potential term, no reference-electrode term, and no
  logarithm.
* **This is a legacy engineering choice**, and the source says so: the comment
  reads *"Existing calibration model preserved"*. It was carried forward from
  the predecessor firmware rather than re-derived.
* The consequence is that the mapping is calibrated, not fundamental. It is
  accurate over the span that the two-point calibration actually covered, and
  degrades outside it. Two-point calibration cannot characterise a logarithmic
  transfer function outside its calibrated points.

### The compensation moves the reading with temperature

This is a known limitation and is documented rather than hidden:

* The denominator `1 + 0.02 × (T − 25)` **increases with temperature**.
* Dividing the deviation from 7 by an increasing denominator **compresses** the
  reading towards 7 as the water warms.
* At 25 °C the compensation is unity and the reading is unaffected.
* The effect is therefore: **pH readings drift towards 7.0 as water
  temperature rises**, and the drift is reversible if temperature falls.

Whether this matches the probe's real temperature dependence is
**Not verified from the current source** — the 0.02 coefficient's provenance is
not documented in the firmware. The compression also means the compensation
cannot correct for a temperature-dependent *offset*, only scale the deviation
from neutrality.

## Calibration

### Stored constants and defaults

```cpp
struct CalibrationData {
    float phSlope;
    float phOffset;
    float ecKFactor;
};
```

```cpp
--8<-- "assets/snippets/node4-calibration-struct.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
calibration storage · lines 53–66 · commit <code>db6d9b8</code>
</div>

```cpp
--8<-- "assets/snippets/node4-load-calibration.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>loadCalibration</code> · lines 132–156 · commit <code>db6d9b8</code>
</div>

| Constant | Default (`Node4`) | Default (`Node4_SMTP`) | Storage |
|---|---|---|---|
| `phSlope` | `3.5f` | `3.5f` | NVS namespace `node4_cal`, key `phSlope` |
| `phOffset` | `-1.75f` | `0.0f` | NVS namespace `node4_cal`, key `phOffset` |

!!! WARNING
    **The two Node 4 variants ship with different pH defaults.** The standard
    `Node4` uses `phOffset = -1.75f`; `Node4_SMTP` uses `phOffset = 0.0f`. With
    a slope of 3.5 and an offset of 0, a raw voltage must be near zero to read
    pH 0 — so the SMTP default will produce readings well outside the expected
    range unless the console is used to set an offset. Do not assume the two
    variants read the same water the same way out of the box.

### Live calibration over the PC serial console

Node 4's calibration console runs on the **115200 baud debug serial port** and
is handled from the UART task. Commands are case-insensitive and
newline-terminated.

```cpp
--8<-- "assets/snippets/node4-calibration-console.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>handleSerialCalibrationCommands</code> · lines 717–931 · commit <code>db6d9b8</code>
</div>

| Command | Effect |
|---|---|
| `HELP` | Lists the available commands |
| `STATUS` | Prints raw ADC counts and volts for pH, EC and turbidity, plus the saved constants |
| `SET:PH_S=<val>` | Persists `phSlope` to NVS |
| `SET:PH_O=<val>` | Persists `phOffset` to NVS |
| `SET:EC_K=<val>` | Persists `ecKFactor` — rejects values ≤ 0 |
| `RESET` | Clears the `node4_cal` namespace and reloads defaults |

`STATUS` is the correct starting point for a calibration session: it shows the
actual voltage at the pin, which is what both calibration constants operate on.

Procedure reference: [pH Calibration](../calibration/ph.md).
Console reference: [Calibration Console](../firmware/configuration.md).

## Expected values and typical ranges

Derivable **strictly from the firmware**:

* Output is a dimensionless pH value, formatted to **one decimal place**.
* Accepted range: **0.0 to 14.0**.
* Accepted input voltage: **0.02 to 3.30 V**.
* Default conversion: `3.5 × V − 1.75`.
* Compensation is unity at **25 °C**; the coefficient is **1.2 at 35 °C** and
  **1.4 at 45 °C**.
* With the default slope and offset, `pH = 7.0` corresponds to an input of
  `(7.0 + 1.75) / 3.5` = **2.50 V**.

Typical effluent pH, expected neutral point for the water in question, and
achievable accuracy:

> **Not verified from the current source.** No field data, no datasheet and no
> device specification is available to this documentation set.

## Failure modes

What the firmware treats as invalid:

* Input voltage **below 0.02 V** — a dead-low or shorted input.
* Input voltage **above 3.30 V** — a saturated or over-range input.
* Computed pH **outside 0.0 to 14.0** — the linear model has produced a value
  outside the physical scale, which indicates a bad calibration as much as a
  bad sensor.

What a field technician should look for:

* **Invalid flag with `pH` reading stale or absent.** This is the genuine
  detected case. Check `STATUS` for the actual pin voltage: near 0 V or near
  full scale explains it.
* **A plausible but wrong constant.** The most common real-world failure. The
  linear model will happily report any voltage between 0.02 V and 3.30 V as a
  valid pH, so a disconnected board presenting a mid-scale voltage produces a
  perfectly plausible pH of about 7.
* **A reading pinned near 7.0 in changing water.** This is the signature of the
  temperature compensation compressing everything towards neutrality, or of the
  probe sitting in still buffer, or of the electrode having failed towards
  mid-scale.
* **Drift.** Electrodes drift; the firmware has no drift detection and no
  re-zero mechanism. Long-term drift will be reported as a valid but wrong
  value.
* **Compensation silently inactive.** If the submerged
  [DS18B20](temperature.md) fails, the coefficient is computed from the
  25 °C default and the pH reading is still reported as valid.

Field verification note: `STATUS` on the serial console is the intended
diagnostic for this channel, and is the only place in the cluster where the raw
voltage behind a reported value is printed.

## Environmental considerations

* **Electrode hydration and storage.** A glass pH electrode must remain
  hydrated. Drying out is a common cause of drift and eventual permanent
  failure, and it is invisible to the firmware.
* **Reference electrode drift and fouling.** Contamination of the reference
  junction shifts the potential. This manifests as a slow offset error.
* **Junction potentials and ionic strength.** Readings in very low
  conductivity water carry larger errors than readings in ordinary tap or
  wastewater. Effluent from a constructed wetland may be in the low
  conductivity regime, where a pH probe's accuracy typically degrades. The
  magnitude is **not quantified here**.
* **Temperature.** Handled by the linear coefficient, with the caveats
  documented above.
* **Bubble or membrane blockage on the probe face.** Trapped air slows response
  and can bias the reading.
* **Electrical interference.** The electrode output is high impedance. A long
  unscreened run from the probe to the amplifier board, or a high-impedance
  node run at low conductivity, both increase noise pickup. Cable type and
  length are **Not verified from the current source**, and no schematic exists.

## Limitations

Firmware-level limitations, stated plainly:

* **Not a Nernst model.** A linear transfer function approximates a logarithmic
  one; it is exact only across the span the two-point calibration covered.
  This is a deliberate legacy choice, retained by the source's own admission.
* **The compensation biases readings towards 7.0 as temperature rises.** The
  denominator grows with temperature; readings compress towards neutrality. The
  `0.02` coefficient's provenance is undocumented.
* **Two-point calibration only.** Two constants (slope, offset) cannot
  characterise a nonlinear transfer function, and there is no third-point
  verification.
* **The temperature compensation failure is silent.** A failed submerged probe
  substitutes 25 °C and the pH channel continues to report valid.
* **A disconnected sensor is usually reported as valid.** The voltage window
  `0.02 – 3.30 V` is wide enough that a mid-scale failure passes the gate.
* **The two Node 4 variants ship different defaults** (`-1.75f` versus `0.0f`
  for the offset).
* **The ADC voltage is measured at the pin**, which includes the ESP32's own
  ADC calibration error and any resistive divider or cable resistance in the
  path. No correction is applied for a divider ratio, because the calibration
  absorbs it — but that means the stored constants are specific to the wiring
  in which they were set.
* **16-sample averaging with no outlier rejection.** A single glitch is
  averaged in rather than discarded.
* **No hysteresis or filtering across cycles.** Consecutive values are
  independent samples.
* **pH is reported to one decimal place**, which is coarser than a well-
  calibrated laboratory measurement could justify.

## Maintenance and replacement

Because calibration is runtime-adjustable and persisted in NVS, pH is the
cheapest sensor in the cluster to re-calibrate after service: fit the new
electrode, then use `SET:PH_S=` and `SET:PH_O=` against known buffers. No
reflash is required. Note that `RESET` clears the NVS namespace, so a full
reset returns the node to whichever defaults its variant ships with.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md) and
[pH Calibration](../calibration/ph.md).
Routine checks: [Maintenance](../field-service/maintenance.md).

> **Not verified from the current source.** Sensor and amplifier board part
> numbers, electrode type, cable type, length, gauge and connector pinout. No
> schematic exists in the repository.

## Where it is used

| Node | GPIO | ADC bank | Reading function | Frame field | Valid flag |
|---|---|---|---|---|---|
| 4 | 13 (`PIN_PH_ANALOG`) | ADC2 | `Task_Sensors_Node4` | `pH` (`%.1f`) | `node4` |

Dependent inputs and consumers:

* **Input from** the submerged [DS18B20](temperature.md) on GPIO 27, for
  temperature compensation, with a 25 °C fallback.
* **Output to** the Node 4 LCD, row 0: `EV:%dL pH:%.1f`.
* **Output to** the downstream controller as `|pH:%.1f`.

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
| `node4-ph-processing` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 458–509 |
| `node4-sensor-task` | `FreeRTOS_Implementation/Node4/Node4.ino` | `Task_Sensors_Node4` | 374–712 |
| `node4-sensor-voltage` | `FreeRTOS_Implementation/Node4/Node4.ino` | `readSensorVoltage` | 246–266 |
| `node4-adc-configuration` | `FreeRTOS_Implementation/Node4/Node4.ino` | `configureADC` | 161–189 |
| `node4-calibration-struct` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 53–66 |
| `node4-load-calibration` | `FreeRTOS_Implementation/Node4/Node4.ino` | `loadCalibration` | 132–156 |
| `node4-calibration-console` | `FreeRTOS_Implementation/Node4/Node4.ino` | `handleSerialCalibrationCommands` | 717–931 |
| `node4-pin-definitions` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 10–41 |

Everything on this page is *firmware implementation* unless explicitly labelled
otherwise. No manufacturer specification for the pH sensor or its amplifier is
available, and none is asserted. The characterisation of the ESP32 ADC voltage
range and the Nernst relationship are general engineering facts stated as
*engineering interpretation*, not as verified CIRQUA specifications.

Related: [Sensors overview](index.md) · [pH Calibration](../calibration/ph.md) ·
[Conductivity](conductivity.md) · [Water Temperature](temperature.md) ·
[Calibration Console](../firmware/configuration.md)

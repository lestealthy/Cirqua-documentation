---
title: Conductivity
description: Effluent electrical conductivity on Node 4 (GPIO 12) — K-factor conversion, temperature compensation, µS/cm reporting and the mS/cm SMTP divergence.
---

# Conductivity

Electrical conductivity (EC) is measured on **Node 4 only**, in the effluent
stream. It is one of the two channels with runtime-adjustable calibration: the
K-factor is stored in NVS and set from the serial console.

This page also documents a **significant divergence between the two Node 4
variants**: the standard `Node4` reports µS/cm, while `Node4_SMTP` reports
mS/cm. Data from the two must not be compared directly.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Node</span>
    <span class="cirqua-identity__value">4 (only)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">GPIO</span>
    <span class="cirqua-identity__value"><code>PIN_EC_ANALOG</code> <code>12</code> (ADC2)</span>
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
    <span class="cirqua-identity__value"><code>Task_Sensors_Node4</code> → <code>readSensorVoltage(PIN_EC_ANALOG)</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Frame field</span>
    <span class="cirqua-identity__value"><code>EC:%.0f</code> µS/cm · <span class="cirqua-badge cirqua-badge--variant">variant</span> SMTP reports <code>EC:%.1f</code> mS/cm</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Status</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--verified">field-calibrable</span> <span class="cirqua-badge cirqua-badge--unknown">device unverified</span></span>
  </div>
</div>

## Purpose and measured quantity

The sensor reports the electrical conductivity of the effluent water at Node 4.
Conductivity is the ability of the water to conduct electricity, which rises
with the concentration of dissolved ions. It is a general indicator of dissolved
solids, not a measurement of any particular substance.

Consumers of the value:

| Variant | Frame field | Format | Unit | LCD row 1 |
|---|---|---|---|---|
| `Node4` | `EC` | `%.0f` | **µS/cm** | `EC:%duS` |
| `Node4_SMTP` | `EC` | `%.1f` | **mS/cm** | `EC:%.1fmS` |

## Physical principle

> **Manufacturer specification.** **Not verified from the current source.** The
> firmware contains no manufacturer name or part number for the conductivity
> sensor or its amplifier board. No cell constant, cell type, range, accuracy,
> response time or wetted material is asserted on this page.

Generic principle, independent of the fitted device: a conductivity probe
immerses two or more electrodes in the water and applies an AC excitation
between them. The AC is used because a DC excitation polarises the electrodes
and produces an electrolytic drift. The measured AC current, or the AC
equivalent resistance, is proportional to the conductivity of the solution and
to the geometry of the cell. An amplifier board scales that to an analogue
voltage proportional to EC, and the microcontroller applies a K-factor to convert
the voltage into an EC value.

The K-factor absorbs the cell constant, the amplifier gain and any resistive
divider in the signal path. It is specific to the hardware it was determined on.

### Why conductivity is temperature dependent

Conductivity rises with temperature — typically by around 2 % per °C near room
temperature. The firmware's compensation coefficient of `0.0185` per °C is
consistent with that order of magnitude. That figure is a compile-time literal
whose provenance is not documented in the source.

## Electrical interface

| Property | Value |
|---|---|
| Pin | GPIO 12 |
| ADC bank | ADC2 |
| Attenuation | `ADC_11db`, set by `configureADC()` |
| Resolution | 12-bit |
| Pin mode | `INPUT` |
| Samples per reading | 16, plus one discarded sample after channel switching |
| Measurement method | `analogReadMilliVolts()` average, in volts |

Configuration is shared with the [pH](ph.md) and
[turbidity](turbidity.md) channels:

```cpp
--8<-- "assets/snippets/node4-adc-configuration.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>configureADC</code> · lines 161–189 · commit <code>db6d9b8</code>
</div>

As with [turbidity](turbidity.md), the voltage used is the **actual voltage
measured at the ESP32 pin**, obtained from `analogReadMilliVolts()`. No assumed
reference voltage is used on this channel.

## How CIRQUA uses it

### The computation

```text
ecCoefficient = 1.0 + 0.0185 * (T - 25.0)

rawEcMilliSiemens = voltage * ecKFactor

ec_uS_cm = (rawEcMilliSiemens / ecCoefficient) * 1000

ec_uS_cm = max(ec_uS_cm, 0)
```

where `T` is the submerged [DS18B20](temperature.md) reading, or **25.0 °C**
if that reading is invalid.

### Step by step

**Step 1 — the temperature coefficient.**

```cpp
float ecCoefficient =
    1.0f +
    0.0185f *
    (validTempForComp - 25.0f);
```

Unity at 25 °C. At 15 °C it is 0.815; at 35 °C it is 1.185. Because the EC is
**divided** by this coefficient, the reported value is normalised to 25 °C:
cooling increases the reading, warming decreases it.

**Step 2 — volts to millisiemens per centimetre.**

```cpp
float rawEcMilliSiemens =
    ecVolt * calData.ecKFactor;
```

With the shipped default `ecKFactor = 9.997f`, this is very nearly
`voltage x 10`. A 1 V input gives 10 mS/cm before compensation.

**Step 3 — compensate and convert to µS/cm.**

```cpp
float compensatedEc =
    (rawEcMilliSiemens /
     ecCoefficient) *
    1000.0f;
```

The `x 1000` converts mS/cm to µS/cm. The source comment records the origin of
this model:

```text
Original:
   EC(mS/cm) = voltage * K
Then temperature compensation and conversion to uS/cm.
```

### Reading the source

```cpp
--8<-- "assets/snippets/node4-ec-processing.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
conductivity K-factor conversion and temperature compensation · lines 584–635 · commit <code>db6d9b8</code>
</div>

### Validity gating — zero is accepted deliberately

```text
valid  <=>  0.0 <= V <= 3.30
```

The source states the intent:

> *"Reject impossible ADC conditions but do not reject a zero EC value —
> zero/very-low conductivity is a legitimate measurement."*

This is the correct engineering choice for this sensor, and it is worth
contrasting it with the [turbidity](turbidity.md) channel: there, saturation
is accepted as a physical condition; here, zero is accepted as a physical
condition. In both cases the firmware declines to flag a legitimate reading as
invalid.

The practical consequence for a field technician:

* A reading of **exactly 0 µS/cm** means the input voltage was at or near
  **0 V**. For a genuine low-conductivity effluent this is a real measurement.
  It is also what a disconnected sensor will very often present. The firmware
  cannot distinguish the two — use `STATUS` on the serial console and reason
  about the water.

### The SMTP variant divergence

`Node4_SMTP` omits both the temperature compensation and the `x 1000`
conversion. It therefore reports:

```text
EC_mS_cm = voltage * ecKFactor
```

with a default `ecKFactor` of **`2.0f`** rather than `9.997f`.

| Aspect | `Node4` | `Node4_SMTP` |
|---|---|---|
| Temperature compensation | Yes (`1 + 0.0185*(T-25)`) | **No** |
| `x 1000` conversion | Yes | **No** |
| Reported unit | **µS/cm** | **mS/cm** |
| Frame format | `EC:%.0f` | `EC:%.1f` |
| LCD | `EC:%duS` | `EC:%.1fmS` |
| Default `ecKFactor` | `9.997f` | `2.0f` |

!!! WARNING
    **Do not compare an `EC` figure from `Node4` with one from `Node4_SMTP`
    without first establishing which unit is in play.** They differ by a factor
    of 1000 in scale, they use different default K-factors, and the SMTP figure
    is not temperature-normalised while the standard one is. The two field
    names are identical in the frame; only the downstream field set differs, so
    a consumer of the frame cannot tell them apart from the field name alone.

### µS/cm versus mS/cm

For clarity, since the units carry the divergence:

| Unit | Relationship | Typical use |
|---|---|---|
| µS/cm (microsiemens per centimetre) | 1 mS/cm = 1000 µS/cm | Fresh water, drinking water, low-conductivity effluent |
| mS/cm (millisiemens per centimetre) | — | Sea water, brines, concentrated solutions |

Constructed wetland effluent is likely to fall in the µS/cm regime, which is
presumably why the standard `Node4` reports in µS/cm and formats it with `%.0f`
to whole units.

### A note on TDS

Conductivity is sometimes used to estimate total dissolved solids (TDS) through
a conversion factor of the form `TDS (mg/L) = EC (µS/cm) x K`, where K is
typically between 0.5 and 0.7.

**CIRQUA does not compute or transmit TDS.** There is no TDS code path, no TDS
field and no conversion factor anywhere in the audited firmware. The
`ecKFactor` stored in NVS is a **voltage-to-conductivity** factor, not a
TDS conversion factor, and the `SET:EC_K=` command adjusts the former. Do not
interpret `ecKFactor` as a TDS factor, and do not present any TDS figure as a
CIRQUA output.

## Calibration

### Stored constant and defaults

The EC K-factor is the third member of the Node 4 calibration structure:

```cpp
struct CalibrationData {
    float phSlope;
    float phOffset;
    float ecKFactor;
};
```

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
| `ecKFactor` | `9.997f` | `2.0f` | NVS namespace `node4_cal`, key `ecKFactor` |

### Setting the K-factor

From the Node 4 calibration console on the **115200 baud debug serial port**,
handled in the UART task, case-insensitive and newline-terminated:

| Command | Effect |
|---|---|
| `STATUS` | Prints raw ADC counts and volts for pH, EC and turbidity, plus the saved constants |
| `SET:EC_K=<val>` | Persists `ecKFactor` to NVS. **Rejects values ≤ 0** |
| `HELP` | Lists commands |
| `RESET` | Clears the `node4_cal` namespace and reloads defaults |
| `SET:PH_S=<val>` / `SET:PH_O=<val>` | pH calibration — see [pH](ph.md) |

The rejection of non-positive values is the only input validation on this
channel, and it prevents a K-factor that would invert or zero the reported
conductivity.

```cpp
--8<-- "assets/snippets/node4-calibration-console.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>handleSerialCalibrationCommands</code> · lines 717–931 · commit <code>db6d9b8</code>
</div>

Procedure reference: [Conductivity Calibration](../calibration/conductivity.md).
Console reference: [Calibration Console](../firmware/configuration.md).

## Expected values and typical ranges

Derivable **strictly from the firmware**:

* Standard `Node4` unit: **µS/cm**, clamped at **0**.
* `Node4_SMTP` unit: **mS/cm**, clamped at **0**.
* Temperature normalisation reference: **25 °C**.
* Temperature coefficient: **0.0185 per °C**.
* Default K-factor (`Node4`): **9.997**; (`Node4_SMTP`): **2.0**.
* Voltage accepted: **0.0 to 3.30 V**.
* With the default K of 9.997 at 25 °C, an input of 1.000 V gives
  `1.000 x 9.997 x 1000` = **9997 µS/cm**.
* `ecCoefficient` reaches zero at approximately **75.7 °C**
  (`1 + 0.0185*(T-25) = 0`), at which point the expression divides by zero.
  The firmware performs no guard against this; see Limitations.

Typical effluent conductivity, and achievable accuracy for the fitted device:

> **Not verified from the current source.** No field data, no datasheet and no
> device specification is available to this documentation set.

## Failure modes

What the firmware treats as invalid:

* **Input voltage above 3.30 V.** This is the only invalid condition, plus the
  physically impossible negative case.

What a field technician should look for:

* **`EC` reading exactly 0 with `node4` healthy.** The input was at or near
  0 V. This is *either* genuinely very low conductivity *or* a disconnected or
  failed sensor — the two are indistinguishable from the frame. Use `STATUS`
  and reason about the water.
* **A reading that tracks temperature only.** When the submerged
  [DS18B20](temperature.md) fails, the coefficient reverts to the 25 °C
  default and the EC reading continues to be reported as valid. A reading that
  moves with the ambient thermal cycle but not with the water is a sign of this.
* **An implausibly high reading.** A K-factor left at a default for a different
  sensor, or an amplifier board with a much higher gain than the one the
  K-factor was set for, produces readings high by the ratio of the gains. There
  is no upper-bound plausibility check on the computed EC.
* **Drifting with immersion time.** Electrode polarisation or incomplete
  immersion of the cell produces a reading that changes with how long the probe
  has been in the water.
- **A stable zero.** A genuinely low-conductivity effluent is a real and
  interesting measurement, particularly for a reuse system. Do not assume a
  zero reading is a fault.

Field verification note: `STATUS` prints the actual pin voltage for this
channel and is the correct first diagnostic.

## Environmental considerations

* **Temperature.** Conductivity of water changes substantially with temperature;
  the compensation is a linear approximation anchored at 25 °C.
* **Immersion depth.** Conductivity cells must be fully immersed to the
  specified depth for the measured volume to be the cell volume. Shallow
  immersion reads low.
* **Flow and stirring.** Some cell designs require flow past the electrodes to
  avoid polarisation. Whether the fitted device does is
  **Not verified from the current source**.
* **Air bubbles.** Trapped bubbles on the electrodes reduce the wetted area and
  read low.
* **Suspended solids and fouling.** Deposits on the electrodes insulate them
  and reduce the effective area, causing a progressive under-read. Biofouling
  in an effluent line is a realistic concern.
* **Electrode scaling from hard water.** Calcium carbonate scale is a common
  long-term problem for conductivity probes in hard water.
* **Very low ionic strength.** In near-deionised water, conductivity cells are
  prone to noise and drift, and their accuracy degrades. If effluent
  conductivity is genuinely near zero, treat the reading as a limit case.
* **EMI.** A high-impedance electrode signal can pick up electrical noise. Cable
  type and length are **Not verified from the current source**, and no
  schematic exists.

## Limitations

Firmware-level limitations, stated plainly:

* **The two variants report different units under the same field name.** A
  1000× scale difference plus different default K-factors plus the presence or
  absence of temperature normalisation. This is the single largest source of
  potential error when comparing data across Node 4 variants.
* **No TDS is computed**, and no EC-to-TDS conversion factor exists in the
  firmware. Do not derive TDS from these values using an assumed factor and
  present the result as a CIRQUA measurement.
* **No upper-bound plausibility check** on the computed value, only on the input
  voltage.
* **A zero reading is accepted as valid**, by deliberate design, which means a
  disconnected sensor is indistinguishable from genuinely low-conductivity
  water without `STATUS`.
* **No guard against a zero compensation denominator.** `1 + 0.0185*(T-25)`
  reaches zero at about 75.7 °C. The firmware has no validity range on the
  temperature used for compensation and does not check the coefficient before
  dividing. At temperatures approaching that point the reported EC would
  diverge. This is a real firmware-level limitation, though it is unlikely to
  be reached in this application.
* **The temperature compensation failure is silent.** A failed submerged
  DS18B20 substitutes 25 °C and the EC channel still reports valid.
* **Linear temperature compensation** applied to a relationship that is itself
  approximately but not exactly linear over wide ranges. The coefficient's
  provenance is undocumented.
* **The K-factor absorbs the entire signal chain**, including any resistive
  divider, cable resistance and amplifier gain. It is therefore specific to the
  wiring and board in which it was set: replacing the amplifier board without
  resetting the K-factor leaves a systematic error.
* **16-sample averaging with no outlier rejection.**
* **No cross-check against [pH](ph.md) or
  [turbidity](turbidity.md)**, although all three measure the same water.
* **No trend, drift detection or cleaning reminder.**

## Maintenance and replacement

EC is runtime-adjustable through the serial console, so replacing the sensor
requires a K-factor re-determination rather than a reflash. Because the K-factor
absorbs board-level differences, replacing the sensor alone and replacing the
sensor *and* its amplifier board require different responses. Establish the new
baseline with `STATUS` and a reference solution, then set `SET:EC_K=`.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md) and
[Conductivity Calibration](../calibration/conductivity.md).
Routine checks: [Maintenance](../field-service/maintenance.md).

> **Not verified from the current source.** Sensor and amplifier board part
  numbers, cell constant, cell type, cable type, length, gauge and connector
  pinout. No schematic exists in the repository.

## Where it is used

| Node | GPIO | ADC bank | Reading function | Frame field | Unit | Valid flag |
|---|---|---|---|---|---|---|
| 4 | 12 (`PIN_EC_ANALOG`) | ADC2 | `Task_Sensors_Node4` | `EC` (`%.0f`) | µS/cm | `node4` |
| 4 SMTP | 12 (`PIN_EC_ANALOG`) | ADC2 | `Task_Sensors_Node4` | `EC` (`%.1f`) | mS/cm | `node4` |

Dependent input:

* **Submerged [DS18B20](temperature.md)** on GPIO 27 supplies the compensation
  temperature, with a **25.0 °C** fallback. The SMTP variant does not use it for
  this channel.

Consumers:

* the Node 4 LCD, row 1: `EC:%duS` or `EC:%.1fmS`;
* the downstream controller, via the `EC` field.

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
| `node4-ec-processing` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 584–635 |
| `node4-sensor-task` | `FreeRTOS_Implementation/Node4/Node4.ino` | `Task_Sensors_Node4` | 374–712 |
| `node4-sensor-voltage` | `FreeRTOS_Implementation/Node4/Node4.ino` | `readSensorVoltage` | 246–266 |
| `node4-adc-configuration` | `FreeRTOS_Implementation/Node4/Node4.ino` | `configureADC` | 161–189 |
| `node4-calibration-struct` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 53–66 |
| `node4-load-calibration` | `FreeRTOS_Implementation/Node4/Node4.ino` | `loadCalibration` | 132–156 |
| `node4-calibration-console` | `FreeRTOS_Implementation/Node4/Node4.ino` | `handleSerialCalibrationCommands` | 717–931 |
| `node4-pin-definitions` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 10–41 |

Everything on this page is *firmware implementation* unless explicitly labelled
otherwise. No manufacturer specification for the conductivity sensor or its
amplifier is available, and none is asserted. The general observation about the
temperature dependence of conductivity is stated as generic engineering
context, not as a verified device specification.

Related: [Sensors overview](index.md) ·
[Conductivity Calibration](../calibration/conductivity.md) ·
[pH](ph.md) · [Turbidity](turbidity.md) ·
[Calibration Console](../firmware/configuration.md)

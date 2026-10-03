---

title: Dissolved Oxygen

description: Analogue dissolved oxygen measurement on Node 2 (GPIO 34, ADC1) — the 2-point linear conversion, temperature compensation factor and validity gating.

---

# Dissolved Oxygen

Dissolved oxygen (DO) is measured on **Node 2 only**. It is an analogue sensor

read from an ESP32 ADC channel and converted to a concentration in mg/L by a

two-point linear model with a linear temperature compensation factor.

<div class="cirqua-identity">

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Node</span>

    <span class="cirqua-identity__value">2 (only)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">GPIO</span>

    <span class="cirqua-identity__value"><code>PIN_DO_ANALOG</code> <code>34</code> (ADC1)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Interface</span>

    <span class="cirqua-identity__value">Analogue, single-ended, single conversion per cycle</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Signal type</span>

    <span class="cirqua-identity__value">Analogue voltage, 12-bit ADC reading</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware reading function</span>

    <span class="cirqua-identity__value"><code>Task_Sensors_Node2</code> → <code>analogRead(PIN_DO_ANALOG)</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Output unit</span>

    <span class="cirqua-identity__value">mg/L (LCD renders <code>mg/l</code>)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Status</span>

    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--unknown">device unverified</span></span>

  </div>

</div>

## Purpose and measured quantity

The sensor reports the dissolved oxygen concentration of the water in Feeding

Tank B. The value is:

* carried upstream as the `DO` field of the Node 2 frame,

* displayed on the Node 1 LCD as row 2, `DO{value}mg/l`.

The firmware applies no unit conversion: the reported number is mg/L.

## Physical principle

> **Manufacturer specification.** **Not verified from the current source.** The

> firmware contains no manufacturer name or part number for this sensor. No

> output range, current consumption, membrane lifetime, response time or

> accuracy figure is asserted anywhere on this page.

Generic principle, independent of the fitted device: an optical or

electrochemical dissolved oxygen probe produces a current, or a voltage

proportional to current, that varies with the partial pressure of oxygen

dissolved in the sample. A common form is a polarographic or galvanic cell in

which oxygen is reduced at a cathode; the resulting current is limited by the

rate at which oxygen diffuses through a membrane, and therefore tracks the

oxygen concentration. Such probes also have a temperature-dependent response

and a consume-rate dependent zero, which is why commercial interfaces

typically offer calibration and temperature compensation.

CIRQUA's firmware assumes the analogue output is a **monotonic, linear

function of concentration**. Whether the fitted device is linear over its

working range is not established by anything available to this documentation

set.

## Electrical interface

A single-ended analogue input on **ADC1 channel GPIO 34**. GPIO 34 is an

input-only pin — it has no output driver and no internal pull-up — which is a

common and appropriate choice for an analogue sensor input.

Node 2 configures:

```cpp

analogReadResolution(12);

```

| Property | Value |

|---|---|

| Pin | GPIO 34 |

| ADC bank | ADC1 |

| Resolution | 12-bit (0–4095) |

| Samples per cycle | 1 |

| Filtering | none |

| Direction | input only (GPIO 34 has no output driver) |

Node 2's DO path is markedly simpler than Node 4's analogue paths. There is no

averaging, no discarded first sample, no `analogReadMilliVolts()` call and no

`analogSetPinAttenuation()` call — a single raw `analogRead()` is converted

arithmetically using compile-time constants.

### The voltage reference question — read this

The conversion uses a **5000 mV full-scale reference** over a **0–4095** 12-bit

range:

```cpp

float doVoltage = ((float)rawDO / ADC_RESOLUTION) * VREF;  // Voltage in mV

```

where `VREF = 5000.0f`.

> **Engineering interpretation, flagged as a risk — not a verified

> specification.** The ESP32 ADC input range is approximately 0–3.3 V, not

> 0–5 V. The firmware therefore scales its ADC counts as though the full range

> were 5 V, which maps the 3.3 V ceiling to roughly 2700 counts and leaves

> counts 2701–4095 unreachable by any signal the pin can physically see. A

> sensor board powered from 5 V whose analogue output is referenced to that 5 V

> rail could present an output above the ESP32 ADC input range, which would not

> be measured correctly and, depending on the front end, could damage the pin.

>

> The facts above — the 0–3.3 V ADC input range and the pin's lack of

> protection — are properties of the ESP32 silicon, not of the fitted sensor,

> and are not derived from the CIRQUA source. **The actual DO sensor board,

> its supply and its output range are Not verified from the current source.**

> Confirm the fitted board's output range against its datasheet before assuming

> any DO reading is correct.

Note also that Node 2 does **not** call `analogSetPinAttenuation()` for GPIO 34,

unlike Node 4 which explicitly sets 11 dB attenuation on each of its analogue

pins. The attenuation actually in effect on Node 2's ADC channel is therefore

not established by the audited source.

## How CIRQUA uses it

### Constants

```cpp

const float VREF = 5000.0f;               // ADC Reference Voltage (mV) on 3.3V ESP32

const float ADC_RESOLUTION = 4095.0f;     // 12-bit ADC

const float TWO_POINT_VOLTAGE = 1000.0f;  // Calibration voltage threshold (mV)

const float SATURATION_DO_25C = 8.26f;    // Saturation DO concentration mg/L at 25°C

```

| Constant | Value | Role |

|---|---|---|

| `VREF` | 5000.0 mV | Full-scale reference used to convert counts to millivolts |

| `ADC_RESOLUTION` | 4095.0 | 12-bit denominator |

| `TWO_POINT_VOLTAGE` | 1000.0 mV | Divisor — the reference point of the linear model |

| `SATURATION_DO_25C` | 8.26 mg/L | Multiplier — concentration assigned to that reference voltage |

```cpp

--8<-- "assets/snippets/node2-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

pin and constant definitions · lines 10–32 · commit <code>db6d9b8</code>

</div>

### The complete conversion

Three steps, in the order the firmware performs them.

**Step 1 — counts to millivolts.**

```text

doVoltage_mV = (raw / 4095.0) * 5000.0

```

**Step 2 — temperature compensation factor.**

```text

compTemp   = tempValid ? temp : 25.0

compFactor = 1.0 + (compTemp - 25.0) * (-0.02)

```

The coefficient `-0.02` per °C is a linear approximation applied to a factor

anchored at 25 °C.

**Step 3 — millivolts to concentration, clamped at zero.**

```text

DO_mg_L = (doVoltage_mV / 1000.0) * 8.26 * compFactor

DO_mg_L = max(DO_mg_L, 0.0)

```

### Reading the source

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

The DO block is the second acquisition in the task, immediately after the

DS18B20. It reads `localSnap.temp`, which was populated earlier in the *same*

iteration, so the compensation uses the temperature read in the current cycle.

### What the two-point model assumes

The conversion `DO = (V / 1000 mV) x 8.26` is a straight line through the

origin. It says:

* at an output of 0 mV the concentration is 0 mg/L;

* at an output of 1000 mV the concentration is 8.26 mg/L.

Stated honestly, that model:

* **Assumes proportionality through the origin.** Many dissolved oxygen probes

  have a non-zero, temperature-dependent rest current. If the fitted device has

  an offset, this model will report a non-zero concentration in a genuinely

  oxygen-free sample. The firmware has no intercept term.

* **Assumes the device is linear between and beyond the two points.** There is

  no second, independent calibration point actually measured at commissioning —

  both numbers are compile-time constants.

* **Extrapolates above the reference point without bound.** An output above

  1000 mV yields a proportionally larger concentration, up to the limit

  imposed by the ADC range. Nothing detects saturation.

* **Is calibrated by a constant, not a procedure.** There is no span or zero

  adjustment in the firmware at all — see below.

The `-0.02 / °C` coefficient is likewise a **linear approximation** to a

response that is physically non-linear over the full temperature range. It is

applied to a multiplier, and it is not derived from the fitted device's

specification.

## Calibration

**There is no calibration mechanism in the firmware for this sensor.**

`TWO_POINT_VOLTAGE` and `SATURATION_DO_25C` are compile-time constants; they

cannot be changed at runtime, and they are not stored in NVS. Node 4's serial

calibration console covers pH and EC only — it does not reach Node 2.

| Item | Adjustable? | Mechanism |

|---|---|---|

| `TWO_POINT_VOLTAGE` | No | Compile-time constant, edit and re-flash |

| `SATURATION_DO_25C` | No | Compile-time constant, edit and re-flash |

| Temperature coefficient `-0.02` | No | Literal in the expression |

| Span / zero adjustment | Not implemented | — |

Because there is no field adjustment, the practical options are a

**substitution calibration**: expose the water to a known condition and treat

any systematic error as a gain error, then correct it downstream. The Node 4

calibration console pattern would be the natural place to add this; it is not

there.

Procedure reference: [Dissolved Oxygen Calibration](../calibration/dissolved-oxygen.md).

## Expected values and typical ranges

Derivable **strictly from the firmware constants**:

* Output unit: **mg/L**.

* The concentration assigned to an output of 1000 mV at 25 °C:

  **8.26 mg/L**.

* The lowest output the model can produce: **0 mg/L** (clamped).

* The validity rule: the reading is invalid only when the raw ADC count is

  **exactly zero**.

* Upper bound implied by the ADC scaling: with `VREF` of 5000 mV and a 12-bit

  range, a raw count of 4095 maps to 5000 mV, giving

  `(5000 / 1000) x 8.26` = **41.3 mg/L** before compensation. Whether that is

  physically reachable depends on the fitted board and the ADC's real input

  range.

* Temperature compensation at 25 °C is unity; the factor reaches 0 at 75 °C and

  exceeds 1.0 below 25 °C.

Typical operating range, saturation concentration, and achievable accuracy for

any real wastewater or wetland sample:

> **Not verified from the current source.** No field data, no datasheet and no

> device specification is available to this documentation set. The 8.26 mg/L

> figure is a firmware constant that describes what the code *does*, not a

> statement about the water.

## Failure modes

What the firmware treats as invalid:

* **Raw ADC count of exactly zero.** This is the *only* invalid condition.

This is a weak test and it is worth being explicit about why:

* A disconnected analogue sensor presents as a floating or low input. If that

  reads as a small non-zero count, it will be reported as a small non-zero and

  entirely plausible DO concentration.

* A shorted or saturated sensor presenting a constant count is likewise

  reported as a valid, constant, wrong value.

* There is **no plausibility gate** on the resulting mg/L figure. No upper

  bound, no rate-of-change check, no stuck-value detection.

What a field technician should look for:

* **Pinned at 0.00 mg/l with `node2` healthy.** This is the genuine

  zero-count case, and it is the *only* case the firmware itself can flag.

* **Pinned at a low but non-zero and unchanging value.** Classic signature of an

  open circuit, a failed sensor board, or a probe that has dried out.

* **Pinned high.** A saturated or shorted output, or a disconnected sensor

  board presenting a pulled-up input.

* **A value that tracks temperature but not the water.** When the

  [DS18B20](temperature.md) is producing an error, the compensation factor

  moves and the DO value moves with it.

* **A value that changes only with temperature.** Suspect the temperature

  compensation is dominating a static sensor output, which can look like a

  live measurement.

Field verification note: the raw ADC count and the derived voltage are not

printed to the debug serial port by Node 2. Diagnosing this channel requires

recovering the raw value by other means.

## Environmental considerations

* **Temperature.** Compensation is linear and applied as a multiplier. Outside

  the range where that approximation holds, the error grows. The factor is

  anchored at 25 °C, so readings taken far from 25 °C rely entirely on the

  approximation.

* **Probe immersion and flow.** A membrane-based probe needs consistent

  immersion and some flow across the membrane. The firmware has no way to

  detect either condition.

* **Biofouling.** Membrane fouling reduces sensitivity and typically drifts the

  reading low. Nothing in the firmware detects a slow drift.

* **Inlet disturbance.** Turbulence, entrained air and a falling inlet can

  produce both real and artefactual changes in a dissolved oxygen reading.

* **Altitude.** Air pressure affects oxygen partial pressure and hence

  saturation concentration. The firmware applies no pressure or altitude

  correction, and the 8.26 mg/L constant is not altitude-adjusted.

* **Analogue noise.** A single unfiltered sample per cycle at 1 Hz will pass

  noise straight into the reported value.

## Limitations

Firmware-level limitations, stated plainly:

* **No runtime calibration.** No span, no zero, no NVS storage, no console

  command. Constants are compile-time only.

* **A 5000 mV reference over a 3.3 V-input ADC** — see the risk note under

  [Electrical interface](#electrical-interface). This is the single most

  consequential design decision in this channel, and it is an *engineering

  interpretation* of the source, not a verified device specification.

* **No ADC attenuation is configured** for GPIO 34 by the audited source, so

  the effective input range of the conversion is not established.

* **No filtering at all.** One sample, used directly. This is unlike Node 4's

  analogue channels, which average 16 samples.

* **No plausibility bounds** on the output. Only the zero-count case is caught.

* **The linear model has no intercept.** A probe with a rest current will read

  high.

* **The two "calibration points" are constants, not measurements.** Nothing in

  the system verifies that 1000 mV corresponds to 8.26 mg/L for the fitted

  device, or at the current temperature.

* **The temperature coefficient is an unexplained literal.** Its provenance is

  not documented in the source.

* **No diagnostic output.** Unlike Node 4, Node 2 prints no raw ADC or voltage

  for this channel.

* **Temperature-compensation failure is silent.** If the DS18B20 fails, DO is

  still reported as valid using the 25 °C default.

## Maintenance and replacement

The DO probe is the item on Node 2 most likely to need periodic attention,

because it is immersed and because no calibration interface exists to recover

its accuracy after service. Replacement should be treated as a

**re-baselining** exercise: record the observed output in a known condition

before and after fitting a new probe, since the firmware offers no way to trim

the result.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md).

Routine checks: [Maintenance](../field-service/maintenance.md).

> **Not verified from the current source.** Sensor part number, supply

> voltage, output range, cable type, length, gauge and connector pinout. No

> schematic exists in the repository.

## Where it is used

| Node | GPIO | ADC bank | Reading function | Frame field | Valid flag |

|---|---|---|---|---|---|

| 2 | 34 (`PIN_DO_ANALOG`) | ADC1 | `Task_Sensors_Node2` | `DO` | `node2` |

The reading is consumed by:

* Node 2's own UART task, which emits it as `DO:%.2f` towards Node 3 / Node 4

  and echoes it back to Node 1;

* Node 1's LCD, row 2: `DO{value}mg/l`, shown as `--` when unavailable.

The temperature it depends on is measured by

[DS18B20 water temperature](temperature.md) on the same node.

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),

branch `main`, commit

[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)

(short `db6d9b8`).

| Snippet | Source path | Symbol | Lines |

|---|---|---|---|

| `node2-pin-definitions` | `FreeRTOS_Implementation/Node2/Node2.ino` | — | 10–32 |

| `node2-sensor-task` | `FreeRTOS_Implementation/Node2/Node2.ino` | `Task_Sensors_Node2` | 98–220 |

| `node2-uart-routing` | `FreeRTOS_Implementation/Node2/Node2.ino` | `Task_UART_Node2` | 259–370 |

| `node1-lcd-task` | `FreeRTOS_Implementation/Node1/Node1.ino` | `Task_LCD_Node1` | 220–310 |

Everything on this page is *firmware implementation* unless explicitly labelled

otherwise. The 0–3.3 V ADC input range and GPIO 34's input-only nature are

stated as *engineering interpretation* of ESP32 behaviour, not as verified

CIRQUA specifications. No manufacturer specification for the dissolved oxygen

sensor is available.

Related: [Sensors overview](index.md) ·

[Dissolved Oxygen Calibration](../calibration/dissolved-oxygen.md) ·

[Water Temperature](temperature.md) ·

[Sensor Replacement](../field-service/sensor-replacement.md)


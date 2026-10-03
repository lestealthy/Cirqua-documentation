---
title: Sensors
description: Reference for the eight sensors in the CIRQUA cluster — ultrasonic level, DS18B20, dissolved oxygen, flow, pH, turbidity, conductivity and DHT11 ambient.
---

# Sensors

The CIRQUA cluster measures eight quantities across four ESP32 nodes. This
section documents each sensor in two separate terms: **what the device does in
principle** (generic, and explicitly unattributed where no datasheet has been
checked) and **what the firmware actually does with it** (audited against the
source at commit `db6d9b8`).

Those two things are kept strictly apart throughout, because they diverge more
than is comfortable. Most of the cluster's calibration constants are
compile-time literals with no field adjustment path; two channels — pH and
conductivity — can be recalibrated from a serial console; and one channel —
dissolved oxygen — applies a 5 V reference to a 3.3 V ADC.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Sensor types</span>
    <span class="cirqua-identity__value">8</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Nodes</span>
    <span class="cirqua-identity__value">1, 2, 3, 4 (+ Node 4 SMTP variant)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Interfaces</span>
    <span class="cirqua-identity__value">Digital pulse, 1-Wire, single-wire digital, ADC (4 analogue channels)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Framework</span>
    <span class="cirqua-identity__value">Arduino ESP32, FreeRTOS tasks</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Named in source</span>
    <span class="cirqua-identity__value"><code>HC-SR04</code>, <code>DS18B20</code>, <code>DHT11</code>, <code>SEN0189 / DFRobot</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Status</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> audited at commit <code>db6d9b8</code></span>
  </div>
</div>

## Sensor Matrix

| Sensor | Node(s) | Measurement | Interface | GPIO | Frame field | Calibration required |
|---|---|---|---|---|---|---|
| [Ultrasonic level](ultrasonic.md) | 1, 2, 4 | Volume, litres | Digital time-of-flight (trigger / echo) | N1 2 / 17 · N2 16 / 17 · N4 4 / 2 | `TAV` (N1), `TBV` (N2), `TCV` / `EV` (N4) | **Yes — compile-time geometry, no runtime path.** Node 1 additionally applies an unexplained ×2.0 factor |
| [Water temperature](temperature.md) — DS18B20 | 2, 4 | Temperature, °C | 1-Wire digital | N2 4 · N4 27 | `Temp` (N2), `ST` (N4 SMTP only) | **No** — no offset, gain or stored constant |
| [Dissolved oxygen](dissolved-oxygen.md) | 2 | Concentration, mg/L | Analogue ADC1, 12-bit | 34 | `DO` | **Yes — compile-time constants only.** No span, zero or console command exists |
| [Flow rate](flow.md) | 3 | Flow, L/min | Digital pulse, `INPUT_PULLUP`, FALLING ISR | 23 | `FLM` | **Yes — `FLOW_CAL_FACTOR` is compile-time only** (5.5 pulses/litre) |
| [pH](ph.md) | 4 | pH | Analogue ADC2, 12-bit, 11 dB | 13 | `pH` | **Yes — field-adjustable** via `SET:PH_S=` / `SET:PH_O=`, persisted to NVS `node4_cal` |
| [Turbidity](turbidity.md) | 4 | Turbidity, NTU (integer) | Analogue ADC2, 12-bit, 11 dB | 14 | `Turb` | **Yes — the SEN0189 polynomial is compile-time only**, with no console command |
| [Conductivity](conductivity.md) | 4 | EC, µS/cm (or mS/cm on SMTP) | Analogue ADC2, 12-bit, 11 dB | 12 | `EC` | **Yes — field-adjustable** via `SET:EC_K=`, persisted to NVS `node4_cal` |
| [Ambient temperature and humidity](humidity.md) — DHT11 | 2, 4 | Temperature °C, humidity % | Single-wire digital | N2 27 · N4 5 | `AT`, `AH` (N2 only in the frame) | **No** — no offset or constant of any kind |

### Calibration at a glance

Only two channels can be calibrated in the field without reflashing:

| Channel | Command | NVS namespace | Default (`Node4`) |
|---|---|---|---|
| pH slope | `SET:PH_S=<val>` | `node4_cal` | `3.5f` |
| pH offset | `SET:PH_O=<val>` | `node4_cal` | `-1.75f` |
| Conductivity K-factor | `SET:EC_K=<val>` (rejects ≤ 0) | `node4_cal` | `9.997f` |

`Node4_SMTP` ships different defaults: `phOffset = 0.0f` and `ecKFactor = 2.0f`.

## Which node measures what

| Node | Sensors present | GPIO | Frame field emitted | Local LCD |
|---|---|---|---|---|
| **1** — Collection Tank A, cluster head | Ultrasonic level | TRIG 2, ECHO 17 | `TAV` | Yes, 16×4 I²C at 0x27 |
| **2** — Feeding Tank B, water telemetry | Ultrasonic level, DS18B20 water temperature, dissolved oxygen, DHT11 ambient | TRIG 16, ECHO 17, DS18B20 4, DO 34, DHT11 27 | `TBV`, `DO`, `Temp`, `AT`, `AH` | No |
| **3** — Flow metering | Flow pulse | 23 | `FLM` | No |
| **4** — Effluent analytics, cluster tail | Ultrasonic level, DS18B20 submerged temperature, pH, turbidity, conductivity, DHT11 ambient | TRIG 4, ECHO 2, DS18B20 27, pH 13, Turb 14, EC 12, DHT11 5 | `pH`, `Turb`, `EC`, `TCV` (SMTP: `EV`, `ST`) | Yes, 16×4 I²C at 0x27 |

!!! WARNING
    **Pin numbers do not carry across nodes.** Node 1 and Node 2 both use
    **GPIO 17** for ECHO. GPIO 2 is Node 1's TRIG but Node 4's ECHO. Never wire
    two nodes' parts together by number. The authoritative table is
    [GPIO Map](../hardware/gpio-map.md).

## Sensor pages

### [Ultrasonic level](ultrasonic.md)

Time-of-flight tank level converted to litres by a cylindrical tank model.
Three instances with different pins, different echo timeouts and different
geometry. Node 1 doubles the computed volume; the firmware gives no reason.

### [Water temperature](temperature.md)

DS18B20 on a 1-Wire bus, twice: Node 2 non-blocking with a one-cycle pipeline
delay, Node 4 at 10-bit resolution and deliberately blocking. Node 4's
submerged reading is the temperature compensation input for both pH and
conductivity, and silently falls back to 25 °C when it fails.

### [Dissolved oxygen](dissolved-oxygen.md)

Analogue on ADC1 GPIO 34, converted by a two-point linear model with a linear
temperature coefficient. No calibration interface exists, the model has no
intercept, and the 5000 mV reference applied to a 3.3 V-input ADC is documented
here as an engineering risk rather than a specification.

### [Flow rate](flow.md)

Pulse counting on Node 3 GPIO 23 with a FALLING-edge ISR and a critical-section
counter. L/min from a one-second count divided by 5.5 pulses/litre. The
validity flag is hard-coded true under all circumstances.

### [pH](ph.md)

Analogue on ADC2 GPIO 13. A linear slope/offset model, **not** a Nernst
electrochemical model, with a compensation that compresses readings towards
neutrality as temperature rises. The only channel with a full two-point field
calibration.

### [Turbidity](turbidity.md)

Analogue on ADC2 GPIO 14, piecewise SEN0189 / DFRobot conversion. The source
records that the original code wrongly used a 5.0 V ADC reference and now uses
the real voltage at the pin — which materially changes results and breaks
comparability with `_OLD` data.

### [Conductivity](conductivity.md)

Analogue on ADC2 GPIO 12, K-factor conversion with 25 °C normalisation.
**The two Node 4 variants report different units under the same field name:**
`Node4` gives µS/cm, `Node4_SMTP` gives mS/cm. No TDS is computed anywhere.

### [Humidity and ambient temperature](humidity.md)

DHT11 on Nodes 2 and 4, paced at most every 2 seconds. Node 2 accepts any
non-`NAN` value; Node 4 adds range gates — but the SMTP variant uses Node 2's
weaker gating. Node 1 derives `OVERTEMP` and `HI HUMID` from Node 2's values.

## Cross-cutting observations

Things that apply to more than one sensor and are documented on the individual
pages as well:

* **Validity is a per-node boolean, not a shared mechanism.** Each sketch
  applies its own rules. Flow has no invalid state at all; dissolved oxygen has
  exactly one; pH combines an input voltage window with a pH range; turbidity
  and conductivity accept saturation and zero respectively as legitimate.
* **A failed temperature sensor does not fail its dependents.** The DO, pH and
  EC compensations silently substitute 25.0 °C and continue to report valid.
  Always check the node health flag before trusting a compensated channel.
* **Node 4's analogue channels are well conditioned; Node 2's is not.** Node 4
  averages 16 samples, discards the first after a channel switch, uses
  `analogReadMilliVolts()` and sets 11 dB attenuation explicitly. Node 2's
  dissolved oxygen channel takes a single raw `analogRead()`, applies no
  attenuation setting, and scales by an assumed 5 V reference.
* **Two channels are field-calibrable; six are not.** The Node 4 console reaches
  pH and EC only.
* **Most constants are compile-time literals** with no NVS storage and no
  runtime path: `0.0343f` cm/µs, `FLOW_CAL_FACTOR`, the DO constants, the
  turbidity polynomial, the temperature compensation coefficients.
* **Node health flags are the only failure signal downstream.** A consumer sees
  a value and a per-node flag, never a reason. A structurally valid but
  physically wrong reading is reported as healthy.
* **No datasheet has been checked** for the dissolved oxygen, flow, pH or
  conductivity devices, and no part number exists for them in the source.
  Accuracy figures are therefore not stated on any of these pages.

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),
branch `main`, commit
[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)
(short `db6d9b8`).

Every constant, GPIO, formula, timeout, unit and validity rule in this section
is taken from the firmware at that commit. Statements about device
specifications are generic and unattributed unless a part name appears in a
source comment, in which case it is reported as an attribution only.

Related: [GPIO Map](../hardware/gpio-map.md) ·
[Nodes](../nodes/index.md) · [Calibration](../calibration/index.md) ·
[Message Format](../communication/message-format.md) ·
[Known Limitations](../validation/known-limitations.md) ·
[Sensor Replacement](../field-service/sensor-replacement.md)

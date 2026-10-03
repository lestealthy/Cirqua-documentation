---
title: Maintenance
description: Recommended maintenance intervals for the CIRQUA sensors and enclosures, with a maintenance log template and an honest note on what is not published.
---

# Maintenance

!!! warning

    **Every interval on this page is a recommendation, not a documented schedule.** The
    firmware repository contains **no maintenance schedule, no consumable part numbers,
    no service intervals and no calibration calendar**. These intervals are our
    engineering judgement based on the sensor types and duty cycles the firmware
    actually implements. They must be reviewed, agreed and owned by the project before
    being treated as authoritative.

Claim types used throughout: **Firmware implementation**, **Engineering
interpretation**, **Recommendation**.

## What the firmware actually does to the sensors

**Firmware implementation.** Understanding the duty cycle tells you how much load each
sensor carries:

| Sensor | Node | Task period | Notes from the source |
|---|---|---|---|
| DS18B20 submerged | 4 | 1 Hz | `setResolution(10)`, `setWaitForConversion(true)` — **blocking** ~187.5 ms per cycle by design |
| DS18B20 water | 2 | 1 Hz | `setWaitForConversion(false)` — non-blocking, conversion requested each cycle |
| DHT11 ambient | 2, 4, SMTP | at least 2000 ms | Paced by `xLastDHTTick`; the DHT11 is a slow, lossy part |
| Ultrasonic HC-SR04 | 1 | 500 ms | 2 Hz, 20–30 ms `pulseIn` blocking each cycle |
| Ultrasonic HC-SR04 | 2, 4 | 1 Hz | 1 Hz |
| pH / turbidity / EC ADC | 4 | 1 Hz | 16 averaged `analogReadMilliVolts()` samples per channel per cycle |
| Flow pulse ISR | 3 | 1 Hz aggregation | Free-running counter; count is reset and re-based each second |

**Engineering interpretation.** Two consequences for maintenance planning:

- The submerged DS18B20 conversion **blocks the Node 4 sensor task** for roughly 190 ms
  of every second. That is a designed-in latency, not a fault, and it means the Node 4
  cycle is inherently long. Do not "optimise" it in the field.
- **The ultrasonic on Node 1 is polled twice a second, in a blocking `pulseIn`.** That is
  the highest-duty sensor in the system and the most exposed to condensation and dust.

## Recommended intervals

### Ultrasonic sensor — face cleaning and re-verification

**Engineering interpretation.** The HC-SR04 transducers couple acoustically to the water
and are exposed to condensation, biofilm and mineral deposit. Deposits attenuate the echo
and shift the measured distance, which the firmware will happily convert into litres. There
is no filter, averaging or hysteresis to suppress a degraded return.

| Interval | Action |
|---|---|
| **Monthly** | Visual inspection of the transducer face through the housing window. Clean with a soft, lint-free cloth. |
| **Quarterly** | Clean and re-verify the level against an independent height measurement — see [Ultrasonic calibration](../calibration/ultrasonic.md#step-by-step-verification-procedure) |
| **After any cleaning event, heavy rain, or a fog episode** | Re-verify |
| **Annually** | Confirm the ×2 factor on Node 1 still matches the ratio you established; replacement units drift |

**Recommendation.** If condensation forms inside the ultrasonic housing, fix the housing
seal before anything else. A clean face with a leaking housing will re-foul within days.

### DHT11 — long-term drift

**Engineering interpretation.** The DHT11 is a low-cost humidity sensor with known
long-term drift and a narrow operating range. It is used here only for ambient
enclosure conditions — the alarm thresholds are 45 °C and 80 % RH — so its absolute
accuracy matters less than its *trend*. Node 1 will display `OVERTEMP`, `HI HUMID` or
`HOT+HUM` purely on this reading, so a drifting DHT11 can generate persistent false
alarms.

| Interval | Action |
|---|---|
| **Six-monthly** | Compare Node 1's `AT` / `H` display against a reference hygrometer at the same location |
| **Annually** | Replace, or at minimum re-baseline |
| **Whenever the status word shows `OVERTEMP`, `HI HUMID` or `HOT+HUM` unexpectedly** | Verify against a reference before acting — the sensor may be wrong rather than the enclosure |

**Recommendation.** Do not adjust the firmware thresholds to silence a suspect DHT11. The
thresholds are compile-time constants and changing them hides the actual condition.

### DS18B20 — probe sealing and cable strain

**Recommendation.**

| Interval | Action |
|---|---|
| **Quarterly** | Inspect the cable entry and strain relief. Check for moisture ingress, cracking or a stiff section |
| **Semi-annually** | Verify the reading against a reference thermometer at depth. Confirm the probe is still fully submerged at all times |
| **Annually** | Replace the cable and re-seal. Confirm `getDeviceCount() > 0` on Node 4 |
| **After any replacement** | Node 4's temperature feeds the pH and EC compensation, so re-check those channels — see [Sensor replacement](sensor-replacement.md#ds18b20-watersubmerged-temperature) |

**Engineering interpretation.** A 1-Wire bus is a single data line with no error
detection. A chafed cable produces intermittent, apparently random failures that are very
hard to diagnose from telemetry. Physical inspection is the only reliable method.

### pH electrode — bulb condition, electrolyte and storage

**Engineering interpretation.** Electrodes are consumables. Their behaviour changes with
use, with contamination and with dehydration. The firmware applies a legacy
straight-line model with a single temperature compensation divisor, so it has no ability
to compensate for a drifting or poorly hydrated electrode — a degraded electrode looks
exactly like a mis-calibrated one.

| Interval | Action |
|---|---|
| **Before and after every removal from the water** | Rinse with deionised water and store in the manufacturer's storage solution. **Never** store dry and never store in tap water |
| **Monthly** | Inspect the glass bulb for cracks, cloudiness or a dried-out junction |
| **Quarterly** | Two-point calibration check with pH 7 and pH 4 or pH 10 — see [pH calibration](../calibration/ph.md#full-two-point-buffer-calibration) |
| **Annually, or per the electrode manufacturer's stated life** | Replace the electrode and re-calibrate from scratch |
| **Whenever the reading is unstable, sluggish, or drifts between buffers** | Treat as an electrode fault, not a calibration fault |

**Recommendation.** Keep spare electrodes and buffers on site. The firmware's `node4_cal`
values are specific to one electrode; a swapped electrode invalidates them.

### Turbidity — optical surface and biofilm

**Recommendation.**

| Interval | Action |
|---|---|
| **Monthly** | Inspect and clean the optical window. A soft cloth; do not scratch the surface |
| **Quarterly** | Run the visual cross-check against prepared samples — see [Turbidity calibration](../calibration/turbidity.md#verification-procedure) |
| **Annually** | Confirm clear water still reads well below 3.20 V |
| **Whenever `TU:` is stuck at `0` or `3000`** | Clean first. Both values are also correct outputs at the extremes, so neither indicates a fault by itself |

**Engineering interpretation.** Biofilm on the optical window is the dominant failure
mode for in-line optical sensors in this kind of water. The firmware's validity rule
(`0.0 <= V <= 3.30`) will happily accept a heavily fouled reading as valid.

### EC probe — cell cleaning

**Recommendation.**

| Interval | Action |
|---|---|
| **Monthly** | Inspect the cell for deposit and biofilm |
| **Quarterly** | Clean per the manufacturer's method and re-verify the K-factor against a standard |
| **Annually** | Replace the cell if cleaning no longer restores the reading |
| **After any period out of the water** | Refill and re-condition the cell before trusting readings |

**Engineering interpretation.** EC cells foul in a way that usually shows first as a
falling K-factor requirement. Re-derive the K-factor **after** cleaning, never before —
otherwise you absorb the fouling into the calibration and it will persist after the cell
is clean.

### Flow sensor — impeller, hall pickup and debris

**Recommendation.**

| Interval | Action |
|---|---|
| **Monthly** | Check for debris in the bore and confirm the impeller spins freely with no grit |
| **Quarterly** | Compare `FLM:` against an independent measurement during a known flow |
| **Annually** | Clean the impeller and inspect the hall pickup |

**Engineering interpretation.** Because Node 3 always sets the validity flag true,
`FLM:0` is never reported as invalid. Debris blocking the impeller and a disconnected
sensor are **indistinguishable from telemetry**. Physical verification is mandatory.
Also note the counter is a free-running `uint32_t` with **no overflow detection**, and
the firmware assumes 50 % duty.

### LCD and enclosure seals

**Recommendation.**

| Interval | Action |
|---|---|
| **Quarterly** | Inspect the enclosure gasket and cable glands for compression set, tearing or water tracks |
| **Quarterly** | Confirm the LCD backlight is on and all four rows are legible and complete |
| **Annually** | Replace the gasket; check the enclosure for UV embrittlement and cracking |

**Recommendation.** Open enclosures in a dry state. Node 1's own firmware treats 80 % RH
and 45 °C as alarm conditions because condensation is expected here.

### The 3.3 V rail under Wi-Fi load (SMTP variant)

**Recommendation.**

| Interval | Action |
|---|---|
| **At every service visit** | Measure the 3.3 V rail at the ESP32 pins **while the SMTP variant is transmitting**, and record it |
| **Annually** | Repeat under sustained Wi-Fi activity |

**Engineering interpretation.** `Node4_SMTP` brings Wi-Fi and an SMTP client onto a node
whose analogue channels depend directly on the supply: pH, turbidity and EC are read from
the ESP32 ADC and converted with `analogReadMilliVolts()`. Any sag or noise on the 3.3 V
rail appears as ADC error on all three channels simultaneously, and Wi-Fi TX is the
largest transient load in the system.

**A useful diagnostic:** if all three Node 4 analogue channels shift together, suspect the
supply before suspecting three failed sensors. That pattern is in the
[Troubleshooting](troubleshooting.md#reading-raw-adc-counts) table.

> **Not verified from the current source.** Power supply voltage, regulator part
> numbers, battery or solar topology, and any measured tolerance or ripple requirement
> for the 3.3 V rail. The value measured here is a field observation, not a
> specification.

## Maintenance log template

Copy this table into your own records. There is **no log format defined in the
repository**; this template covers what the firmware makes worth recording.

| Date | Node | Task | Reading before | Reading after | Action | Technician |
|---|---|---|---|---|---|---|
| | 1 | Ultrasonic face cleaned, level re-verified | | | | |
| | 2 | DHT11 compared with reference | | | | |
| | 2 | DS18B20 cable and seal inspected | | | | |
| | 2 | DO checked against reference | | | | |
| | 3 | Impeller cleaned, `FLM` verified | | | | |
| | 4 | pH two-point check | | | | |
| | 4 | Turbidity window cleaned, cross-check | | | | |
| | 4 | EC cell cleaned, K-factor re-derived | | | | |
| | 4 | 3.3 V rail measured under load | | | | |
| | 4 | NVS calibration persistence confirmed after power-cycle | | | | |
| | all | Enclosure seals and glands inspected | | | | |

### Columns worth extra care

**Reading before / Reading after** — these are the most valuable columns and the ones most
often left blank. For each task record the actual values, not "OK":

- Level in litres **and** the independent height measurement, so a drift is visible.
- pH slope and offset, or the EC K-factor, from `STATUS` — these persist in NVS and are the
  clearest evidence of drift.
- Raw ADC counts and volts from `STATUS`, not just the computed value.
- The 3.3 V rail measurement in volts.

**Action** — state what was changed *and whether it required a re-flash*. The distinction
matters: pH and EC survive in NVS; tank geometry, the Node 1 ×2 factor, the DO constants
and the flow K-factor do not.

**Technician** — one person, named. The repository holds no shared service record.

## What is not published

State this plainly in any maintenance record:

- **No maintenance intervals** are defined in the firmware repository. The intervals on
  this page are recommendations only.
- **No consumable part numbers.** Only HC-SR04, DS18B20 and DHT11 are named in the
  source. The DO, flow, pH and EC modules are unnamed, so replacement parts cannot be
  specified from this documentation.
- **No calibration schedule** and no calibration certificate or traceability statement.
- **No schematics, circuit diagrams or wiring records.**
- **No enclosure dimensions, materials or IP rating.** This documentation makes no claim
  about any of them.
- **No hardware photographs** and no confirmation that any node is deployed in the field.
- **No flow K-factor calibration page** in this documentation set, despite the flow K
  factor being a compile-time constant like the others.

**Recommendation.** The project should adopt this log, agree the intervals, and record
them as project documentation. Until it does, the maintenance history of any node exists
only in whatever notebook the technician carried.

## Related pages

- [Field service index](index.md)
- [Sensor replacement](sensor-replacement.md)
- [Startup checklist](startup-checklist.md)
- [Troubleshooting](troubleshooting.md)
- [Calibration index](../calibration/index.md)
- [Validation: hardware validation](../validation/hardware-validation.md)
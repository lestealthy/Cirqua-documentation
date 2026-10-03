---
title: Terminology
description: Glossary of CIRQUA, wastewater, sensor and telemetry terms, plus every telemetry field key emitted by the ESP32 node chain with its meaning and unit.
---

# Terminology

## Project and partner terms

| Term | Meaning |
|---|---|
| **CIRQUA** | The funded research project: *"Integrated Approaches at Local Scale for Enhancing Water Reuse Efficiency and Sustainable Soil Fertilization from Wastewater's Recovered Nutrients"*. Horizon Europe funded, 4.09 million EUR, 36 months from April 2024 to March 2027, 13 partners across 10 countries and 3 continents. Attributed to `cirqua-water.eu` |
| **Waterwise Futures** | The project's public branding tag. A theme, not a separate technical system |
| **CW** | Constructed Wetland. Engineered, planted, surface-flow or subsurface treatment media used in this project for wastewater treatment and water recovery |
| **NBS** | Nature-Based Solution. A treatment approach that uses ecological processes — in this project, constructed wetlands — rather than purely engineered unit processes |
| **ABC** | African Biotechnology Company. CIRQUA project partner, founded 2017, based in Tunis, Tunisia |
| **WattLab** | Author and maintainer of this documentation and of the firmware repository. Separate from both the project and the partner |
| **N2-fixing legume cultivation** | Project strand: cultivation of nitrogen-fixing legumes, relevant because fixed nitrogen is one of the recovered nutrients |
| **Nutrient valorisation** | Recovery of nitrogen and other nutrients from treated wastewater for reuse as fertiliser |

## Hardware and software terms

| Term | Meaning |
|---|---|
| **ESP32** | The microcontroller on every node. Dual-core, with two additional hardware UARTs available for inter-node links |
| **UART1 / UART2** | `HardwareSerial` instances used for the inter-node chain. The numbers are *device-local*: which physical UART is used for which neighbour differs per node |
| **FreeRTOS** | The real-time kernel the firmware runs on. All work happens in FreeRTOS tasks; the Arduino `loop()` task deletes itself |
| **Task pinning** | `xTaskCreatePinnedToCore` assigns each task to core 0 or core 1. Sensor and display tasks run on core 1; UART tasks run on core 0 |
| **NVS / Preferences** | Non-Volatile Storage, the ESP32 key/value store. Reached through the Arduino `Preferences.h` library. Used namespaces: `node4_cal` (calibration constants) and `email_state` (e-mail timestamps) |
| **ISR** | Interrupt Service Routine. On Node 3 the flow-pulse ISR is `IRAM_ATTR pulseISR()` and fires on the **falling** edge |
| **ADC1 / ADC2** | The two ESP32 SAR ADC peripherals. Node 2's dissolved-oxygen input is on ADC1 (GPIO 34); Node 4's pH, turbidity and EC inputs are on ADC2 (GPIO 13, 14, 12) |
| **1-Wire** | The single-wire digital bus used by the DS18B20 water-temperature probes on Node 2 (GPIO 4) and Node 4 (GPIO 27) |
| **HD44780** | The controller family behind the 16×4 character LCDs. Node 4 addresses its rows via DDRAM commands `0x80 \| addr` with `addr` = `0x00`, `0x40`, `0x10`, `0x50` |
| **PWM** | Pulse-width modulation. **Not used in the audited firmware.** No PWM output, LED or buzzer is initialised in any of the current sketches. On-board LED use is a board-specific matter and is not recorded in this repository |

### Sensor parts named in the source

| Term | Meaning |
|---|---|
| **HC-SR04** | Ultrasonic distance sensor. Used on Node 1, Node 2 and Node 4 to derive tank level, then tank volume. Time-of-flight is converted with the speed constant `0.0343f` cm/µs, halved for the round trip |
| **DS18B20** | Programmable-resolution digital temperature sensor on the 1-Wire bus. Water temperature on Node 2; submerged temperature on Node 4 |
| **DHT11** | Combined ambient temperature and relative-humidity sensor. On Node 2 and Node 4, paced to a minimum 2000 ms between reads |

> **Not verified from the current source.** Manufacturer part numbers, brands and
> calibration certificates for the dissolved-oxygen, flow, pH and conductivity
> sensors. Only the HC-SR04, DS18B20 and DHT11 are named in the firmware. The
> turbidity code comments cite SEN0189 / DFRobot, but no part number is
> configured in code.

### Water-quality terms

| Term | Meaning |
|---|---|
| **DO** | Dissolved Oxygen. Measured on Node 2 from an analog probe on GPIO 34 and reported in **mg/L**, temperature-compensated |
| **NTU** | Nephelometric Turbidity Unit — the unit of the turbidity value. The Node 4 conversion is valid over 0–3000 NTU |
| **EC** | Electrical Conductivity. The measure used to indicate dissolved-ion concentration. Reported in **µS/cm** by `Node4` and in **mS/cm** by `Node4_SMTP` — see the divergence note below |
| **µS/cm** | Microsiemens per centimetre. The unit `Node4` uses for EC: raw volts times the K-factor, temperature-compensated, then ×1000 |
| **mS/cm** | Millisiemens per centimetre. The unit `Node4_SMTP` uses: raw volts times the K-factor, **no** temperature compensation and **no** ×1000 |
| **pH** | Acidity measure, valid range 0–14. Node 4 applies a linear calibration `pH = slope × V + offset` and then a temperature compensation around pH 7 |

!!! warning "EC unit divergence is real"
    `Node4` emits `EC` in µS/cm with a `TCV` volume field. `Node4_SMTP` emits
    `EC` in mS/cm with `EV` and `ST` instead. This is a genuine difference between
    the two builds and is documented, not reconciled. A downstream consumer must
    know which build is at the end of its chain.

## Telemetry field keys

These are the literal keys that appear in frames on the wire. Field separator is
`|`, key/value separator is `:`, terminator is `;` followed by a newline.

| Key | Produced by | Meaning | Unit | Notes |
|---|---|---|---|---|
| `TAV` | Node 1 | Tank A volume — Collection Tank A | litres | Emitted as an **integer**; the computed volume is multiplied by 2.0 before the cast. See the calibration warning below |
| `node1` | Node 1 | Node 1 local sensor-health flag | `1` or `0` | `1` means all of Node 1's own local validity flags are true |
| `TBV` | Node 2 | Tank B volume — Feeding Tank B | litres | Emitted as a float with 2 decimals |
| `DO` | Node 2 | Dissolved oxygen | mg/L | Temperature-compensated; invalid if the raw ADC read is zero |
| `Temp` | Node 2 | Water temperature, DS18B20 | °C | Invalid if the sensor reports `DEVICE_DISCONNECTED_C` or the value is outside −55 °C…125 °C |
| `AT` | Node 2 | Ambient temperature, DHT11 | °C | Paced to a minimum 2000 ms interval |
| `AH` | Node 2 | Ambient humidity, DHT11 | % | Paced to a minimum 2000 ms interval |
| `node2` | Node 2 | Node 2 local sensor-health flag | `1` or `0` | `1` means all of Node 2's local validity flags are true |
| `FLM` | Node 3 | Flow rate | L/min | Pulses per litre factor `5.5f`; recomputed each 1000 ms from a reset pulse count |
| `node3` | Node 3 | Node 3 local sensor-health flag | `1` or `0` | Set independently of Node 1 and Node 2 flags |
| `pH` | Node 4 | Acidity of the effluent | pH units (0–14) | Valid only when the input voltage is 0.02–3.30 V *and* the result is 0–14 |
| `Turb` | Node 4 | Turbidity | NTU | Piecewise conversion; saturated 0 NTU and full-scale 3000 NTU are treated as *valid*, not as faults |
| `EC` | Node 4 | Electrical conductivity | µS/cm (`Node4`) / mS/cm (`Node4_SMTP`) | Valid over 0–3.30 V; a reading of zero EC is accepted as legitimate |
| `TCV` | Node 4 | Effluent tank volume | litres | Emitted as an integer by the `Node4` build only |
| `ST` | Node 4 | Submerged water temperature, DS18B20 | °C | Emitted by the `Node4_SMTP` build. On the `Node4` build the same quantity is not sent downstream |
| `EV` | Node 4 | Effluent volume | litres | Emitted by the `Node4_SMTP` build, in place of `TCV` |
| `node4` | Node 4 | Node 4 local sensor-health flag | `1` or `0` | Hard-coded as `1` in the downstream frame emitted to the controller |

!!! note "On the health flags"
    Each frame carries exactly one `nodeN` flag describing the node that
    measured the data immediately preceding it. `cleanUpstreamPacket` on Node 4
    removes the upstream `AT:` and `AH:` tokens so that the controller receives a
    single ambient pair from Node 4's own DHT11 — the upstream ambient values are
    dropped, not merged.

!!! warning "TAV carries an empirical fudge factor"
    Node 1 computes volume from cylinder geometry and then applies
    `volumeLiters = (int)(volumeLiters * 2.0f)`. This doubling is a hard-coded
    compensation, **not** a geometric correction. It must be treated as an
    empirical calibration factor that needs verification per installation, and it
    cannot be derived from the cylinder formula. See
    <a href="../calibration/ultrasonic.html">Calibration: Ultrasonic</a>.

> **Not verified from the current source.** Abbreviation expansions for `TAV`,
> `TBV`, `TCV` and `EV` beyond the tank roles listed above. The values and units
> are audited; the intended letter-by-letter expansion is not stated in the
> firmware.

## Acronyms used across these pages

| Acronym | Expansion |
|---|---|
| RTOS | Real-Time Operating System |
| ISR | Interrupt Service Routine |
| PWM | Pulse-Width Modulation (unused in the audited firmware) |
| ADC | Analogue-to-Digital Converter |
| NVS | Non-Volatile Storage |
| SSL/TLS | Secure Sockets Layer / Transport Layer Security |
| SMTP | Simple Mail Transfer Protocol |
| LCD | Liquid Crystal Display |
| SSID | Service Set Identifier (wireless network name) |
| CW / NBS | Constructed Wetland / Nature-Based Solution |
| ABC | African Biotechnology Company |
| EUR | Euro |

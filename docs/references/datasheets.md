---
title: Datasheets And Component Documentation
description: Component references for the parts named in the CIRQUA firmware - roles, pins, where each appears in the source, and what documentation is missing.
---

# Datasheets And Component Documentation

This page lists only what can be honestly listed. A component appears here if
its **part name appears in the firmware source** at commit
[`db6d9b8`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55).
Anything the source does not name is recorded as **unidentified**, not guessed.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Parts named in source</span>
    <span class="cirqua-identity__value"><code>HC-SR04</code> · <code>DS18B20</code> · <code>DHT11</code> · <code>ESP32</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Parts named only by comment</span>
    <span class="cirqua-identity__value"><code>SEN0189 / DFRobot</code> — turbidity, comment only</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Parts NOT named in source</span>
    <span class="cirqua-identity__value">dissolved oxygen · flow · pH · conductivity modules</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Board variant</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--unknown">unverified</span> — <strong>Not verified from the current source.</strong></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Schematics / photographs</span>
    <span class="cirqua-identity__value">None exist in the repository</span>
  </div>
</div>

!!! danger "No figure on any sensor page is a datasheet figure"
    The pages in this documentation set quote **firmware constants** — for
    example `TANK_HEIGHT 260.0f` or `SATURATION_DO_25C 8.26f`. These are values
    the firmware uses, which is a different thing from a device specification.
    No range, accuracy, resolution, lifetime or environmental limit is asserted
    anywhere in this documentation set on the basis of a datasheet, because the
    datasheets have not been read into it.

## Components named in the firmware

### HC-SR04 — ultrasonic distance sensor

| Aspect | Value |
|---|---|
| Role in CIRQUA | Non-contact liquid level in three tanks, converted to volume in litres |
| Node(s) | 1 (Collection Tank A, `TAV`), 2 (Feeding Tank B, `TBV`), 4 (effluent, `TCV` / `EV`) |
| GPIO | N1 TRIG `2` / ECHO `17` · N2 TRIG `16` / ECHO `17` · N4 TRIG `4` / ECHO `2` |
| Interface | Digital: trigger out, echo in, `pulseIn()` |
| Named in source | `FreeRTOS_Implementation/Node1/Node1.ino` lines 10–11 (`PIN_N1_TRIG`, `PIN_N1_ECHO`); `Node2/Node2.ino` lines 14–15; `Node4/Node4.ino` lines 13–14. The part name `HC-SR04` appears in source comments in those sketches and on the [Ultrasonic Level](../sensors/ultrasonic.md) page's provenance trail |
| Commit | `db6d9b8` |
| Firmware constants | `0.0343f` cm/µs, halved for round trip; timeouts 30000 / 20000 / 25000 µs |

!!! warning "There is no authoritative HC-SR04 datasheet"
    The `HC-SR04` is one of the most widely cloned electronic modules in the
    hobby and educational market. Numerous manufacturers and sellers offer
    modules under this name with materially different behaviour — and the
    documentation is frequently a translation of a Chinese datasheet of unclear
    provenance.

    **This documentation set therefore does not cite an HC-SR04 datasheet, and
    does not assert any range, beam angle, accuracy or supply specification for
    it.** Inventing a plausible-looking datasheet link here would be worse than
    admitting the gap.

    What *is* stated is firmware behaviour: the trigger pulse width, the echo
    timeout, the speed-of-sound constant used, and the per-node maximum distance
    those timeouts imply. Those come from the source and are verifiable.

    To document this part properly, obtain the datasheet for the **specific
    module fitted** from its actual supplier, and record which supplier that is.

### DS18B20 — 1-Wire water temperature sensor

| Aspect | Value |
|---|---|
| Role in CIRQUA | Water temperature on Node 2; submerged effluent temperature on Node 4, which also serves as the temperature-compensation input for pH and conductivity |
| Node(s) | 2, 4, 4 SMTP |
| GPIO | 1-Wire bus: N2 `4` · N4 `27` |
| Named in source | `Node2/Node2.ino` line 12 (`PIN_DS18B20`); `Node4/Node4.ino` line 18 (`PIN_SUB_DS18B20`); `Node4_SMTP/Node4_SMTP.ino` line 32. Driven through `OneWire` + `DallasTemperature` |
| Commit | `db6d9b8` |
| Firmware behaviour | Node 2: 12-bit, non-blocking conversion. Node 4: 10-bit (0.25 °C), **blocking** conversion, with the source comment stating ≈187.5 ms is acceptable at 1 Hz. Both reject `DEVICE_DISCONNECTED_C` and gate to −55…125 °C |
| Manufacturer documentation | [Maxim Integrated / Analog Devices — DS18B20](https://www.analog.com/en/products/ds18b20.html) |

This is the one analogue-equivalent part here with an unambiguous, long-standing
manufacturer. Confidence in the URL is high. Note that DallasTemperature is a
third-party driver, not the manufacturer's software.

### DHT11 — ambient temperature and relative humidity sensor

| Aspect | Value |
|---|---|
| Role in CIRQUA | Enclosure ambient temperature and humidity. Drives Node 1's `STATUS:` string and, on the SMTP variant, the fault-alert thresholds |
| Node(s) | 2, 4, 4 SMTP |
| GPIO | N2 `27` · N4 `5` |
| Named in source | `Node2/Node2.ino` lines 16 and 22 (`PIN_DHT11`, `#define DHTTYPE DHT11`); `Node4/Node4.ino` lines 19 and 29; `Node4_SMTP/Node4_SMTP.ino` lines 33 and 43 |
| Commit | `db6d9b8` |
| Firmware behaviour | Read at most every 2000 ms. Node 2 gates on `!isnan()` only; Node 4 additionally gates −20…80 °C and 0…100 %; the SMTP variant reverts to the `!isnan()` gate |
| Manufacturer documentation | [Aosong — DHT11](https://www.aosong.com/en/product-40.html) |

Aosong (Guangzhou Aosong Electronic Technology) is the identified manufacturer of
the DHT11 family. Confidence in the URL is reasonable but not absolute; verify it
before citing in a controlled document.

### ESP32 — microcontroller

| Aspect | Value |
|---|---|
| Role in CIRQUA | The controller on every node; runs the FreeRTOS task set, the UART links and the LCD |
| Node(s) | All |
| Named in source | Referenced throughout all five sketches — dual-core task pinning, `HardwareSerial` UART1/UART2, ADC1/ADC2 channels, `Preferences` NVS, and the Wi-Fi radio on the SMTP variant |
| Commit | `db6d9b8` |
| Firmware constants | GPIO 12/13/14 as ADC2 channels; `analogReadResolution(12)`; `ADC_11db` attenuation; `Serial.begin(115200)`; `INTERNODE_BAUD 9600` |
| Manufacturer documentation | [Espressif — ESP32](https://www.espressif.com/en/products/socs/esp32) |

> **Not verified from the current source.** The exact module and devkit are
> **Not verified from the current source.** The GPIO map uses GPIO 32–35, which
> implies a WROM-class module on a break-out board with the usual pin count, but
> no board is named in the repository and no board is asserted here.

#### Board reference — general only

[Espressif — ESP32-DevKitC user guide](https://docs.espressif.com/projects/esp-devkits/en/latest/esp32/esp32-devkitc/user_guide.html)
is the closest generic reference for the pin set the firmware uses. It is cited
as **general platform documentation only**. It is not evidence that an
ESP32-DevKitC is what is fitted, and it must not be read as such.

### LiquidCrystal_I2C — 16×4 character LCD

| Aspect | Value |
|---|---|
| Role in CIRQUA | Local display on Nodes 1 and 4 (and the SMTP variant) |
| Node(s) | 1, 4, 4 SMTP |
| GPIO | I²C: SDA `21`, SCL `22`; backpack address `0x27`, 16×4 |
| Named in source | `Node1/Node1.ino` lines 3, 17–18, 65; `Node4/Node4.ino` lines 4, 26–27, 77; `Node4_SMTP.ino` lines 3, 40–41, 66 |
| Commit | `db6d9b8` |
| Library documentation | [johnrickman — LiquidCrystal_I2C](https://github.com/johnrickman/LiquidCrystal_I2C) |

Node 4 addresses rows with `lcdN4.command(0x80 | addr)` over DDRAM addresses
`0x00, 0x40, 0x10, 0x50`, which is standard HD44780 row addressing for this
controller. No library version is pinned in the repository.

### OneWire — 1-Wire bus driver

| Aspect | Value |
|---|---|
| Role in CIRQUA | Bus driver for the DS18B20 probes |
| Node(s) | 2, 4, 4 SMTP |
| GPIO | As per the DS18B20 rows above |
| Named in source | `Node2/Node2.ino` line 2 and line 38; `Node4/Node4.ino` line 5 and line 72; `Node4_SMTP.ino` line 5 and line 63 |
| Commit | `db6d9b8` |
| Library documentation | [PaulStoffregen — OneWire](https://github.com/PaulStoffregen/OneWire) |

### DallasTemperature — DS18B20 driver

| Aspect | Value |
|---|---|
| Role in CIRQUA | Converts 1-Wire scratchpad data into temperatures, and controls conversion blocking and resolution |
| Node(s) | 2, 4, 4 SMTP |
| Named in source | `Node2/Node2.ino` line 3 and line 39; `Node4/Node4.ino` line 6 and line 73; `Node4_SMTP.ino` line 6 and line 64 |
| Commit | `db6d9b8` |
| Library documentation | [milesburton — DallasTemperature](https://github.com/milesburton/DallasTemperature) |

Used directly for `setResolution`, `setWaitForConversion`, `requestTemperatures`,
`getTempCByIndex` and `getDeviceCount` — the calls that produce the two
documented behavioural differences between Nodes 2 and 4.

### DHT sensor library — DHT11 driver

| Aspect | Value |
|---|---|
| Role in CIRQUA | Reads ambient temperature and humidity from the DHT11 |
| Node(s) | 2, 4, 4 SMTP |
| GPIO | N2 `27` · N4 `5` |
| Named in source | `Node2/Node2.ino` line 4 and line 40; `Node4/Node4.ino` line 7 and line 75; `Node4_SMTP.ino` line 7 and line 65 |
| Commit | `db6d9b8` |
| Library documentation | [mburton — DHT-sensor-library](https://github.com/mburton/DHT-sensor-library) |

The library returns `NaN` on a checksum failure, which is exactly why both nodes'
gating logic tests `!isnan()` before accepting a value. The DHT11's slow
conversion is the reason for the firmware's 2000 ms pacing gate.

### ESP_Mail_Client — SMTP client

| Aspect | Value |
|---|---|
| Role in CIRQUA | Sends the startup, heartbeat and fault e-mails on the SMTP variant |
| Node(s) | 4 SMTP only |
| GPIO | none — network only |
| Named in source | `Node4_SMTP/Node4_SMTP.ino` line 9; used via `SMPSession smtp` (line 85) and `sendMailMessage` (lines 138–171) |
| Commit | `db6d9b8` |
| Library documentation | [mobivex — Mail-Client-ESP32](https://github.com/mobivex/Mail-Client-ESP32) |

Configured for implicit TLS on port 465 with base64 HTML and high priority. The
library's error strings are what appear after `[SMTP ERROR]`, so those messages
are third-party text, not firmware-authored.

### Wi-Fi and NVS (ESP32 platform, no separate library)

| Aspect | Value |
|---|---|
| Role in CIRQUA | Network association and time synchronisation on the SMTP variant; non-volatile storage for calibration and e-mail timestamps on Node 4 |
| Node(s) | 4 (NVS), 4 SMTP (Wi-Fi, NTP, NVS) |
| Named in source | `WiFi.h` at `Node4_SMTP.ino` line 8; `Preferences.h` at `Node4.ino` line 8 and `Node4_SMTP.ino` line 7 |
| Commit | `db6d9b8` |
| Platform documentation | [Espressif — Arduino-ESP32 documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/) |

Namespaces used: `node4_cal` and, on the SMTP variant, `email_state`. Neither the
ESP32 core version nor the library versions are pinned in the repository.

## Firmware and tooling documentation

These are not field components, but they are the primary documentation for the
software this project is built from.

| Item | Role | Documentation |
|---|---|---|
| Arduino-ESP32 core | The framework the `.ino` sketches are compiled against; supplies FreeRTOS, `HardwareSerial`, the ADC API and `Preferences` | [docs.espressif.com/projects/arduino-esp32](https://docs.espressif.com/projects/arduino-esp32/en/latest/) |
| FreeRTOS kernel | The scheduler, tasks, mutexes and critical sections behind every node's execution model | [freertos.org — RTOS documentation](https://www.freertos.org/Documentation/RTOS_book.html) |
| Python | The documentation tooling language — snippet extraction, manifest generation, QR generation | [python.org](https://www.python.org/) |
| MkDocs | The static site generator | [mkdocs.org](https://www.mkdocs.org/) |
| Material for MkDocs | The theme, and the `pymdownx.snippets` extension used to embed extracted code | [squidfunk.github.io/mkdocs-material](https://squidfunk.github.io/mkdocs-material/) |
| PyYAML | Reads and writes `sources/firmware-source.yml` and the snippet index | [pyyaml.org](https://pyyaml.org/) |

!!! note "Core version not pinned"
    The Arduino-ESP32 core version used for the deployed nodes is **Not verified
    from the current source**. The documentation repository pins *its own*
    Python toolchain in `requirements.txt`; the firmware repository pins nothing.

## Components NOT identified in the source

The firmware uses four analogue or pulse-based sensing channels whose hardware is
**not named anywhere in the source**. This is recorded honestly rather than
matched to a plausible-looking product.

| Channel | Node(s) | GPIO | What the source says | What it does **not** say |
|---|---|---|---|---|
| Dissolved oxygen | 2 | `34` (ADC1) | `PIN_DO_ANALOG`, with electrical calibration constants `VREF 5000.0f`, `TWO_POINT_VOLTAGE 1000.0f`, `SATURATION_DO_25C 8.26f` | Manufacturer, model, part number, cell type, output type (current or voltage) |
| Flow | 3 | `23`, `INPUT_PULLUP`, FALLING ISR | `PIN_FLOW_SENSOR`, `FLOW_CAL_FACTOR 5.5f` | Manufacturer, model, whether it is a turbine, Hall or magnetic sensor |
| pH | 4, 4 SMTP | `13` (ADC2) | `PIN_PH_ANALOG`, slope/offset model | Manufacturer, model, whether the probe is combined with a BNC amplifier board |
| Conductivity (EC) | 4, 4 SMTP | `12` (ADC2) | `PIN_EC_ANALOG`, K-factor model | Manufacturer, model, cell constant, whether a temperature compensation is built in |
| Turbidity | 4, 4 SMTP | `14` (ADC2) | `PIN_TURB_ANALOG`, and a comment naming **`SEN0189 / DFRobot`** with the SEN0189 voltage-to-NTU relationship | Any confirmation of the exact module fitted |

### On the DFRobot SEN0189 reference

The turbidity block in `Node4.ino` (lines 523–532) carries the comment:

> *"SEN0189 / DFRobot turbidity relationship. IMPORTANT: The original code used
> 5.0 V as the ADC reference. That is incorrect for the ESP32 ADC measurement.
> The voltage here is the actual voltage measured at the ESP32 ADC input."*

The official manufacturer documentation for that part was located during the
2026-10-04 audit and is now recorded with access dates in
[Source Registry](source-registry.md):

| Source | URL |
|---|---|
| DFRobot wiki — SEN0189 specification | `https://wiki.dfrobot.com/sen0189` |
| DFRobot wiki — analogue output example and voltage/NTU reference chart | `https://wiki.dfrobot.com/sen0189/docs/18001` |
| DFRobot product listing | `https://www.dfrobot.com/product-1394.html` |

!!! warning "A catalogue URL trap worth recording"
    DFRobot product URL identifiers are re-used. `product-1385.html` now resolves
    to **SEN0193**, a soil moisture sensor, and must not be cited for SEN0189.
    The correct listing for the turbidity sensor is `product-1394.html`.

Comparing that specification against the firmware produced a substantive finding,
documented in full on the [Turbidity](../sensors/turbidity.md) page: the module
outputs **0–4.5 V** and about **4.1 V in clear water**, while the ESP32 ADC at the
attenuation the firmware selects measures only **150 mV – 3100 mV**. The clear-water
condition therefore falls outside the measurable range and outside the firmware's own
validity window, and the firmware's zero-turbidity branch is unreachable.

Note also that the SMTP variant converts turbidity through an intermediate
`turbVolt5V = turbVolt * (5.0f / 3.3f)` — reintroducing a 5 V-referred quantity
that `Node4`'s comment explicitly rejects. See
[Known Limitations](../validation/known-limitations.md).

## Documentation to obtain

A checklist of what would close the gaps on this page. This is a
**Recommendation**: nothing here has been requested or supplied.

| # | Item | Why it is needed | Priority |
|---|---|---|---|
| 1 | Datasheet for the **specific** HC-SR04 module fitted, from its actual supplier | There is no single authoritative HC-SR04 datasheet; the module determines range and echo amplitude | High |
| 2 | Confirmation of the **echo output voltage** of the fitted HC-SR04 | A 5 V logic echo into a 3.3 V GPIO is an unquantified risk (L13) | High |
| 3 | ESP32 board / devkit part number and its schematic | GPIO availability, strapping-pin handling, ADC routing | High |
| 4 | Power supply, regulator and any battery or solar topology | Current draw, brownout behaviour, whether the node is mains- or solar-powered | High |
| 5 | Manufacturer and model for the dissolved-oxygen module | To document its output type and its own calibration requirements | High |
| 6 | Manufacturer and model for the flow sensor | To relate `FLOW_CAL_FACTOR 5.5f` to the manufacturer's pulse-per-litre figure | Medium |
| 7 | Manufacturer and model for the pH probe and amplifier board | To check the two-point model against the board's own output characteristic | Medium |
| 8 | Manufacturer, model and cell constant for the EC probe | The K-factor of 9.997 has no documented provenance | Medium |
| 9 | ~~Confirmed DFRobot product page for SEN0189~~ | **Closed 2026-10-04** — official wiki and product listing recorded in the source registry | Closed |
| 10 | Measured voltage at the turbidity pin (GPIO 14) in clear and in turbid water | The sensor's 0–4.5 V output conflicts with the ESP32 `ADC_11db` range of 150–3100 mV; until measured the channel is unvalidated | **High** |
| 11 | Arduino-ESP32 core version and library versions used for the deployed nodes | Without these, no binary can be reproduced | Medium |
| 12 | Schematic and wiring diagrams | None exist; wiring is documented only as a GPIO map | Medium |
| 13 | Cable types, lengths, gauges and connector pinouts | Field service and replacement | Low |
| 13 | Enclosure specification, material and mounting heights | Required before any environmental claim can be made | Low |
| 14 | Controller (Arduino Mega) firmware or its field-name expectations | The external contract that the `FLM` name and the packet cleaner protect | Medium |
| 15 | Licence file for the firmware repository | Absent; unclear what reuse is permitted | Low |

## Related

* [GPIO Map](../hardware/gpio-map.md) — the same pins as a wiring reference.
* [Controllers](../hardware/controllers.md) — the ESP32 and the downstream
  controller.
* [Sensors index](../sensors/index.md) — per-sensor pages, each distinguishing
  firmware behaviour from device specification.
* [Standards](standards.md) — and why none is claimed.
* [Source Registry](source-registry.md) — URLs with access dates.
* [Known Limitations](../validation/known-limitations.md) — L12, L13 and L17 in
  full.
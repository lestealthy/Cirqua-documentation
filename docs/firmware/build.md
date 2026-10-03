---
title: Building The Firmware
description: How to compile the five CIRQUA ESP32 sketches in the Arduino IDE, which libraries each needs, and what the repository does not provide.
---

# Building The Firmware

There is no build system in the CIRQUA firmware repository. Every `.ino` sketch
is compiled and flashed individually with the Arduino tooling, and this page
documents that manual process.

!!! warning "No build system exists in the repository"
    The firmware repository contains **no `platformio.ini`, no
    `CMakeLists.txt`, no Makefile, no `arduino-cli.yaml`, no lock file and no CI
    workflow.** There is no reproducible, version-pinned build definition
    anywhere. Two people building this firmware on different days, with
    different Arduino core versions and different library versions, may produce
    different binaries from the same source.

    > **Not verified from the current source.** The Arduino-ESP32 core version
    > used to build the deployed nodes is **Not verified from the current
    > source.** It is not recorded in the repository, in the sketches, or in any
    > manifest.

## What you need

| Requirement | Value | Status |
|---|---|---|
| IDE | Arduino IDE 2.x | <span class="cirqua-badge cirqua-badge--recommended">recommended</span> |
| Alternative | PlatformIO Core (with `platform = espressif32`) | <span class="cirqua-badge cirqua-badge--recommended">recommended alternative</span> |
| Board package | `esp32` by Espressif Systems | required |
| Board selection | **ESP32 Dev Module** | see note below |
| Core version | any installed `esp32` core that provides FreeRTOS | > **Not verified from the current source.** |
| Framework | **Arduino-ESP32** — *not* bare ESP-IDF | required |
| Target per sketch | a **separate** ESP32 board | required |

!!! info "Why the Arduino-ESP32 core and not ESP-IDF"
    The sketches use `xTaskCreatePinnedToCore`, `vTaskDelayUntil`,
    `xSemaphoreCreateMutex`, `portMUX_TYPE`, `portENTER_CRITICAL`,
    `IRAM_ATTR`, `HardwareSerial`, `analogSetPinAttenuation`, `Preferences`
    and `.ino` auto-prototyping. That API surface is provided by the
    Arduino-ESP32 core, which embeds FreeRTOS. A bare ESP-IDF component build
    would not compile these files. The FreeRTOS tasks are *not* something you
    add on top of a plain Arduino sketch for another platform — here they are
    the execution model.

!!! warning "Board variant is not pinned either"
    > **Not verified from the current source.** The exact ESP32 devkit model is
    > **Not verified from the current source.** The GPIO maps use GPIO 32–35,
    > which imply a WROOM-class module with the usual 38-pin break-out, but the
    > documentation does not assert a specific board. Select the board that
    > matches the module actually fitted; `ESP32 Dev Module` is the generic
    > Arduino IDE choice that matches the required GPIO set.

## Libraries required per sketch

Read directly from the `#include` lines at commit `db6d9b8`. Each sketch is
independent: **libraries required by one node are not needed to build another
node.**

| Sketch | `#include` lines beyond `Arduino.h` | Libraries to install |
|---|---|---|
| `Node1.ino` | `Wire.h`, `LiquidCrystal_I2C.h` | Wire (bundled with the core), LiquidCrystal I²C |
| `Node2.ino` | `OneWire.h`, `DallasTemperature.h`, `DHT.h` | OneWire, DallasTemperature, DHT sensor library |
| `Node3.ino` | *none* | none — this sketch needs **no** external library |
| `Node4.ino` | `Wire.h`, `LiquidCrystal_I2C.h`, `OneWire.h`, `DallasTemperature.h`, `DHT.h`, `Preferences.h` | Wire (bundled), LiquidCrystal I²C, OneWire, DallasTemperature, DHT sensor library, ESP32 Preferences (bundled with the core) |
| `Node4_SMTP.ino` | `Node4.ino`'s set plus `WiFi.h`, `ESP_Mail_Client.h` | Wire (bundled), LiquidCrystal I²C, OneWire, DallasTemperature, DHT sensor library, Preferences (bundled), **ESP Mail Client** |

Library sources, where the firmware does not itself specify a version:

| Library | Canonical repository | Note |
|---|---|---|
| LiquidCrystal I²C | `github.com/johnrickman/LiquidCrystal_I2C` | HD44780 backpack at address `0x27`, 16×4 |
| OneWire | `github.com/PaulStoffregen/OneWire` | |
| DallasTemperature | `github.com/milesburton/DallasTemperature` | depends on OneWire |
| DHT sensor library | `github.com/mburton/DHT-sensor-library` | `DHTTYPE DHT11` on Nodes 2, 4 and 4 SMTP |
| ESP Mail Client | `github.com/mobivex/Mail-Client-ESP32` | `Node4_SMTP` only; requires mbed TLS |

!!! warning "Library versions are not pinned"
    No `library.properties` reference, no `platformio.ini` `lib_deps` and no
    vendored copy exists in the firmware repository. Install the current
    release of each library and record what you installed alongside the binary
    you flash.

!!! danger "`Node4_SMTP.ino` contains placeholder credentials — handle with care"
    The SMTP configuration block in the committed source is filled with
    placeholders (`YOUR_WIFI_SSID`, `YOUR_WIFI_PASSWORD`,
    `your_sender_email@gmail.com`, `your_email_app_password`,
    `your_recipient_email@gmail.com`). **These are not working values.**

    * Never commit a filled-in version. Keep real credentials out of the
      repository, out of the sketch, and out of any documentation page.
    * Supply real values at build time, from a local, untracked settings header
      or from your build system's secret injection.
    * The documentation snippet for this block is **automatically redacted**:
      the extractor replaces the password macros with
      `<REDACTED - set at build time>`. See
      [Calibration Console](configuration.md)) and
      [Known Limitations](../validation/known-limitations.md).

## Building with the Arduino IDE 2.x — exact steps

These steps are repeated once per node, because **each node is a separate
sketch flashed to its own ESP32.**

1. Open the Arduino IDE.
2. Attach the target ESP32 over USB. If it does not enumerate, hold **BOOT**,
   tap **EN**, release **BOOT** — see [Flashing](flashing.md)) for the full
   procedure and its cautions.
3. Menu **File ▸ Open** the sketch file itself, for example
   `FreeRTOS_Implementation/Node1/Node1.ino`. Opening the `.ino` (not the
   parent folder) makes the IDE create the containing folder as the sketch.
4. Menu **Tools ▸ Board ▸ esp32 ▸ ESP32 Dev Module**. Select the serial port
   your board enumerated on.
5. Menu **Tools ▸ Manage Libraries…**, install the libraries listed for that
   sketch in the table above. The Library Manager searches both the official
   index and the contributed index; if `LiquidCrystal_I2C` offers several
   similarly named entries, confirm it exposes the `LiquidCrystal_I2C` class
   used here and is maintained.
6. Optional but recommended: menu **Tools ▸ PSRAM** and **Tools ▸ Partition
   Scheme** are not used by this firmware; leave the defaults. Menu
   **Tools ▸ Upload Speed** may be lowered to 115200 if the link is unstable.
7. Menu **Sketch ▸ Verify** to compile. Read the warnings — in particular, the
   `String`-heavy Node 1 and Node 4 code, and unused variables such as
   `adcToVoltage`'s `totalMv`.
8. Menu **Sketch ▸ Upload** to flash. First upload after a fresh core install
   may require the BOOT sequence described on the [Flashing](flashing.md))
   page.
9. Open **Tools ▸ Serial Monitor** at **115200 baud** and compare the output
   against the expected first-boot output for that node on the
   [Flashing](flashing.md)) page.
10. Repeat for each remaining node. A cluster is only functional once all four
    (or five) boards carry their own correct sketch.

### Suggested sketch folder layout for local editing

The repository stores sketches in `<node>/<node>.ino` form, which is already a
valid Arduino IDE sketch layout. Copy `FreeRTOS_Implementation/NodeN` out of the
submodule into a writable working directory before editing — the submodule
working tree should stay clean so that the staleness check
(`python scripts/extract_code_snippets.py --check`) remains meaningful.

## Building with PlatformIO

PlatformIO is the recommended alternative because it pins the platform and the
libraries in a project file. It is not what the firmware repository uses, so you
would be **adding** the configuration, not recovering it.

```ini
; Example only - NOT part of the firmware repository.
; Derived from the #include lines and the tasks used by each sketch.
[env:node1]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    johnrickman/LiquidCrystal_I2C

[env:node2]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    milesburton/DallasTemperature@^3.11.0
    mburton/DHT-sensor-library@^1.4.6

[env:node3]
platform = espressif32
board = esp32dev
framework = arduino

[env:node4]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    johnrickman/LiquidCrystal_I2C
    milesburton/DallasTemperature@^3.11.0
    mburton/DHT-sensor-library@^1.4.6

; Node4_SMTP additionally needs:
;   mobivex/Mail-Client-ESP32@^3.x
; Credentials must come from an untracked local header or environment
; injection. Never commit real values.
```

Each environment points `src_dir` at one of the `FreeRTOS_Implementation/*`
directories. Because `Node4` and `Node4_SMTP` share a directory name pattern but
live in different directories, keep them as separate environments.

> **Recommendation, not a description.** The settings above are a starting
> point assembled from the `#include` lines at commit `db6d9b8`. Library version
> ranges have not been validated against a successful build of this source and
> must be confirmed by compiling.

## Compiling the documentation, not the firmware

The documentation repository has its own, *real*, pinned build:

```bash
python -m pip install -r requirements.txt
python scripts/extract_code_snippets.py --check   # snippets not stale
mkdocs build --strict
```

`sources/firmware-source.yml` names the firmware commit the documentation
describes, and `scripts/extract_code_snippets.py` reads the submodule to
regenerate `docs/assets/snippets/`. See [Repository](repository.md)).

## Compile-time constants you will probably change first

Most field adjustments are compile-time. See [Configuration](configuration.md))
for the full table of constants, their files, values and effects.

| Goal | Where |
|---|---|
| Tank geometry for a different tank | `TANK_HEIGHT`, `TANK_RADIUS` in the node sketch |
| Dissolved-oxygen saturation point | `SATURATION_DO_25C` in `Node2.ino` |
| Flow meter pulses per litre | `FLOW_CAL_FACTOR` in `Node3.ino` |
| ADC attenuation for a probe with a narrower output | `SENSOR_ADC_ATTENUATION` in `Node4.ino` |
| ADC averaging depth | `ADC_SAMPLES` in `Node4.ino` |
| pH and conductivity calibration | Runtime via the Node 4 serial console, or defaults in `loadCalibration()` |
| Wi-Fi, SMTP, alerting intervals | `Node4_SMTP.ino` only — and never commit credentials |

## Verification after a build

| Check | Expected |
|---|---|
| `Sketch ▸ Verify` completes | No errors |
| `loop()` compiles to `vTaskDelete(NULL)` | Present in every sketch |
| Expected first-boot serial output | See [Flashing](flashing.md)) |
| Task names in a debugger or `FreeRTOS` task list | See [RTOS Tasks](../rtos/tasks.md)) |
| Frames on the inter-node links | See [Message Format](../communication/message-format.md)) |

## Related

* [Flashing](flashing.md)) — putting the binary on the board.
* [Configuration](configuration.md)) — every constant and the serial console.
* [Repository](repository.md)) — what is and is not in the source tree.
* [Known Limitations](../validation/known-limitations.md) — including the
  absence of tests and CI.
* [Test Strategy](../validation/test-strategy.md)) — a proposed build-verification
  scheme.
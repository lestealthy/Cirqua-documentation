---
title: References
description: Reference hub for the CIRQUA documentation - project sources, manufacturer documentation, standards, literature and the source registry.
---

# References

Every external source used to produce this documentation set, grouped by what it
was used *for*. Each entry records the publisher, the URL, the date it was
consulted and — importantly — its authority level, so that a reader can tell a
primary project claim from a manufacturer specification from an inference.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Project-level claims</span>
    <span class="cirqua-identity__value">CIRQUA official site and African Biotechnology Company site — <strong>primary</strong></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Firmware claims</span>
    <span class="cirqua-identity__value">The pinned firmware repository at <code>db6d9b8</code> — <strong>primary</strong></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Device claims</span>
    <span class="cirqua-identity__value">Manufacturer pages, cited only for parts <strong>named in source</strong></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Standards</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--unknown">none claimed or tested</span></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Machine-readable</span>
    <span class="cirqua-identity__value">[Source Registry](source-registry.md)</span>
  </div>
</div>

## Categories

### Official project sources — primary

Used for every project-level claim: funding, duration, consortium, scope and the
partner organisation's own description of itself.

| Source | Used for |
|---|---|
| [cirqua-water.eu](https://cirqua-water.eu/) | Project identity, full title, Horizon Europe funding, duration, consortium size, thematic focus |
| [The Project](https://cirqua-water.eu/the-project/) | Project objectives, constructed wetlands as the nature-based solution, water recovery and nutrient reuse |
| [Team](https://cirqua-water.eu/team-2/) | Partner composition and the 13-partner / 10-country / 3-continent claim |
| [Work Programme](https://cirqua-water.eu/work-program/) | Work-package structure, the sensor and automation theme, precision irrigation and AI tooling |
| [african-biotech.com](https://www.african-biotech.com/) | African Biotechnology Company: founding year, location, service list, and the fact that it lists CIRQUA among its projects |

Full attribution, extracted facts and re-verification notes:
[Official Project Sources](official-project-sources.md).

### Hardware manufacturer sources

Used only for components whose part name appears in the firmware source. Parts
that the source does not name are recorded as **unidentified** rather than
guessed.

| Source | Used for |
|---|---|
| [Maxim Integrated / Analog Devices — DS18B20](https://www.analog.com/en/products/ds18b20.html) | Identity and nature of the named 1-Wire temperature sensor |
| [Aosong — DHT11](https://www.aosong.com/en/product-40.html) | Identity and nature of the named humidity/temperature sensor |
| [Espressif — ESP32](https://www.espressif.com/en/products/socs/esp32) | Identity of the microcontroller named throughout the firmware |
| [Espressif — Arduino-ESP32 documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/) | The framework the sketches are built on |
| [Espressif — ESP32-DevKitC](https://docs.espressif.com/projects/esp-devkits/en/latest/esp32/esp32-devkitc/user_guide.html) | The devkit family the GPIO maps imply — *general reference, not a verified fit* |
| [Arduino — LiquidCrystal I2C](https://github.com/johnrickman/LiquidCrystal_I2C) | The LCD library the sketches include |
| [Paul Stoffregen — OneWire](https://github.com/PaulStoffregen/OneWire) | The 1-Wire library the sketches include |
| [Miles Burton — DallasTemperature](https://github.com/milesburton/DallasTemperature) | The DS18B20 driver the sketches include |
| [Miles Burton — DHT sensor library](https://github.com/mburton/DHT-sensor-library) | The DHT driver the sketches include |
| [Mobivex — ESP Mail Client](https://github.com/mobivex/Mail-Client-ESP32) | The SMTP library `Node4_SMTP.ino` includes |
| [FreeRTOS kernel documentation](https://www.freertos.org/Documentation/RTOS_book.html) | Task creation, pinning, priorities and the scheduling model the firmware uses |
| [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) | The documentation toolchain, and the `pymdownx.snippets` mechanism the code embedding relies on |

Item-by-item detail, including the **no-authoritative-datasheet** position on
HC-SR04: [Datasheets](datasheets.md).

### Software and RTOS sources

The firmware's own execution model is documented by the RTOS it runs on, not by
a project document.

| Source | Used for |
|---|---|
| [FreeRTOS kernel documentation](https://www.freertos.org/Documentation/RTOS_book.html) | `xTaskCreatePinnedToCore` semantics, stack-depth units, priority ranges, `vTaskDelayUntil` periodic release, mutex semantics, `portMUX_TYPE` critical sections |
| [Espressif ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/) | General ESP32 hardware behaviour: strapping pins, ADC characteristics, `analogReadMilliVolts`, NVS/`Preferences` behaviour |
| [Arduino language reference](https://docs.arduino.cc/language-reference/) | `String`, `pulseIn`, `snprintf` semantics used throughout the sketches |

### Scientific literature

Used only for background framing of the measurement principles — never for a
number quoted on a sensor page.

| Source | Used for |
|---|---|
| Vymazal's constructed-wetland reviews | Context for the treatment performance of horizontal flow constructed wetlands |
| Kadlec and Wallace's treatment wetland work | The conceptual basis for wetland-based treatment, the subject area of the project |
| Reference texts on constructed wetlands for water reuse | The project context that a monitoring system like this serves |
| Reference texts on oxygen solubility and temperature compensation | Why dissolved-oxygen readings need temperature compensation at all |

Because these are cited from knowledge rather than from a consulted catalogue in
this build, each is presented with the caution it needs. See
[Scientific Literature](scientific-literature.md) — every entry there carries an
explicit instruction to verify its identifier before publication.

### Standards

**No standard compliance is claimed, implemented or tested anywhere in this
firmware.** The list on [Standards](standards.md)) is of standards that are
*relevant to the project's subject matter* or *referenced by the tooling*, and
it says so explicitly. Nothing in the firmware source contains
standards-conformance logic.

### Source registry

[Source Registry](source-registry.md) is the machine-readable companion to
this page: every external source as a YAML record with `id`, `title`,
`publisher`, `source_type`, `url`, `accessed`, `used_for`, `authority` and
`notes`, in a form that can be diffed and checked.

## How sources are treated in this documentation

| Claim type | What may be cited | Never acceptable |
|---|---|---|
| Project fact | The official CIRQUA or ABC site, dated | A press release, a conference slide or a third-party summary |
| Firmware implementation | The pinned commit, with file, symbol and line range | A paraphrase presented as a quotation |
| Manufacturer specification | The manufacturer's own page or datasheet, for a named part | A distributor listing, a forum post or a datasheet for a *similar* part |
| Engineering interpretation | Labelled as such, with the reasoning shown | Presented as if the firmware stated it |
| Recommendation | Labelled as such | Presented as existing practice |

!!! warning "Manufacturer and part identity is deliberately incomplete"
    Only `HC-SR04`, `DS18B20` and `DHT11` are named as parts in the firmware.
    The dissolved-oxygen, flow, pH and conductivity modules have **no manufacturer
    or part number in the source**, with one exception noted in the comments
    (`SEN0189 / DFRobot` for turbidity). Those are recorded as unidentified on
    [Datasheets](datasheets.md) rather than matched to a plausible product. The
    documentation also does not assert an authoritative HC-SR04 datasheet,
    because the part is widely cloned and has no single authoritative
    manufacturer.

## Related

* [Official Project Sources](official-project-sources.md)
* [Datasheets](datasheets.md)
* [Standards](standards.md)
* [Scientific Literature](scientific-literature.md)
* [Source Registry](source-registry.md)
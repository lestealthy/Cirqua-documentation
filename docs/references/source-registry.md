---
title: Source Registry
description: Machine-readable registry of every external source used in the CIRQUA documentation, with publisher, type, URL, access date, use and authority level.
---

# Source Registry

The machine-readable companion to the [References index](index.md). Every
external source behind this documentation set is listed here with its
publisher, type, URL, the date it was consulted, what it was used for, and its
authority level.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Records</span>
    <span class="cirqua-identity__value">Project · manufacturer · library · RTOS · tooling · literature · standards</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Access date for web sources</span>
    <span class="cirqua-identity__value">2026-10-03</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Highest authority present</span>
    <span class="cirqua-identity__value"><strong>primary</strong> — official project sites and the pinned firmware source</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Firmware source pin</span>
    <span class="cirqua-identity__value"><code>db6d9b896341a9c7d8fd01913e854b663c110d55</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Companion manifest</span>
    <span class="cirqua-identity__value"><code>sources/firmware-source.yml</code></span>
  </div>
</div>

## Authority levels

| Level | Meaning |
|---|---|
| `primary` | The organisation's own publication, or the source code itself. Everything project-level and firmware-level rests here |
| `manufacturer` | The manufacturer's own product or documentation page |
| `primary-literature` | Peer-reviewed work by the field's established authors |
| `secondary` | Useful context, but not a basis for a claim |
| `tooling` | Documentation of the toolchain, with no bearing on the firmware's behaviour |

## Registry

```yaml
# ===========================================================================
# CIRQUA documentation — external source registry
#
# Companion to docs/references/source-registry.md.
#
# Fields per record:
#   id          stable identifier used by pages that cite the source
#   title       the source's own title
#   publisher   who publishes it
#   source_type project | manufacturer | library | rtos | tooling | literature | standard
#   url         canonical URL, or the pinned commit for the firmware
#   accessed    ISO date of consultation (web sources)
#   used_for    what it is cited for in this documentation set
#   authority   primary | manufacturer | primary-literature | secondary | tooling
#   notes       caveats, verification status, and what is NOT claimed
#
# Rules encoded in this file:
#   * No record asserts standards conformance by the firmware.
#   * No record supplies a device specification for a part the firmware
#     does not name.
#   * No record contains a credential, token or real network identifier.
# ===========================================================================

sources:

  # -------------------------------------------------------------------------
  # Firmware source — the primary basis for every implementation claim
  # -------------------------------------------------------------------------
  - id: fw-cirqua
    title: "Cirqua firmware with FreeRTOS implementation"
    publisher: "WattLab (GitHub: lestealthy)"
    source_type: repository
    url: "https://github.com/lestealthy/Cirqua"
    accessed: "2026-10-03"
    used_for: >-
      Every firmware-implementation claim in this documentation set: pin map,
      task table, frame formats, conversion formulas, calibration constants,
      boot output, library dependencies, and all 41 embedded code snippets.
    authority: primary
    notes: >-
      Pinned to branch main at commit
      db6d9b896341a9c7d8fd01913e854b663c110d55 (db6d9b8), consumed as a Git
      submodule at _external/Cirqua-firmware and recorded in
      sources/firmware-source.yml. Single commit; 11 files; 6953 insertions.
      No README, licence, build system, tests, CI, schematic or photograph
      exists in it. That deployed nodes run this commit is NOT verified.

  - id: fw-cirqua-tree
    title: "Cirqua firmware repository tree at commit db6d9b8"
    publisher: "WattLab (GitHub: lestealthy)"
    source_type: repository
    url: "https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55"
    accessed: "2026-10-03"
    used_for: >-
      Directory layout, the FreeRTOS_Implementation versus _OLD split, and
      every permalink used in the Source Map and Code Reference.
    authority: primary
    notes: >-
      FreeRTOS_Implementation/ is CURRENT. _OLD/ is HISTORICAL and is never
      described as the current architecture.

  # -------------------------------------------------------------------------
  # Official project sources — primary, and time-varying
  # -------------------------------------------------------------------------
  - id: cirqua-home
    title: "CIRQUA — Waterwise Futures"
    publisher: "CIRQUA project"
    source_type: project
    url: "https://cirqua-water.eu/"
    accessed: "2026-10-03"
    used_for: >-
      Project full name, Horizon Europe funding of 4.09 million EUR, 36-month
      duration, and the thematic scope (constructed wetlands, nanostructured
      filters, photocatalytic modules, N2-fixing legumes, sensors and
      automation, precision irrigation, AI tooling).
    authority: primary
    notes: >-
      Re-verify before publication; project facts change. No claim is made that
      this firmware is a CIRQUA deliverable or that any node is deployed for the
      project.

  - id: cirqua-the-project
    title: "The Project"
    publisher: "CIRQUA project"
    source_type: project
    url: "https://cirqua-water.eu/the-project/"
    accessed: "2026-10-03"
    used_for: >-
      Objectives, the nature-based-solution framing of constructed wetlands,
      the rural and Mediterranean focus, and the stated outcomes concerning
      reuse of treated water and wetland biomass.
    authority: primary
    notes: >-
      Timeline of April 2024 kick-off to March 2027 is taken from this page.
      Do not extrapolate beyond the page's own statements.

  - id: cirqua-team
    title: "Team"
    publisher: "CIRQUA project"
    source_type: project
    url: "https://cirqua-water.eu/team-2/"
    accessed: "2026-10-03"
    used_for: >-
      Consortium composition: 13 partners, 10 countries, 3 continents.
    authority: primary
    notes: >-
      No partner-specific role is attributed beyond what the page states. No
      claim is made about which partner built which node.

  - id: cirqua-work-programme
    title: "Work Programme"
    publisher: "CIRQUA project"
    source_type: project
    url: "https://cirqua-water.eu/work-program/"
    accessed: "2026-10-03"
    used_for: >-
      Work-package structure and the sensors-and-automation theme that a
      distributed monitoring cluster supports.
    authority: primary
    notes: >-
      This firmware is not presented as a project deliverable.

  - id: abc-home
    title: "African Biotechnology Company"
    publisher: "African Biotechnology Company"
    source_type: project
    url: "https://www.african-biotech.com/"
    accessed: "2026-10-03"
    used_for: >-
      Founding in 2017, based in Tunis, Tunisia; the listed consulting services
      (scientific-project consulting, wastewater treatment plant maintenance,
      3D printing and product development, molecular biology services); the
      stated specialisation in smart irrigation and wastewater reuse; and the
      public listing of CIRQUA among the company's projects.
    authority: primary
    notes: >-
      No CIRQUA role is attributed to ABC beyond the fact that it lists the
      project. No staffing, certification or registration detail is claimed.

  # -------------------------------------------------------------------------
  # Manufacturer documentation — only for parts named in the firmware
  # -------------------------------------------------------------------------
  - id: mfg-esp32
    title: "ESP32"
    publisher: "Espressif Systems"
    source_type: manufacturer
    url: "https://www.espressif.com/en/products/socs/esp32"
    accessed: "2026-10-03"
    used_for: "Identity of the microcontroller named throughout all five sketches."
    authority: manufacturer
    notes: >-
      The specific module and devkit are NOT verified from the current source;
      the documentation set asserts no board variant.

  - id: mfg-esp32-devkitc
    title: "ESP32-DevKitC User Guide"
    publisher: "Espressif Systems"
    source_type: manufacturer
    url: "https://docs.espressif.com/projects/esp-devkits/en/latest/esp32/esp32-devkitc/user_guide.html"
    accessed: "2026-10-03"
    used_for: >-
      General platform reference for the GPIO set and strapping pins the
      firmware uses.
    authority: manufacturer
    notes: >-
      Cited as general documentation ONLY. It is not evidence that a
      ESP32-DevKitC is the board fitted.

  - id: mfg-arduino-esp32
    title: "Arduino-ESP32 core documentation"
    publisher: "Espressif Systems"
    source_type: manufacturer
    url: "https://docs.espressif.com/projects/arduino-esp32/en/latest/"
    accessed: "2026-10-03"
    used_for: >-
      The framework the .ino sketches are compiled against: FreeRTOS, HardwareSerial
      UART1/UART2, the ADC API including analogReadMilliVolts and attenuation,
      and the Preferences NVS API.
    authority: manufacturer
    notes: >-
      Core version used for the deployed nodes is NOT verified from the current
      source. The firmware repository pins nothing.

  - id: mfg-ds18b20
    title: "DS18B20 — Programmable Resolution 1-Wire Digital Temperature Sensor"
    publisher: "Maxim Integrated (now Analog Devices)"
    source_type: manufacturer
    url: "https://www.analog.com/en/products/ds18b20.html"
    accessed: "2026-10-03"
    used_for: "Identity and nature of the 1-Wire temperature sensor named in the firmware."
    authority: manufacturer
    notes: >-
      Confidence in this URL is high. DallasTemperature is a third-party driver,
      not manufacturer software. No device specification from this datasheet is
      quoted anywhere in this documentation set.

  - id: mfg-dht11
    title: "DHT11 — Digital Humidity and Temperature Sensor"
    publisher: "Aosong Electronic Technology"
    source_type: manufacturer
    url: "https://www.aosong.com/en/product-40.html"
    accessed: "2026-10-03"
    used_for: "Identity and nature of the ambient humidity and temperature sensor named in the firmware."
    authority: manufacturer
    notes: >-
      Verify the URL before citing in a controlled document. No accuracy figure
      from this page is quoted in this documentation set.

  - id: mfg-hc-sr04
    title: "HC-SR04 — ultrasonic distance sensor"
    publisher: "unidentified"
    source_type: manufacturer
    url: ""
    accessed: ""
    used_for: "Identity of the ultrasonic module named in the firmware source."
    authority: secondary
    notes: >-
      NO AUTHORITATIVE DATASHEET IS CITED, DELIBERATELY. The part name is widely
      cloned across numerous manufacturers with materially different behaviour,
      so there is no single authoritative datasheet to point at. Range, beam
      angle, accuracy and echo amplitude are NOT asserted anywhere in this
      documentation set. The exact module fitted is NOT verified from the
      current source. Obtaining the supplier's datasheet for the fitted part is
      an open action on the Datasheets page.

  - id: mfg-dfrobot-sen0189
    title: "SEN0189 — analog turbidity sensor (DFRobot / Gravity series)"
    publisher: "DFRobot"
    source_type: manufacturer
    url: ""
    accessed: ""
    used_for: >-
      The voltage-to-NTU relationship named in a source comment in Node4.ino
      lines 523-532.
    authority: secondary
    notes: >-
      THE EXACT PRODUCT PAGE URL IS DELIBERATELY NOT GIVEN. A catalogue URL was
      not verified during this build, and an unverified link in a reference
      section is worse than an acknowledged gap. Locate it in the manufacturer's
      own catalogue, then record the URL and access date here. Note that
      Node4_SMTP converts turbidity through an intermediate 5 V-referred voltage,
      reintroducing the assumption that Node4's comments reject.

  # -------------------------------------------------------------------------
  # Components NOT identified in the firmware source
  # -------------------------------------------------------------------------
  - id: unidentified-do
    title: "Dissolved oxygen sensing module"
    publisher: "unidentified"
    source_type: manufacturer
    url: ""
    accessed: ""
    used_for: "Documenting the gap for GPIO 34 on Node 2."
    authority: secondary
    notes: >-
      No manufacturer, model or part number appears in the firmware. Output type
      (current or voltage), cell type and calibration requirements are unknown.

  - id: unidentified-flow
    title: "Inline flow sensor"
    publisher: "unidentified"
    source_type: manufacturer
    url: ""
    accessed: ""
    used_for: "Documenting the gap for GPIO 23 on Node 3."
    authority: secondary
    notes: >-
      No manufacturer or model appears in the firmware. Whether it is a turbine,
      Hall or magnetic sensor is unknown, so the provenance of the pulses-per-litre
      constant 5.5 cannot be checked against a manufacturer figure.

  - id: unidentified-ph
    title: "pH probe module"
    publisher: "unidentified"
    source_type: manufacturer
    url: ""
    accessed: ""
    used_for: "Documenting the gap for GPIO 13 on Node 4."
    authority: secondary
    notes: >-
      No manufacturer or model appears in the firmware. Whether the probe is
      combined with an amplifier board is unknown, so the two-point slope/offset
      model cannot be checked against the board's own characteristic.

  - id: unidentified-ec
    title: "Electrical conductivity probe module"
    publisher: "unidentified"
    source_type: manufacturer
    url: ""
    accessed: ""
    used_for: "Documenting the gap for GPIO 12 on Node 4."
    authority: secondary
    notes: >-
      No manufacturer, model or cell constant appears in the firmware. The
      default K-factor 9.997 has no documented provenance and is a field
      calibration constant that must be established per installation.

  # -------------------------------------------------------------------------
  # Libraries — the canonical repositories, not pinned versions
  # -------------------------------------------------------------------------
  - id: lib-liquidcrystal-i2c
    title: "LiquidCrystal_I2C"
    publisher: "johnrickman (GitHub)"
    source_type: library
    url: "https://github.com/johnrickman/LiquidCrystal_I2C"
    accessed: "2026-10-03"
    used_for: "The 16x4 HD44780 I2C display driver included by Nodes 1, 4 and Node4_SMTP at address 0x27."
    authority: manufacturer
    notes: >-
      Library version NOT pinned in the firmware repository. Several similarly
      named libraries exist in the Arduino Library Manager.

  - id: lib-onewire
    title: "OneWire"
    publisher: "Paul Stoffregen (GitHub)"
    source_type: library
    url: "https://github.com/PaulStoffregen/OneWire"
    accessed: "2026-10-03"
    used_for: "The 1-Wire bus driver included by Nodes 2, 4 and Node4_SMTP."
    authority: manufacturer
    notes: "Library version NOT pinned in the firmware repository."

  - id: lib-dallas-temperature
    title: "DallasTemperature"
    publisher: "Miles Burton (GitHub)"
    source_type: library
    url: "https://github.com/milesburton/DallasTemperature"
    accessed: "2026-10-03"
    used_for: >-
      The DS18B20 driver. Supplies the API calls behind the documented difference
      between Node 2 (non-blocking conversion) and Node 4 (10-bit blocking
      conversion).
    authority: manufacturer
    notes: "Library version NOT pinned in the firmware repository."

  - id: lib-dht
    title: "DHT sensor library"
    publisher: "Miles Burton (GitHub)"
    source_type: library
    url: "https://github.com/mburton/DHT-sensor-library"
    accessed: "2026-10-03"
    used_for: >-
      The DHT11 driver. Its NaN return on checksum failure is why both nodes gate
      on !isnan(); the DHT11's slow conversion is why the firmware paces reads
      to at least 2000 ms.
    authority: manufacturer
    notes: "Library version NOT pinned in the firmware repository."

  - id: lib-esp-mail-client
    title: "Mail Client ESP32"
    publisher: "Mobivex (GitHub)"
    source_type: library
    url: "https://github.com/mobivex/Mail-Client-ESP32"
    accessed: "2026-10-03"
    used_for: >-
      SMTP dispatch for the Node4_SMTP variant: implicit TLS on port 465,
      base64 HTML, high priority. Its error strings are the text that follows
      [SMTP ERROR] on the serial monitor.
    authority: manufacturer
    notes: >-
      Library version NOT pinned. Requires mbed TLS. The committed configuration
      in the sketch is PLACEHOLDER text; no working credential appears in this
      documentation set and none must ever be committed.

  # -------------------------------------------------------------------------
  # RTOS and framework documentation
  # -------------------------------------------------------------------------
  - id: rtos-freertos
    title: "FreeRTOS kernel documentation"
    publisher: "FreeRTOS.org"
    source_type: rtos
    url: "https://www.freertos.org/Documentation/RTOS_book.html"
    accessed: "2026-10-03"
    used_for: >-
      Semantics behind every node's execution model: xTaskCreatePinnedToCore,
      stack depth units, priority ranges, vTaskDelayUntil periodic release,
      mutex semantics, and portMUX_TYPE critical sections.
    authority: manufacturer
    notes: >-
      The kernel is supplied by the Arduino-ESP32 core, not linked directly.
      The FreeRTOS version in use is NOT verified from the current source.

  - id: rtos-esp-idf
    title: "ESP-IDF Programming Guide"
    publisher: "Espressif Systems"
    source_type: rtos
    url: "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/"
    accessed: "2026-10-03"
    used_for: >-
      General ESP32 hardware behaviour referenced by the flashing page: strapping
      pins (GPIO 0, 2, 5, 12, 15), ADC characteristics and channel groups, and
      NVS behaviour.
    authority: manufacturer
    notes: >-
      Cited as general platform knowledge. The strapping-pin cautions on the
      flashing page are labelled as such and are NOT findings from the CIRQUA
      source.

  - id: lang-arduino
    title: "Arduino Language Reference"
    publisher: "Arduino"
    source_type: tooling
    url: "https://docs.arduino.cc/language-reference/"
    accessed: "2026-10-03"
    used_for: "Semantics of String, pulseIn and snprintf as used throughout the sketches."
    authority: manufacturer
    notes: "Framework documentation only; no bearing on node behaviour."

  # -------------------------------------------------------------------------
  # Documentation tooling
  # -------------------------------------------------------------------------
  - id: tool-python
    title: "Python"
    publisher: "Python Software Foundation"
    source_type: tooling
    url: "https://www.python.org/"
    accessed: "2026-10-03"
    used_for: >-
      Language of scripts/extract_code_snippets.py, which mechanically extracts
      all 41 code snippets and generates the snippet index. Also the language of
      the manifest and validation tooling.
    authority: tooling
    notes: "Documentation tooling only."

  - id: tool-mkdocs
    title: "MkDocs"
    publisher: "MkDocs"
    source_type: tooling
    url: "https://www.mkdocs.org/"
    accessed: "2026-10-03"
    used_for: "The static site generator for this documentation set."
    authority: tooling
    notes: "Documentation tooling only."

  - id: tool-mkdocs-material
    title: "Material for MkDocs"
    publisher: "squidfunk (GitHub)"
    source_type: tooling
    url: "https://squidfunk.github.io/mkdocs-material/"
    accessed: "2026-10-03"
    used_for: >-
      The theme, and the pymdownx.snippets extension that embeds the extracted
      firmware snippets into pages.
    authority: tooling
    notes: "Documentation tooling only."

  - id: tool-pyyaml
    title: "PyYAML"
    publisher: "PyYAML"
    source_type: tooling
    url: "https://pyyaml.org/"
    accessed: "2026-10-03"
    used_for: "Reads and writes sources/firmware-source.yml and docs/assets/snippets/snippet-index.yml."
    authority: tooling
    notes: "Documentation tooling only. Version pinned in requirements.txt."

  # -------------------------------------------------------------------------
  # Scientific literature — background framing only
  #
  # IDENTIFIERS ARE DELIBERATELY ABSENT. These are long-established works cited
  # from knowledge, not from a catalogue lookup performed in this build. Each
  # must be verified against a publisher record before publication. No DOI,
  # volume or page range is asserted anywhere.
  # -------------------------------------------------------------------------
  - id: lit-treatment-wetlands
    title: "Work on treatment wetlands"
    publisher: "peer-reviewed literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Conceptual basis for constructed wetlands as a deliberate treatment
      technology, which is the reason the project's interest in them is
      technical rather than merely ecological.
    authority: primary-literature
    notes: >-
      Authors R. Kadlec and W. Wallace. IDENTIFIER TO BE VERIFIED. No DOI,
      volume or page range is asserted. No performance figure from this work is
      quoted anywhere in this documentation set.

  - id: lit-constructed-wetland-reviews
    title: "Review literature on constructed wetlands for wastewater treatment"
    publisher: "peer-reviewed literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Performance context for horizontal- and vertical-flow treatment wetlands,
      which explains why a range of effluent parameters is monitored routinely.
    authority: primary-literature
    notes: >-
      Author J. Vymazal. IDENTIFIER TO BE VERIFIED. No DOI, volume or page range
      is asserted. No literature range is quoted as a specification for this
      installation.

  - id: lit-oxygen-solubility
    title: "Solubility of oxygen in water and its temperature dependence"
    publisher: "peer-reviewed and reference literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Explains why dissolved-oxygen readings and probe output require temperature
      compensation, which is the reason the firmware's compensation terms exist.
    authority: primary-literature
    notes: >-
      IDENTIFIER TO BE VERIFIED. This justifies the EXISTENCE of the
      compensation term; it does NOT justify the firmware's coefficient of
      -0.02 per degree Celsius or its 8.26 mg/L saturation constant, which are
      unvalidated firmware values.

  - id: lit-conductivity-temperature
    title: "Electrical conductivity as a measure of dissolved ions, and its temperature dependence"
    publisher: "peer-reviewed and reference literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Justifies normalising conductivity to a reference temperature and stating
      the unit on every reported value.
    authority: primary-literature
    notes: >-
      IDENTIFIER TO BE VERIFIED. Does NOT justify the firmware's K-factor of
      9.997, which is a field calibration constant with no documented
      provenance.

  - id: lit-ph-nernst
    title: "Glass electrode potential and the Nernst equation"
    publisher: "peer-reviewed and reference literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Explains why pH temperature compensation exists and why two-point
      calibration is normal practice for a field probe.
    authority: primary-literature
    notes: >-
      IDENTIFIER TO BE VERIFIED. Does NOT justify the firmware's affine
      slope-times-voltage-plus-offset model, which is recorded as a deliberate
      legacy-preserved choice and is documented as a limitation.

  - id: lit-biological-nitrogen-fixation
    title: "Biological nitrogen fixation by nitrogen-fixing organisms, including crop legumes"
    publisher: "peer-reviewed literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Notes only that biological nitrogen fixation is the basis of legume-based
      approaches and that N2-fixing legume cultivation is a named project theme.
    authority: primary-literature
    notes: >-
      IDENTIFIER TO BE VERIFIED. The project-level claim is sourced to the
      CIRQUA site, not to literature. IMPORTANT BOUNDARY: this firmware
      measures nothing about nitrogen fixation — there is no nitrogen, nitrate or
      biomass channel in the cluster.

  - id: lit-ultrasonic-tOF
    title: "Ultrasonic time-of-flight distance measurement and the speed of sound"
    publisher: "peer-reviewed and reference literature"
    source_type: literature
    url: ""
    accessed: ""
    used_for: >-
      Identifies the two systematic biases the firmware does not correct: an
      uncompensated speed-of-sound constant and an assumed zero sensor offset.
    authority: primary-literature
    notes: >-
      IDENTIFIER TO BE VERIFIED. No accuracy figure for the CIRQUA system is
      derived from or quoted alongside this reference.

  # -------------------------------------------------------------------------
  # Standards — listed for orientation. NO CONFORMANCE IS CLAIMED.
  # -------------------------------------------------------------------------
  - id: std-iso-24512
    title: "ISO 24512 — Water reuse — Guidelines for treated water usage"
    publisher: "International Organization for Standardization"
    source_type: standard
    url: ""
    accessed: ""
    used_for: >-
      Contextualises the purpose of the effluent-quality measurements the cluster
      reports. Relevant to the subject matter only.
    authority: secondary
    notes: >-
      NO CONFORMANCE IS CLAIMED, IMPLEMENTED OR TESTED. The firmware contains no
      standards-conformance logic. The specific edition is not verified.

  - id: std-iso-16061
    title: "ISO 16061 — Irrigation management — Controllers with electrical control interfaces"
    publisher: "International Organization for Standardization"
    source_type: standard
    url: ""
    accessed: ""
    used_for: >-
      Potentially relevant to the downstream controller that Node 4 forwards
      frames to.
    authority: secondary
    notes: >-
      NO CONFORMANCE IS CLAIMED. Whether the downstream controller falls within
      this standard's scope is NOT verified from the current source: its
      firmware is not in this repository. The specific edition is not verified.

  - id: std-eu-wfd
    title: "Directive 2000/60/EC — Water Framework Directive"
    publisher: "European Union"
    source_type: standard
    url: ""
    accessed: ""
    used_for: >-
      Policy context for a European water-reuse and water-efficiency initiative,
      including monitoring programmes and water-use efficiency.
    authority: secondary
    notes: >-
      NO CONFORMANCE IS CLAIMED. The firmware performs no reporting to any
      authority and produces no regulatory output.

  - id: std-iso-9001
    title: "ISO 9001 — Quality management systems — Requirements"
    publisher: "International Organization for Standardization"
    source_type: standard
    url: ""
    accessed: ""
    used_for: >-
      Listed solely to state explicitly that it is NOT claimed. No quality
      management system, certification, audit or conformity claim exists for
      this firmware or for this documentation set.
    authority: secondary
    notes: "EXPRESSLY NOT CLAIMED."

  - id: std-iso-17025
    title: "ISO/IEC 17025 — General requirements for the competence of testing and calibration laboratories"
    publisher: "International Organization for Standardization"
    source_type: standard
    url: ""
    accessed: ""
    used_for: >-
      Orientation on where calibration of equipment of this kind should be
      performed.
    authority: secondary
    notes: >-
      NO CONFORMANCE IS CLAIMED. No calibration in this project has been
      performed by an accredited laboratory; every reported quantity is an
      uncalibrated field estimate.

  # -------------------------------------------------------------------------
  # Documentation conventions
  # -------------------------------------------------------------------------
  - id: conv-rfc2119
    title: "RFC 2119 / BCP 14 — Key words for use in RFCs to Indicate Requirement Levels"
    publisher: "IETF"
    source_type: standard
    url: "https://www.rfc-editor.org/rfc/rfc2119"
    accessed: "2026-10-03"
    used_for: >-
      Recorded as NOT APPLIED. This documentation set distinguishes requirement
      from suggestion using the explicit labels Recommendation, Engineering
      interpretation and Not verified from the current source, rather than RFC
      2119 keywords.
    authority: secondary
    notes: "Explicitly not adopted as a convention in this documentation set."

  - id: conv-commonmark
    title: "CommonMark"
    publisher: "CommonMark"
    source_type: standard
    url: "https://commonmark.org/"
    accessed: "2026-10-03"
    used_for: "Markdown syntax used by MkDocs, with documented extensions layered on top."
    authority: tooling
    notes: "Documentation formatting convention only."
```

## Registry summary

| Source type | Records | Notes |
|---|---|---|
| `repository` (firmware) | 2 | The pinned commit; the primary basis for all implementation claims |
| `project` | 5 | Official project and partner sites; all primary, all time-varying |
| `manufacturer` (devices) | 5 | Only for parts named in the source; HC-SR04 and SEN0189 deliberately have no URL |
| `manufacturer` (libraries) | 5 | Canonical repositories; no version is pinned anywhere |
| `unidentified` components | 4 | DO, flow, pH, EC — recorded as gaps, not guessed |
| `rtos` / language | 3 | FreeRTOS, ESP-IDF, Arduino language reference |
| `tooling` | 4 | Python, MkDocs, Material for MkDocs, PyYAML |
| `literature` | 7 | Identifiers deliberately omitted pending verification |
| `standard` | 6 | **No conformance is claimed, implemented or tested** |
| Convention | 2 | RFC 2119 recorded as not applied; CommonMark as the formatting base |

## Invariants encoded in this registry

These are the rules the registry exists to enforce.

1. **No conformance claim.** No record asserts that the firmware complies with
   any standard, and the firmware contains no standards-conformance logic.
2. **No specification for an unnamed part.** A device specification is only ever
   attached to a part whose name appears in the firmware.
3. **No invented identifier.** Where an identifier was not verified, the field is
   empty and the `notes` field says so. An empty URL is a deliberate statement,
   not an oversight.
4. **No credentials.** No record contains a password, token, real SSID or
   mailbox address. The SMTP configuration in the firmware is placeholder text.
5. **One access date convention.** All web sources were consulted on
   **2026-10-03**; re-consultation requires updating the `accessed` field.
6. **Nothing is asserted beyond its source.** Where a claim cannot be extended
   without re-checking, the `notes` field says so explicitly.

## Related

* [References index](index.md) — the human-readable hub.
* [Official Project Sources](official-project-sources.md) — the five project
  pages in full.
* [Datasheets](datasheets.md) — component detail and the
  "documentation to obtain" checklist.
* [Standards](standards.md) — why none is claimed.
* [Scientific Literature](scientific-literature.md) — the framing behind the
  measurement principles.
* [Firmware Repository](../firmware/repository.md) — the pinned commit this
  registry depends on.
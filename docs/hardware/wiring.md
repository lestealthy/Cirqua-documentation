---
title: Wiring
description: Per-node connection tables for the CIRQUA cluster, derived only from the verified GPIO maps — UART crossovers, I2C, 1-Wire and level-shift hazards.
---

# Wiring

**Schematics: not available.** No schematic files, circuit diagrams or
connection drawings exist in the firmware repository. Everything on this page
is derived strictly from the verified GPIO assignments in
<a href="gpio-map.html">GPIO Map</a>, plus clearly labelled engineering
reasoning about the electrical behaviour those assignments imply.

!!! warning "Pin numbers do not carry across nodes"

    Never wire two different nodes together by matching pin numbers. Confirm
    the node identity first. See
    <a href="gpio-map.html#shared-pin-facts-you-must-know">Shared-pin facts</a>.

## Node 1 — Collection Tank A

| Function | GPIO | Connect to | Notes |
|---|---|---|---|
| Ultrasonic TRIG | 2 | HC-SR04 `TRIG` | Driven output, 2–3 µs low / 10 µs high |
| Ultrasonic ECHO | 17 | HC-SR04 `ECHO` | **5 V logic level risk** — see below |
| LCD SDA | 21 | I2C backpack `SDA` | Address `0x27` |
| LCD SCL | 22 | I2C backpack `SCL` | Address `0x27` |
| UART1 TX | 33 | **Node 2** GPIO 25 (RX) | 9600 8N1; TX→RX crossover |
| UART1 RX | 32 | **Node 2** GPIO 26 (TX) | 9600 8N1 |
| GND | — | **Node 2** GND | **Required** — see below |
| VCC | — | Sensor / LCD supply | 3.3 V logic domain; see <a href="power.html">Power</a> |

Node 1 has **no upstream link** — it is the cluster head and originates the
upstream frame itself.

## Node 2 — Feeding Tank B

| Function | GPIO | Connect to | Notes |
|---|---|---|---|
| DS18B20 data | 4 | DS18B20 DQ (water temp) | 1-Wire; **external pull-up required** |
| DO analog | 34 | Dissolved oxygen board analogue out | **Input-only pin, ADC1_CH6**; no internal pull-up available |
| Ultrasonic TRIG | 16 | HC-SR04 `TRIG` | Driven output |
| Ultrasonic ECHO | 17 | HC-SR04 `ECHO` | **5 V logic level risk** — see below |
| DHT11 | 27 | DHT11 data pin | Single-wire digital; internal pull-up handling not configured in source |
| UART1 TX | 26 | **Node 1** GPIO 32 (RX) | 9600 8N1; TX→RX crossover |
| UART1 RX | 25 | **Node 1** GPIO 33 (TX) | 9600 8N1 |
| UART2 TX | 33 | **Node 3** GPIO 25 (RX) | 9600 8N1 |
| UART2 RX | 32 | **Node 3** GPIO 26 (TX) | 9600 8N1 |
| GND | — | Node 1 **and** Node 3 GND | Node 2 is the mid-point of the chain |

Node 2 has **no display** and no I2C bus.

## Node 3 — Flow metering

| Function | GPIO | Connect to | Notes |
|---|---|---|---|
| Flow pulse | 23 | Flow sensor signal output | `INPUT_PULLUP` configured; ISR on **FALLING** |
| UART1 TX | 26 | **Node 2** GPIO 32 (RX) | 9600 8N1 |
| UART1 RX | 25 | **Node 2** GPIO 33 (TX) | 9600 8N1 |
| UART2 TX | 33 | **Node 4** GPIO 25 (RX) | 9600 8N1 |
| UART2 RX | 32 | **Node 4** GPIO 26 (TX) | 9600 8N1 |
| GND | — | Node 2 **and** Node 4 GND | Node 3 is the mid-point of the chain |

Node 3 has **no display**, **no analogue inputs** and **no 1-Wire**.

## Node 4 — Effluent

Identical pin map for the `Node4_SMTP` variant.

| Function | GPIO | Connect to | Notes |
|---|---|---|---|
| Ultrasonic TRIG | 4 | HC-SR04 `TRIG` | Driven output; note this is 1-Wire on **Node 2** |
| Ultrasonic ECHO | 2 | HC-SR04 `ECHO` | **5 V logic level risk**; note this is TRIG on **Node 1** |
| pH analog | 13 | pH probe board output | **ADC2** — unusable while Wi-Fi is active (SMTP variant) |
| Turbidity analog | 14 | Turbidity board output | **ADC2** — same caution |
| EC analog | 12 | EC board output | **ADC2** — same caution; also a strapping pin |
| DS18B20 data | 27 | DS18B20 DQ (submerged) | 1-Wire; **blocking** conversion; external pull-up required |
| DHT11 | 5 | DHT11 data pin | Single-wire digital; note this is DS18B20 on **Node 2** |
| UART1 TX | 26 | **Node 3** GPIO 32 (RX) | 9600 8N1 |
| UART1 RX | 25 | **Node 3** GPIO 33 (TX) | 9600 8N1 |
| UART2 TX | 33 | **Controller** GPIO 32 (RX) | 9600 8N1; source comments this as "To Controller (Mega)" |
| UART2 RX | 32 | **Controller** GPIO 33 (TX) | 9600 8N1 |
| LCD SDA | 21 | I2C backpack `SDA` | Address `0x27` |
| LCD SCL | 22 | I2C backpack `SCL` | Address `0x27` |

## Inter-node UART connections

Every link is 9600 baud, 8 data bits, no parity, 1 stop bit, and every link is a
**TX↔RX crossover**. Summary in chain order:

| Link | From (TX → RX) | To |
|---|---|---|
| 1 | Node 1 GPIO **33** (TX) | Node 2 GPIO **25** (RX) |
| 2 | Node 2 GPIO **26** (TX) | Node 1 GPIO **32** (RX) — reverse echo |
| 3 | Node 2 GPIO **33** (TX) | Node 3 GPIO **25** (RX) |
| 4 | Node 3 GPIO **26** (TX) | Node 2 GPIO **32** (RX) |
| 5 | Node 3 GPIO **33** (TX) | Node 4 GPIO **25** (RX) |
| 6 | Node 4 GPIO **26** (TX) | Node 3 GPIO **32** (RX) |
| 7 | Node 4 GPIO **33** (TX) | Controller GPIO **32** (RX) |
| 8 | Controller GPIO **33** (TX) | Node 4 GPIO **32** (RX) |

Full detail in <a href="../communication/serial-links.html">Serial Links</a>.

!!! important "Common ground is required for UART signalling — recommendation"

    **Engineering recommendation.** A TTL UART link is a single-ended,
    reference-to-reference signal. Every node in the chain must share a common
    ground with its neighbours, or the receiver's thresholds are undefined and
    framing errors become likely or the link fails entirely.

    **The firmware does not verify ground continuity** and provides no
    mechanism to detect a broken or missing common. A lifted ground on a
    field cable will present as intermittent `ERROR` on the Node 1 display or
    as the Node 3 timeout fallback — see
    <a href="../communication/fault-handling.html">Fault Handling</a>.

    **Recommendation.** Bond the ground conductor through the whole chain
    (Node 1 → Node 2 → Node 3 → Node 4 → controller) in the same cable as the
    data lines, and treat ground as part of the link, not as an afterthought.

## I2C for the LCDs

* **Firmware implementation.** Both displays are 16×4 HD44780-compatible
  character LCDs on an I2C backpack, at address **`0x27`**, on SDA GPIO 21 and
  SCL GPIO 22. Node 1's LCD shows cluster-wide values including Node 2's
  reverse echo; Node 4's LCD shows only Node 4's local values. Node 4 writes
  rows using explicit HD44780 DDRAM addresses `0x00`, `0x40`, `0x10`, `0x50`.
* **Engineering knowledge — typical, not verified.** I2C requires pull-up
  resistors on both SDA and SCL. PCF8574-based LCD backpack modules
  **typically** include them on the board. This has **not** been verified for
  the modules actually used, and no pull-up value appears in the source.
* **Recommendation.** Before first power-up, confirm with a meter that SDA and
  SCL each sit at about 3.3 V when idle. If either sits at 0 V, the bus is
  shorted or lacks pull-ups entirely.

## 1-Wire for the DS18B20 sensors

* **Firmware implementation.** Two DS18B20 devices: Node 2 GPIO 4 (water
  temperature, non-blocking) and Node 4 GPIO 27 (submerged temperature,
  `setResolution(10)`, blocking conversion). Validity requires a value that is
  not `DEVICE_DISCONNECTED_C` and lies strictly between −55 °C and 125 °C.
  Node 4 warns at boot if `getDeviceCount() == 0`.
* **Engineering knowledge.** 1-Wire requires a pull-up on the data line. The
  DS18B20 supports **parasite power**, in which the data line supplies the
  device.
* **Not verified from the current source.** Which of the two is actually used.
  The firmware does not configure `INPUT_PULLUP` on either pin, which is
  consistent with external pull-ups being fitted but does not prove it.
* **Recommendation.** Confirm the wiring at the sensor body. If the module is
  parasite-powered, normal (not strong) pull-ups are required, and the sensor
  must be within the current budget of the data line. If it is normally
  powered, fit a 4.7 kΩ pull-up to 3.3 V.

## Ultrasonic modules — level shifting is a real risk

!!! warning "HC-SR04 ECHO is a 5 V logic level; ESP32 GPIOs are 3.3 V"

    **Firmware implementation.** All three ultrasonic modules are driven and
    read directly by the ESP32: Node 1 GPIO 2/17, Node 2 GPIO 16/17,
    Node 4 GPIO 4/2. Trigger is driven as a 2–3 µs low / 10 µs high pulse and
    the echo is timed directly on the ESP32 GPIO.

    **Engineering knowledge.** The HC-SR04 is a 5 V device. When its supply is
    5 V, its `ECHO` output is a **5 V push-pull logic level**. Connecting that
    directly to an ESP32 GPIO — which is a 3.3 V domain input — puts the pin
    **above its absolute maximum rating**. This is a real hardware risk, not a
    theoretical one: repeated overvoltage degrades the GPIO and eventually
    destroys it.

    **The source shows no divider and no level shifter** on any of the three
    echo lines.

    **Recommendation.** Fit a resistive divider or a proper bidirectional
    level shifter on each `ECHO` line before first power-up, and verify the
    level at the ESP32 pin with a meter. If the modules are supplied from
    3.3 V, the echo level is already correct — but that supply arrangement
    must be **confirmed**, because the HC-SR04's specified minimum supply is
    5 V.

## Other electrical notes

* **GPIO 34 is input-only** on the ESP32 and has no internal pull-up or
  pull-down. Node 2's dissolved oxygen input uses it only as an analogue input,
  which is correct — but any open-drain sensor signal on that pin needs an
  external pull-up. *(Engineering knowledge, not from the source.)*
* **Strapping pins.** GPIO 0, 2, 5, 12 and 15 influence boot mode or other
  reset-time latches on the ESP32. In this design, GPIO 2 is Node 1's
  ultrasonic trigger, GPIO 5 is Node 4's DHT11 and GPIO 12 is Node 4's EC
  input. *(Engineering knowledge, not from the source.)*
* **DHT11 and flow sensor lines** are single-wire digital signals whose idle
  level depends on a pull-up. Node 3 explicitly configures `INPUT_PULLUP` on
  GPIO 23; the DHT11 pins (Node 2 GPIO 27, Node 4 GPIO 5) have no such
  configuration in the source, so an external pull-up may be required there.

## What must still be documented

> **Not verified from the current source.**
>
> * Cable types, lengths, gauges, connectors, pinouts and keying.
> * Whether level shifters or dividers are fitted on any echo or analogue line
>   in the built hardware.
> * Whether the LCD backpack modules include I2C pull-ups.
> * Whether external 1-Wire pull-ups are fitted, and whether parasite powering
>   is used.
> * The module supply voltage for each HC-SR04.
> * Terminal block, header and connector part numbers on any node.
> * Earthing, bonding and surge protection arrangement.

## Related pages

* <a href="gpio-map.html">GPIO Map</a> — the authoritative pin tables.
* <a href="../communication/serial-links.html">Serial Links</a — the physical
  link table.
* <a href="power.html">Power</a> — the 3.3 V and 5 V domains.
* <a href="../field-service/startup-checklist.html">Startup Checklist</a> —
  bench checks before leaving a node installed.

---
title: Hardware
description: Index of the hardware pages — ESP32 controllers, authoritative GPIO map, power budget, wiring and enclosures for the four CIRQUA nodes.
---

# Hardware

This section covers the physical layer of the CIRQUA node cluster: which
controller runs each node, which GPIO each peripheral is on, how power must be
provided, how the nodes are wired to each other, and what the firmware implies
about the enclosures.

| Page | What it covers |
|---|---|
| <a href="controllers.html">Controllers</a> | ESP32 on all four nodes — dual-core FreeRTOS, two `HardwareSerial` UARTs, I2C LCD bus, NVS calibration, 12-bit ADC configuration |
| <a href="gpio-map.html">GPIO Map</a> | **Authoritative pin reference** — per-node tables, a cross-node table sorted by GPIO number, and the shared-pin hazards |
| <a href="power.html">Power</a> | What the firmware implies about supply rails and logic levels, and the large amount of power information that is still undocumented |
| <a href="wiring.html">Wiring</a> | Per-node connection tables derived only from the verified GPIO maps, plus level-shift and earthing guidance |
| <a href="enclosures.html">Enclosures</a> | What the firmware implies about enclosure thermal monitoring, and what is still unknown about the physical enclosures |

## Node Hardware Matrix

Consolidated view. Every row is transcribed from the firmware source at commit
`db6d9b8`; nothing here is inferred from a datasheet or a photograph.

| Node | MCU | Sensors | Display | UART1 | UART2 | Tasks |
|---|---|---|---|---|---|---|
| **Node 1** — Collection Tank A (TAV) | ESP32 | HC-SR04 ultrasonic, GPIO 2 / 17 | 16×4 I2C LCD at `0x27`, SDA GPIO 21 / SCL GPIO 22 | RX 32, TX 33 — **to Node 2** | *not used* | `N1_Sensors`, `N1_UART`, `N1_LCD` |
| **Node 2** — Feeding Tank B (TBV) | ESP32 | DS18B20 (GPIO 4, 1-Wire), DO analog (GPIO 34, ADC1), HC-SR04 (GPIO 16 / 17), DHT11 (GPIO 27) | *none* | RX 25, TX 26 — **to Node 1** | RX 32, TX 33 — **to Node 3** | `N2_Sensors`, `N2_UART` |
| **Node 3** — Flow metering | ESP32 | Flow pulse input, GPIO 23 (`INPUT_PULLUP`, ISR on FALLING) | *none* | RX 25, TX 26 — **to Node 2** | RX 32, TX 33 — **to Node 4** | `N3_Flow`, `N3_UART` |
| **Node 4** — Effluent (TCV / EV) | ESP32 | HC-SR04 (GPIO 4 / 2), pH (GPIO 13, ADC2), turbidity (GPIO 14, ADC2), EC (GPIO 12, ADC2), DS18B20 (GPIO 27, 1-Wire), DHT11 (GPIO 5) | 16×4 I2C LCD at `0x27`, SDA GPIO 21 / SCL GPIO 22 | RX 25, TX 26 — **to Node 3** | RX 32, TX 33 — **to controller** | `N4_Sensors`, `N4_UART`, `N4_LCD` |
| **Node 4 (SMTP variant)** | ESP32 | *identical pin map to Node 4* | 16×4 I2C LCD at `0x27`, SDA GPIO 21 / SCL GPIO 22 | RX 25, TX 26 — **to Node 3** | RX 32, TX 33 — **to controller** | `N4_Sensors`, `N4_EmailUART`, `N4_LCD` |

### Two points the matrix makes immediately obvious

**Node 3 has no display.** There is no LCD task, no `Wire` initialisation and no
backlight handling in `Node3.ino`. Its single indicator output is the debug
`Serial` port at 115200 baud.

**Node 3 does not originate the upstream frame.** Node 3 is a pure forwarder.
It receives the frame that Node 1 started, appends its own flow field and its
own health flag, and passes the result on. It never synthesises the `TAV`,
`node1`, `DO` or `Temp`/`TBV`/`AT`/`AH` fields — the only frame Node 3 ever
*creates* from nothing is the one-shot timeout fallback, which contains zeros
and `node1:0` / `node2:0`. See
<a href="../communication/fault-handling.html">Fault Handling</a>.

## Claim types used on these pages

Three kinds of statement appear below and are labelled throughout:

* **Firmware implementation** — read directly from the source at commit `db6d9b8`.
* **Engineering interpretation** — a reasoned inference about why the code is
  written the way it is. Debatable, and labelled as such.
* **Recommendation** — advice from the documentation author. Not present in the
  firmware.

## Known gaps

> **Not verified from the current source.**
>
> * Exact ESP32 board variant, devkit model, module variant and PSRAM
>   configuration.
> * Supply voltage, current draw, regulator part numbers, battery or solar
>   topology.
> * Physical enclosure dimensions, IP rating, materials and mounting.
> * Sensor brand and model part numbers for the dissolved oxygen, flow, pH and
>   conductivity probes. Only **HC-SR04**, **DS18B20** and **DHT11** are named
>   in the source.
> * Cable types, lengths, gauges and connector pinouts.
> * Schematic files and circuit diagrams — none exist in the repository.
> * Hardware photographs — none exist in the repository.

## Related pages

* <a href="gpio-map.html">GPIO Map</a> — the pin reference to check before any
  wiring work.
* <a href="../rtos/index.html">RTOS</a> — how the controllers are scheduled.
* <a href="../communication/serial-links.html">Serial Links</a> — the physical
  UART chain between nodes.
* <a href="../sensors/index.html">Sensors</a> — measurement details for each
  sensing channel.

---
title: Node Identification
description: How to determine which of the four CIRQUA nodes you are holding, from physical role, LCD content, sensors and the Node 4 console.
---

# Node Identification

You should never need this page if the node is labelled. If the label or QR sticker is
missing — which happens — this page sets out how to identify a node from what the
hardware and firmware actually do.

Claim types used throughout: **Firmware implementation**, **Engineering
interpretation**, **Recommendation**.

!!! important

    **Recommendation:** durable node labels and QR stickers are the *only* reliable
    identifier. Apply one if the node is unlabelled. The reason is explained in
    [The protocol has no node addressing](#the-protocol-has-no-node-addressing) below,
    and it is the single most important finding on this page.

## Observable decision table

Every entry below is either a physical property of the installation or a behaviour
present in the audited firmware. Nothing here is inferred from a guess.

| Observable | Node 1 | Node 2 | Node 3 | Node 4 |
|---|---|---|---|---|
| **Physical tank role** | Collection Tank A | Feeding Tank B | In-line on the flow path | Effluent |
| **16×4 I2C LCD** | Yes, address `0x27` | **No** | **No** | Yes, address `0x27` |
| **Debug console at 115200** | Not implemented | Not implemented | Not implemented | **Yes** — `HELP` / `STATUS` |
| **Connected sensors** | HC-SR04 only | DS18B20, DHT11, DO analogue, HC-SR04 | Flow sensor only | pH, turbidity, EC, DS18B20, DHT11, HC-SR04 |
| **Analog inputs fitted** | 0 | 1 (GPIO 34) | 0 | 3 (GPIO 13, 14, 12) |
| **1-Wire bus** | No | Yes (GPIO 4) | No | Yes (GPIO 27) |
| **DHT11 present** | No | Yes (GPIO 27) | No | Yes (GPIO 5) |
| **Data field on the wire** | `TAV`, `node1` | `DO`, `Temp`, `TBV`, `AT`, `AH`, `node2` | `FLM`, `node3` | `pH`, `Turb`, `EC`, `TCV`, `node4` |
| **Chain position** | Head — originates the frame | Middle | Middle | Tail — forwards to the controller |
| **UART to downstream neighbour** | None (single link) | UART2 → 32/33 | UART2 → 32/33 | UART2 → 32/33 (controller) |

## Method 1 — physical role (most reliable)

**Firmware implementation.** The sensor mix is fixed per node in the sketches, and it maps
one-to-one onto the tank the node serves.

- A node with **no sensors other than an ultrasonic sensor on a large tank** is Node 1,
  and that tank is Collection Tank A.
- A node with **a dissolved-oxygen module, a DS18B20, a DHT11 and an ultrasonic sensor**
  is Node 2, and that tank is Feeding Tank B.
- A node with **only a flow sensor and no display** is Node 3.
- A node with **three analogue modules (pH, turbidity, EC), a submerged DS18B20, a DHT11,
  an ultrasonic sensor and a display** is Node 4, and that tank is the effluent channel.

The count of analogue channels is often the fastest visual discriminator: Node 1 and
Node 3 have none; Node 2 has exactly one; Node 4 has exactly three.

## Method 2 — the LCD

**Firmware implementation.** Node 1 and Node 4 both fit a 16×4 I2C LCD at address
`0x27`. Node 2 and Node 3 have no display at all. **The presence of a display therefore
narrows the field to two candidates**, and the content distinguishes them.

### Node 1 — Collection Tank A

**Firmware implementation.** `Task_LCD_Node1` renders four rows at a 500 ms period:

| Row | Pattern | Notes |
|---|---|---|
| 1 | `C<TAV>L F<TBV>L` | `F` field shows `----` when the Node 2 volume is unavailable |
| 2 | `DO<mg/l> T<Temp>C` | `--` placeholders when unavailable; decimal point rendered as comma |
| 3 | `AT<AT>C H<AH>%` | Comma decimal separator |
| 4 | `STATUS: <status>` | See below |

The fourth row is unique to Node 1. The full precedence, in order:

| # | Condition | Text shown |
|---|---|---|
| 1 | No frame ever received from Node 2 | `WAITING` |
| 2 | `millis() - lastRx > 3000` ms | `ERROR` |
| 3 | Ambient `>= 45 °C` **and** humidity `>= 80 %` | `HOT+HUM` |
| 4 | Ambient `>= 45 °C` | `OVERTEMP` |
| 5 | Humidity `>= 80 %` | `HI HUMID` |
| 6 | `TAV < 5000` **and** `TBV < 500` | `LOW C+F` |
| 7 | `TAV < 5000` | `LOW TAV` |
| 8 | `TBV < 500` | `LOW TBV` |
| 9 | Node 2 reported `node2:0` | `FAULT` |
| 10 | Otherwise | `NORMAL` |

**Engineering interpretation.** A `STATUS:` row is conclusive: only Node 1 produces one.

### Node 4 — Effluent

**Firmware implementation.** `Task_LCD_Node4` writes four rows using explicit DDRAM
addresses, also at 500 ms:

| Row | Pattern |
|---|---|
| 1 | `EV:<litres>L pH:<value>` |
| 2 | `TU:<ntu> EC:<ec>uS` |
| 3 | `ST:<submerged °C>C AT:<ambient °C>C` |
| 4 | `AH:<humidity>%` |

`Node4_SMTP` renders row 2 as `EC:<value>mS` instead.

**Engineering interpretation.** The `EV:`, `TU:`, `ST:` and `AH:` prefixes identify Node 4
and exclude Node 1. Note there is **no status row on Node 4** — a Node 4 display can look
completely healthy while every sensor is invalid, because the task prints the stored
numbers regardless of the validity flags. See
[Troubleshooting](troubleshooting.md#node-4-display-reads-zero).

## Method 3 — the sensors actually connected

**Firmware implementation.** The GPIO maps are fixed. Use these as a cross-check against
what you can see:

| Signal | Node 1 | Node 2 | Node 3 | Node 4 |
|---|---|---|---|---|
| Ultrasonic TRIG | 2 | 16 | — | 4 |
| Ultrasonic ECHO | 17 | 17 | — | 2 |
| Flow pulse | — | — | 23 | — |
| Dissolved oxygen | — | 34 | — | — |
| pH | — | — | — | 13 |
| Turbidity | — | — | — | 14 |
| EC | — | — | — | 12 |
| DS18B20 | — | 4 | — | 27 |
| DHT11 | — | 27 | — | 5 |
| LCD SDA / SCL | 21 / 22 | — | — | 21 / 22 |

!!! warning

    **GPIO numbers do not carry across nodes.** Node 1 uses **GPIO 2 for TRIG and 17 for
    ECHO**. Node 4 uses **GPIO 4 for TRIG and 2 for ECHO**. Node 1 and Node 2 both use
    **GPIO 17** for ECHO. A module wired by pin number from the wrong node's table will
    produce a node that appears dead while the actual sensor is fine. This is one of the
    most likely field faults — see
    [Troubleshooting: no data on the link](troubleshooting.md#no-data-on-the-link).

## Method 4 — the Node 4 debug console

**Firmware implementation.** Only Node 4 implements a command console on the debug UART at
115200 baud. Nodes 1, 2 and 3 open no `Serial` service that accepts input.

Open a serial terminal at **115200 baud, 8N1** and send:

```text
HELP
```

A response containing the banner `========== NODE 4 CALIBRATION DEBUG CONSOLE ==========`
and the command list is conclusive: **you are holding Node 4** (or `Node4_SMTP`, which
shares the pin map but not the console — if there is no response, check whether the
running firmware is `Node4_SMTP`).

Then send `STATUS` to see all three analogue channels at once — see
[Troubleshooting: serial console diagnostics](troubleshooting.md#serial-console-diagnostics).

**Recommendation.** Record the firmware variant alongside the node identity. `Node4` and
`Node4_SMTP` share hardware and pin assignments but report different EC units, different
turbidity voltage domains and different pH temperature handling. See
[Node 4](../nodes/node4.md) and [Node 4 SMTP](../nodes/node4-smtp.md).

## The protocol has no node addressing

**This is the important honest finding.**

**Firmware implementation.** The inter-node frames carry a health flag per node —
`|node1:`, `|node2:`, `|node3:`, `|node4:`, where `1` means "all local sensor validity
flags are true" — but they carry **no node identifier**. There is no checksum, no CRC, no
sequence number, no acknowledgement and no retry. Validation is purely structural:
`validateUpstreamFrame()` checks that expected key strings are present.

**Engineering interpretation.** Consequences a technician must understand:

- **A swapped pair of nodes is undetectable from telemetry.** If two physically similar
  nodes are exchanged in their enclosures, the link will carry frames, the health flags
  will look normal, and the values will simply be wrong. Nothing in the data will say so.
- **Frame origin is not checked.** A receiving node does not verify that a frame came
  from the neighbour it expects.
- **A damaged or colliding frame can be accepted if it contains the expected keys.**
  There is no integrity protection.
- **Values can silently shift.** Because each node's sensors appear as distinct named
  fields (`TBV` vs `TCV`), a swap changes the meaning of values without changing their
  appearance.

**Recommendation.**

- [ ] Apply a durable, weather-resistant label to every node stating node number, role
      and firmware variant.
- [ ] Apply the matching QR sticker — see the [QR code reference](#qr-code-reference)
      table below.
- [ ] Record the swap in the maintenance log if you physically exchange nodes.
- [ ] If a node has been unlabelled since installation, treat its identity as
      **unverified** until confirmed against the tank it is physically mounted on, and
      confirm the channel values are plausible for that tank before trusting the data.

## QR code reference

**Firmware implementation / project fact.** Each node page has a permanent flat URL
(the site is published with `use_directory_urls: false`). These are the label targets:

| Node | QR target URL | Image |
|---|---|---|
| Node 1 | `https://lestealthy.github.io/Cirqua-documentation/nodes/node1.html` | `assets/qr/` |
| Node 2 | `https://lestealthy.github.io/Cirqua-documentation/nodes/node2.html` | `assets/qr/` |
| Node 3 | `https://lestealthy.github.io/Cirqua-documentation/nodes/node3.html` | `assets/qr/` |
| Node 4 | `https://lestealthy.github.io/Cirqua-documentation/nodes/node4.html` | `assets/qr/` |
| Node 4 SMTP | `https://lestealthy.github.io/Cirqua-documentation/nodes/node4-smtp.html` | `assets/qr/` |

Local equivalents: [Node 1](../nodes/node1.md) · [Node 2](../nodes/node2.md) ·
[Node 3](../nodes/node3.md) · [Node 4](../nodes/node4.md) ·
[Node 4 SMTP](../nodes/node4-smtp.md)

The artwork, label dimensions and printing guidance are on [QR codes](qr-codes.md).

!!! note

    > **Not verified from the current source.** Whether any QR sticker has actually been
    > produced or affixed, and whether any node has been physically installed. No
    > hardware photographs exist in the repository.

## Related pages

- [Field service index](index.md)
- [Startup checklist](startup-checklist.md)
- [Troubleshooting](troubleshooting.md)
- [Hardware: GPIO map](../hardware/gpio-map.md)
- [Communication: message format](../communication/message-format.md)
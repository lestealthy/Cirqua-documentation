---

title: Enclosures

description: What the CIRQUA firmware implies about enclosures — Node 2's DHT11 as an enclosure-health sensor, display fit, and the physical data still unrecorded.

---

# Enclosures

> **Not verified from the current source.** Physical enclosure dimensions, IP

> rating, materials, mounting method and seal type. No photographs, drawings or

> CAD files exist in the firmware repository. This page records only what the

> code implies and is explicit about everything else.

## Nodes with a display

| Node | Display | I2C address | SDA / SCL |

|---|---|---|---|

| Node 1 | 16×4 character LCD on an I2C backpack | **`0x27`** | GPIO 21 / GPIO 22 |

| Node 4 (and SMTP variant) | 16×4 character LCD on an I2C backpack | **`0x27`** | GPIO 21 / GPIO 22 |

| Node 2 | **none** | — | — |

| Node 3 | **none** | — | — |

Both displays sit at the **same I2C address, `0x27`**, on the **same GPIO pair,

21/22**. They are on different controllers, so there is no bus conflict — but

they also cannot be distinguished by address when field-swapping a module.

Node 4 writes its rows using explicit HD44780 DDRAM addresses `0x00`, `0x40`,

`0x10` and `0x50`, sent as `lcdN4.command(0x80 | addr)`. This confirms a

genuine HD44780-compatible controller with the standard row mapping, but says

nothing about the physical panel size beyond "16×4 characters".

## The DHT11 is treated as an enclosure-health sensor

**Firmware implementation.** Node 1's pin-definition block carries this

comment directly above the environmental thresholds:

```cpp

--8<-- "assets/snippets/node1-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>pin-definitions block</code> ·

lines 5–35 · commit <code>db6d9b8</code>
</div>

Two things follow from that comment, and the distinction matters:

1. The thresholds are explicitly attributed to the **Node 2 enclosure** — not

   to Node 1's. `TEMP_ALERT_TH 45.0f` (overheat) and `HUMID_ALERT_TH 80.0f`

   (condensation) are described as environmental safety thresholds for the

   enclosure that houses **Node 2's DHT11**.

2. The values Node 1 displays as `AT` and `AH` arrive from **Node 2 over the

   reverse echo frame** (`|AT:%.2f|AH:%.2f`). They are *not* measured on Node 1.

**Engineering interpretation.** The DHT11 is therefore being used as an

**enclosure-health sensor** rather than as an environmental measurement for the

treatment process: it is there to warn that the electronics enclosure is

overheating or that condensation is forming inside it. 80 % RH is a

condensation-risk threshold, not a comfort or process threshold — the inline

comment says exactly that.

**Engineering interpretation.** A further consequence: because Node 1 raises

these alerts from *remotely received* data, the enclosure alarm for Node 2

depends on the Node 1 → Node 2 → Node 1 link being alive. If that link drops,

Node 1's status line goes to `ERROR` before the thermal information can help.

The two failure modes are not independent.

### Where the enclosure thresholds surface

Node 1 LCD status precedence, exactly as implemented:

| Order | Condition | Status shown |

|---|---|---|

| 1 | No frame ever received | `WAITING` |

| 2 | `millis() - lastRx > RX_TIMEOUT_MS (3000)` | `ERROR` |

| 3 | `ambientTemp >= 45.0` **and** `humidity >= 80.0` | `HOT+HUM` |

| 4 | `ambientTemp >= 45.0` | `OVERTEMP` |

| 5 | `humidity >= 80.0` | `HI HUMID` |

| 6 | `TAV < 5000` **and** `TBV < 500` | `LOW C+F` |

| 7 | `TAV < 5000` | `LOW TAV` |

| 8 | `TBV < 500` | `LOW TBV` |

| 9 | `!node2Health` | `FAULT` |

| 10 | otherwise | `NORMAL` |

The `ERROR` and `WAITING` conditions outrank the thermal conditions, so link

health always wins the display line over enclosure health.

```cpp

--8<-- "assets/snippets/node1-lcd-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>Task_LCD_Node1</code> ·

lines 220–310 · commit <code>db6d9b8</code>
</div>

## Node 4's enclosure context

**Firmware implementation.** Node 4 also carries a DHT11 (GPIO 5) alongside its

own LCD, and its display shows ambient values:

| Row | Content |

|---|---|

| 0 | `EV:%dL pH:%.1f` |

| 1 | `TU:%d EC:%duS` (SMTP variant: `EC:%.1fmS`) |

| 2 | `ST:%.1fC AT:%.1fC` |

| 3 | `AH:%.0f%%` |

**Node 4 has no status or error line.** There is no `OVERTEMP` equivalent on

this display — its fault behaviour differs by variant:

| Variant | Enclosure-relevant fault condition |

|---|---|

| `Node4` | No ambient-derived alert on the display. Ambient is shown but not thresholded for status. |

| `Node4_SMTP` | `hasError` is raised when **any** validity flag is false, **or** `ambTemp > 45`, **or** `ambHum > 90`. Fault e-mails itemise each failed sensor in an HTML list. |

Note the humidity threshold differs between the two contexts: **80 %** in

Node 1's display logic, **90 %** in the SMTP variant's e-mail alert logic.

**Firmware implementation.** Node 4 also gates its ambient DHT11 readings more

tightly than Node 2 does — ambient temperature must be within −20 to 80 °C and

humidity within 0 to 100 %. The SMTP variant reverts to Node 2's looser

`!isnan()` check with no range gate. This is a genuine divergence between the

variants.

```cpp

--8<-- "assets/snippets/node4-lcd-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_LCD_Node4</code> ·

lines 1187–1259 · commit <code>db6d9b8</code>
</div>

## `cleanUpstreamPacket` and the enclosure ambient pair

**Firmware implementation.** Node 4 strips the `AT:` and `AH:` tokens out of

the upstream frame before appending its own fields, so the controller receives

exactly **one** ambient temperature/humidity pair — Node 4's own DHT11, not

Node 2's.

```cpp

--8<-- "assets/snippets/node4-packet-cleaner.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>cleanUpstreamPacket</code> ·

lines 936–990 · commit <code>db6d9b8</code>
</div>

**Engineering interpretation.** This is an enclosure decision encoded in the

protocol: Node 4 is the cluster tail, so its DHT11 is treated as the

authoritative enclosure ambient reading for the downstream record.

## What the firmware implies about enclosure fit

**Engineering interpretation**, drawn only from what is coded:

| Observation | Implication |

|---|---|

| Node 2 hosts a DHT11 whose readings drive condensation and overheat alerts, labelled "Node 2 Enclosure" | The Node 2 enclosure is expected to be sealed or semi-sealed enough for internal humidity to be a meaningful risk indicator |

| Node 1 and Node 4 both have a 16×4 LCD | Those two enclosures have a visible panel or window for local readout |

| Node 2 and Node 3 have no display | Their enclosures need no viewing aperture |

| Node 4 combines six sensing devices plus a display in one enclosure | Node 4's enclosure is the most densely populated and the most constrained for cable entry |

| Ultrasonic modules need a clear line of sight to the tank surface | The Node 1, 2 and 4 enclosures must leave the sensor path unobstructed and dry |

| Node 3's flow input uses `INPUT_PULLUP` and an ISR | Node 3's enclosure must let the flow sensor's signal reach GPIO 23 with a reliable return path |

**Recommendation.** Whatever enclosure is specified, keep the condensation

argument in mind: the firmware treats 80 % RH as a fault condition, so a vented

design will trip `HI HUMID` in humid weather. If ventilation is required for

another reason, the threshold needs revisiting — it is a firmware constant, not

a physical property.

## What must still be documented

> **Not verified from the current source.**

>

> * Enclosure external dimensions for any node.

> * IP rating or ingress-protection rating.

> * Enclosure material, wall thickness and UV/weathering specification.

> * Mounting method: post, wall bracket, floor stand or DIN rail.

> * Gland, conduit and cable-entry arrangement, and the number/size of entries

>   actually required.

> * Whether the Node 2 DHT11 is mounted internally or externally, and its

>   position relative to any heat source.

> * Display viewing angle, backlight type and whether a window is bonded or

>   screw-fitted.

> * Thermal design: whether any passive or forced cooling is fitted.

> * Silicone or gasket type used at cable entries.

> * Photographs or assembly drawings of any node.

## Related pages

* <a href="gpio-map.html">GPIO Map</a> — display and sensor pin assignments.

* <a href="wiring.html">Wiring</a> — cable entry and level-shift hazards.

* <a href="power.html">Power</a> — continuous draw from the always-on displays.

* <a href="../sensors/humidity.html">Humidity</a> — DHT11 behaviour and pacing.

* <a href="../communication/fault-handling.html">Fault Handling</a> — how

  `ERROR` outranks `OVERTEMP` on the display.


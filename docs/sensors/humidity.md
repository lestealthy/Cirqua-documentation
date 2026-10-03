---

title: Humidity & Ambient

description: DHT11 ambient temperature and relative humidity on Nodes 2 and 4 — GPIO 27 and GPIO 5, 2 s read pacing, per-node validity gating and alert thresholds.

---

# Humidity & Ambient

Ambient temperature and relative humidity are measured with a DHT11 on

**Nodes 2 and 4**. There is no humidity sensor on Node 1 or Node 3; Node 1

displays the values measured at Node 2.

Ambient data matters to the cluster beyond reporting: the values drive the

`OVERTEMP` and `HI HUMID` status strings on the Node 1 LCD, and on the SMTP

variant they also gate fault e-mails.

<div class="cirqua-identity">

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Nodes</span>

    <span class="cirqua-identity__value">2 and 4</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">GPIO</span>

    <span class="cirqua-identity__value">N2 <code>PIN_DHT11</code> <code>27</code><br>N4 <code>PIN_N4_DHT11</code> <code>5</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Interface</span>

    <span class="cirqua-identity__value">Single-wire digital, framed bit protocol (DHT <code>DHTTYPE DHT11</code>)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Signal type</span>

    <span class="cirqua-identity__value">Digital, single-wire; returns a read value or a failure sentinel (<code>NAN</code>)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware reading function</span>

    <span class="cirqua-identity__value"><code>Task_Sensors_Node2</code>, <code>Task_Sensors_Node4</code> → <code>readTemperature()</code>, <code>readHumidity()</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Frame field</span>

    <span class="cirqua-identity__value"><code>AT:%.2f</code>, <code>AH:%.2f</code> from Node 2 · <code>AT</code>, <code>AH</code> LCD rows 2 and 3 at Node 4</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Status</span>

    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--variant">per-node gating differs</span></span>

  </div>

</div>

## Purpose and measured quantity

Two quantities, both ambient — that is, of the air inside or immediately around

the node enclosure, not of the water:

| Quantity | Node 2 field | Node 4 use |

|---|---|---|

| Ambient temperature, °C | `AT` | LCD row 2; e-mail alert gating (SMTP variant) |

| Relative humidity, % | `AH` | LCD row 3; e-mail alert gating (SMTP variant) |

### Node 2 values travel; Node 4 values replace them

Node 2 emits `AT:%.2f` and `AH:%.2f` into the frame, and they propagate through

Node 3 to Node 4. At Node 4, `cleanUpstreamPacket()` **strips the upstream

`AT:` and `AH:` tokens** before the packet is forwarded to the downstream

controller, and Node 4's own DHT11 values take their place.

The result is that the controller receives **one** ambient pair, from Node 4.

This is deliberate, and it means the ambient values a data consumer sees

downstream are Node 4's, not Node 2's — even though Node 2's are still present

in the stream between Nodes 2 and 4.

Node 1 receives Node 2's values and uses them for its LCD status logic. Note

that Node 1 and Node 4 therefore display **different** ambient values from the

same cluster.

## Physical principle

> **Manufacturer specification.** `DHT11` is the part name written in the

> firmware. This documentation has not been checked against a DHT11 datasheet,

> and no accuracy figure, humidity range, temperature range, resolution,

> sampling rate, supply voltage or long-term drift specification is asserted on

> this page. The exact fitted part number and its manufacturer are

> **Not verified from the current source.**

Generic principle, independent of any particular part: a capacitive polymer

sensor changes its capacitance with the relative humidity of the air around it,

and a temperature-sensitive element provides the second channel. Both are

converted internally and the pair is transmitted as a checksummed digital frame

on a single wire, so the receiving device applies no analogue conversion.

The DHT11 belongs to a class of digital humidity sensors that are

**slow and of comparatively low accuracy**, and which are limited to a coarse

temperature channel alongside the humidity channel. The firmware reflects that

coarseness in practice: readings are paced at most every 2 seconds, and Node 4

formats ambient temperature to one decimal place. Stating that the sensor is

slow and relatively inaccurate is as far as this documentation can go — no

numeric accuracy figure is available from the source, and none is invented

here.

## Electrical interface

A single-wire digital bus, distinct from the 1-Wire bus used by the

[DS18B20](temperature.md) temperature sensors. The two must not be confused:

the DHT protocol is a framed bit protocol with a start signal, a data payload

and a checksum, not the 1-Wire ROM and command structure.

| Property | Node 2 | Node 4 |

|---|---|---|

| Pin | GPIO 27 (`PIN_DHT11`) | GPIO 5 (`PIN_N4_DHT11`) |

| Type macro | `DHTTYPE DHT11` | `DHTTYPE DHT11` |

| Library instance | `dhtN2` | `dhtN4` |

| Initialisation | `dhtN2.begin()` before the loop | `initializeDHT()` |

| Read pacing | at most every **2000 ms** | at most every **2000 ms** |

Pacing is enforced in firmware rather than relying on the library's own

minimum interval:

```cpp

if (now - xLastDHTTick >= pdMS_TO_TICKS(2000) || xLastDHTTick == 0) {

    xLastDHTTick = now;

    ...

}

```

Node 4's condition is written with the same 2000 ms bound:

```cpp

if (xLastDHTTick == 0 || now - xLastDHTTick >= pdMS_TO_TICKS(2000)) {

    xLastDHTTick = now;

    ...

}

```

The task period is 1000 ms on both nodes, so the sensor is read on **every

other** sampling cycle. The previous values are retained in between, which is

why the snapshot is copied under the mutex at the top of each iteration rather

than re-initialised.

!!! NOTE

    **Node 4 GPIO 5 is a strapping pin on the ESP32**, and GPIO 5 is also used

    as the CS pin of the internal SPI flash on many ESP32 variants. The

    firmware assigns it to the DHT11 without comment. Boot-strapping behaviour

    and flash-sharing implications depend on the specific ESP32 variant, which

    is **Not verified from the current source**. This is noted here because it

    is the kind of assignment that a reviewer of a design would want to check

    against the actual board, not because any fault has been observed.

## How CIRQUA uses it

### Node 2

```cpp

--8<-- "assets/snippets/node2-sensor-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>Task_Sensors_Node2</code> ·

lines 98–220 · commit <code>db6d9b8</code>
</div>

### Node 4

```cpp

--8<-- "assets/snippets/node4-sensor-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_Sensors_Node4</code> ·

lines 374–712 · commit <code>db6d9b8</code>
</div>

### Validity gating — the two nodes differ

This is the substantive difference between the nodes, and it is deliberate:

| Node | Temperature valid iff | Humidity valid iff |

|---|---|---|

| 2 | `!isnan(t)` | `!isnan(h)` |

| 4 | `!isnan(at)` **and** `-20.0 <= at <= 80.0` | `!isnan(ah)` **and** `0.0 <= ah <= 100.0` |

| 4 SMTP | `!isnan()` only — same as Node 2, **no range gate** | `!isnan()` only |

Node 2 accepts any value the library returns, provided it is not `NAN`. Node 4

additionally rejects values outside physically plausible ranges.

!!! WARNING

    **The SMTP variant uses the weaker, Node 2-style gating.** A

    `Node4_SMTP` deployment therefore has looser ambient validity checking than a

    standard `Node4` deployment. This is a real divergence between the two

    variants, recorded here rather than smoothed over.

Note also what Node 2's rule does *not* cover: `isnan()` catches a failed

read, but it does not catch a device that reports a plausible-looking but wrong

value. Only Node 4's range gate offers any protection against that, and only

outside the -20 to 80 °C and 0 to 100 % bands.

### Node 4 replaces the upstream ambient pair

```cpp

--8<-- "assets/snippets/node4-packet-cleaner.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>cleanUpstreamPacket</code> · lines 936–990 · commit <code>db6d9b8</code>

</div>

### Node 1's alert thresholds come from Node 2

Node 1 holds Node 2's ambient values in its telemetry struct and derives the

LCD status string from them. The relevant thresholds are Node 1 compile-time

constants:

```cpp

const float TEMP_ALERT_TH   = 45.0f;  // Deg C (Overheat threshold)

const float HUMID_ALERT_TH  = 80.0f;  // % RH (Condensation threshold)

```

The Node 1 LCD status precedence is exact:

1. no frame ever received → `WAITING`

2. no receive for `RX_TIMEOUT_MS` (3000 ms) → `ERROR`

3. `ambientTemp >= 45.0` **and** `humidity >= 80.0` → `HOT+HUM`

4. `ambientTemp >= 45.0` → `OVERTEMP`

5. `humidity >= 80.0` → `HI HUMID`

6. `TAV < 5000` **and** `TBV < 500` → `LOW C+F`

7. `TAV < 5000` → `LOW TAV`

8. `TBV < 500` → `LOW TBV`

9. `!node2Health` → `FAULT`

10. otherwise → `NORMAL`

Note the ordering consequence: an over-temperature or high-humidity condition

**masks** a Node 2 sensor fault, because `OVERTEMP` and `HI HUMID` are tested

before `!node2Health`. A node showing `OVERTEMP` is not thereby confirmed to

have healthy sensors.

The humidity threshold is described in the source as a condensation threshold.

High ambient humidity is used here as a **proxy for condensation risk in the

enclosure**, which in turn bears on the [ultrasonic](ultrasonic.md) level

heads and on the 1-Wire temperature runs.

### SMTP e-mail alert thresholds

On `Node4_SMTP`, the same sensor validity flags plus two additional thresholds

define a fault condition:

```text

hasError  <=>  any validity flag is false

           OR   ambTemp > 45

           OR   ambHum  > 90

```

| Trigger | Node 1 LCD | `Node4_SMTP` |

|---|---|---|

| Ambient temperature | `>= 45.0` → `OVERTEMP` | `> 45` → fault e-mail |

| Relative humidity | `>= 80.0` → `HI HUMID` | `> 90` → fault e-mail |

Two differences are worth naming explicitly: the humidity threshold is **80 %

on Node 1 but 90 % on the SMTP variant**, and the SMTP test is strictly greater

(`>`) where the LCD test is greater-or-equal (`>=`). Fault e-mails are rate

limited by a 12-hour error cooldown, so a persistent condition produces one

message, not a stream.

## Calibration

**None.** There is no offset, no gain, no calibration constant and no NVS entry

for either ambient quantity. The DHT11 values are used as read.

| Item | Adjustable? |

|---|---|

| Temperature offset | No — not implemented |

| Humidity offset | No — not implemented |

| Any calibration constant | No — not implemented |

The alert thresholds (`TEMP_ALERT_TH`, `HUMID_ALERT_TH`) are Node 1

compile-time constants, and the SMTP `45` / `90` thresholds are literals in the

alert logic. Both are edit-and-reflash only.

## Expected values and typical ranges

Derivable **strictly from the firmware**:

| Property | Value |

|---|---|

| Units | Ambient temperature in °C, relative humidity in % |

| Read interval | at most one read per **2000 ms**; every other 1000 ms task cycle |

| Node 2 accepted range | unbounded, except that the value must not be `NAN` |

| Node 4 accepted temperature range | **-20.0 to 80.0 °C** |

| Node 4 accepted humidity range | **0.0 to 100.0 %** |

| Node 1 over-temperature threshold | **45.0 °C** |

| Node 1 high-humidity threshold | **80.0 %** |

| SMTP alert thresholds | **> 45 °C**, **> 90 %** |

| Compensation fallback | 25.0 °C — note this is for the *water* [DS18B20](temperature.md), not for the ambient channel |

Reported resolution of the humidity channel, achievable accuracy, and the

stability of the fitted device:

> **Not verified from the current source.** The source gives no numeric

> specification for the sensor and no calibration data is recorded anywhere in

> the repository. No accuracy figure is asserted on this page.

## Failure modes

What the firmware treats as invalid:

* **A failed read**, which the library reports as `NAN`. Both nodes catch this

  for both quantities.

* **Node 4 additionally:** ambient temperature outside **-20 to 80 °C**, or

  humidity outside **0 to 100 %**. `Node4_SMTP` does not apply these gates.

What a field technician should look for:

* **Both `AT` and `AH` invalid together.** The usual signature of a failed read

  — timing, wiring or bus contention on the single-wire line. The two channels

  come from one device, so they fail together.

* **A stable, plausible but wrong value.** A device that has failed towards a

  mid-scale reading passes Node 2's `isnan()` check and, unless the value sits

  outside the bands, Node 4's range gate too. The firmware cannot detect this.

* **A value that tracks the enclosure, not the site.** The DHT11 must be inside

  the enclosure and reading the air there. Mounted near a heatsink, a power

  regulator, a direct sunlit wall or an LCD, it will report the local hot spot.

* **A slow-drifting humidity.** Sensor drift is expected over the life of the

  device and there is no compensation.

* **Ambient values that disagree between Node 1 and Node 4 displays.** Expected

  when the two nodes are in different locations or microclimates — Node 1 shows

  Node 2's values, Node 4 shows its own. It is not automatically a fault, but a

  large divergence is worth investigating.

* **A `OVERTEMP` or `HI HUMID` status with an otherwise healthy node.** Recall

  that these status strings mask the `FAULT` condition in Node 1's precedence.

Field verification note: the debug serial output available from the DHT11

readings is limited; the values are best verified from the LCD and the frame.

## Environmental considerations

* **Placement inside the enclosure.** Ambient readings describe the enclosure,

  not the site, unless the enclosure is well ventilated. Enclosure materials,

  dimensions and ventilation are **Not verified from the current source**.

* **Self-heating.** A DHT11 mounted close to the ESP32, its regulators or its

  LCD will read elevated temperature. Node 1's 45 °C over-temperature threshold

  is intended to catch exactly this.

* **Condensation.** Above roughly 80 % relative humidity, condensation becomes

  likely on a cooler surface. This is what Node 1's humidity threshold is for,

  and it is a genuine risk to the 1-Wire runs and the ultrasonic heads.

* **Sensor warm-up and stabilisation.** Digital humidity sensors of this class

  are slow to stabilise after power-up. The firmware's 2 s pacing helps, but it

  applies no settling period after boot, and the first reading is reported like

  any other.

* **Read pacing.** The 2000 ms floor is a genuine constraint: the sensor cannot

  be read faster regardless of task period, and reading faster would return

  stale or failed data.

* **Wiring run.** A long single-wire run is susceptible to noise and timing

  errors. Cable type, length and routing are **Not verified from the current

  source**, and no schematic exists.

## Limitations

Firmware-level limitations, stated plainly:

* **No calibration of any kind.** No offset, no gain, no NVS entry.

* **Low intrinsic precision.** This is a coarse sensor class. The firmware

  presents the values to two decimal places in the frame, which implies more

  precision than such a device can deliver; the extra digits are formatting, not

  information. Do not treat small variations as meaningful.

* **The two Node 2 channels fail together**, because they come from one device,

  but a fault affecting only one of them would be caught independently — the

  validity flags are separate.

* **Node 2 has no range gate.** Only a `NAN` is caught. Any finite value the

  device returns is accepted, however implausible.

* **`Node4_SMTP` has no range gate either**, despite `Node4` having one. The

  variant therefore has weaker ambient validation than the standard build.

* **Read at most every 2 s, and the previous value is retained in between.**

  Ambient data is effectively 0.5 Hz.

* **No averaging.** Each read is used directly.

* **No hysteresis on the alert thresholds.** A value oscillating around 45 °C or

  80 % will flap between status strings.

* **Alert thresholds mask fault reporting** in Node 1's precedence, as described

  above.

* **The two Node 4 variants use different humidity alert thresholds** — 80 %

  for the Node 1 LCD, 90 % for the SMTP e-mail.

* **Only one ambient pair reaches the controller**, from Node 4, with the

  upstream pair stripped. A consumer has no visibility of Node 2's ambient

  values from the downstream frame.

* **The sensor measures the enclosure air**, and nothing in the firmware or its

  placement is verified against the site conditions it is meant to represent.

* **Strapping pin assignment.** Node 4 assigns GPIO 5 to the DHT11. The

  consequences of that depend on the ESP32 variant, which is

  **Not verified from the current source**.

## Maintenance and replacement

A DHT11 is cheap and quick to replace, and no calibration follows replacement

because none exists. The important work is placement: a replacement sensor

installed in a different position will produce a different baseline, and the

alert thresholds were set against the original location.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md).

Routine checks: [Maintenance](../field-service/maintenance.md).

Startup verification: [Startup Checklist](../field-service/startup-checklist.md).

> **Not verified from the current source.** Fitted part number, cable type,

  length, gauge and connector pinout. No schematic or hardware photograph

  exists in the repository.

## Where it is used

| Node | GPIO | Reading function | Frame field | Validity rule | Displayed at |

|---|---|---|---|---|---|

| 2 | 27 (`PIN_DHT11`) | `Task_Sensors_Node2` | `AT:%.2f`, `AH:%.2f` | `!isnan()` only | Node 1 LCD rows 2 and 3 |

| 4 | 5 (`PIN_N4_DHT11`) | `Task_Sensors_Node4` | LCD only (`AT`, `AH`) | `!isnan()` plus `-20..80 °C` and `0..100 %` | Node 4 LCD rows 2 and 3 |

| 4 SMTP | 5 (`PIN_N4_DHT11`) | `Task_Sensors_Node4` | LCD only; e-mail alert input | `!isnan()` only | Node 4 LCD rows 2 and 3 |

Downstream and derived use:

* Node 1's LCD status precedence — `OVERTEMP` at 45 °C, `HI HUMID` at 80 %,

  `HOT+HUM` when both.

* `Node4_SMTP` fault e-mails at `> 45 °C` or `> 90 %`.

* Node 4 strips the upstream `AT:`/`AH:` tokens so the controller receives only

  Node 4's ambient pair.

Full pin table: [GPIO Map](../hardware/gpio-map.md).

Node detail: [Node 1](../nodes/node1.md), [Node 2](../nodes/node2.md),

[Node 4](../nodes/node4.md), [Node 4 SMTP](../nodes/node4-smtp.md).

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),

branch `main`, commit

[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)

(short `db6d9b8`).

| Snippet | Source path | Symbol | Lines |

|---|---|---|---|

| `node2-sensor-task` | `FreeRTOS_Implementation/Node2/Node2.ino` | `Task_Sensors_Node2` | 98–220 |

| `node4-sensor-task` | `FreeRTOS_Implementation/Node4/Node4.ino` | `Task_Sensors_Node4` | 374–712 |

| `node4-packet-cleaner` | `FreeRTOS_Implementation/Node4/Node4.ino` | `cleanUpstreamPacket` | 936–990 |

| `node1-lcd-task` | `FreeRTOS_Implementation/Node1/Node1.ino` | `Task_LCD_Node1` | 220–310 |

| `node1-pin-definitions` | `FreeRTOS_Implementation/Node1/Node1.ino` | — | 5–35 |

| `node2-pin-definitions` | `FreeRTOS_Implementation/Node2/Node2.ino` | — | 10–32 |

| `node4-pin-definitions` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 10–41 |

| `node4-smtp-alert-logic` | `FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino` | — | 301–350 |

Everything on this page is *firmware implementation* unless explicitly labelled

otherwise. `DHT11` is the name used in the source; the characterisation of the

sensor as slow and comparatively low in accuracy is a generic statement about

this sensor class, and no numeric accuracy specification is asserted, because

none is available from the source.

Related: [Sensors overview](index.md) ·

[Water Temperature](temperature.md) ·

[Node 4 SMTP](../nodes/node4-smtp.md) ·

[Sensor Replacement](../field-service/sensor-replacement.md)


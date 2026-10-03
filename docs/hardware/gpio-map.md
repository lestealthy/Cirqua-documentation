---

title: GPIO Map

description: Authoritative GPIO reference for all four CIRQUA nodes — per-node pin tables, a cross-node table sorted by pin, and the shared-pin hazards.

---

# GPIO Map

This is the **authoritative pin reference** for the CIRQUA cluster. Every value

below is transcribed from the `#define` blocks in the firmware at commit

`db6d9b8`. Check this page before any wiring, rework or bench test.

> **Pin numbers do not carry across nodes.** Each ESP32 is an independent

> microcontroller with its own pin namespace. GPIO 17 on Node 1 has nothing

> whatsoever to do with GPIO 17 on Node 2.

## Per-node tables

### Node 1 — Collection Tank A (TAV)

`FreeRTOS_Implementation/Node1/Node1.ino`, lines 5–35.

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

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| HC-SR04 ultrasonic | N1 ultrasonic TRIG | **2** | out | Trigger pulse, 2–3 µs low / 10 µs high |

| HC-SR04 ultrasonic | N1 ultrasonic ECHO | **17** | in | Echo timeout **30000 µs** |

| UART1 | RX (from Node 2) | **32** | in | 9600 8N1 |

| UART1 | TX (to Node 2) | **33** | out | 9600 8N1 |

| 16×4 I2C LCD | SDA | **21** | — | I2C address `0x27` |

| 16×4 I2C LCD | SCL | **22** | — | I2C address `0x27` |

### Node 2 — Feeding Tank B (TBV)

`FreeRTOS_Implementation/Node2/Node2.ino`, lines 10–32.

```cpp

--8<-- "assets/snippets/node2-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>pin-definitions block</code> ·

lines 10–32 · commit <code>db6d9b8</code>
</div>

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| DS18B20 | Water temperature | **4** | 1-Wire | Non-blocking; `setWaitForConversion(false)` |

| Analog sensor board | DO analog | **34** | in (ADC1) | `ADC1_CH6`; 12-bit; `analogReadResolution(12)` |

| HC-SR04 ultrasonic | N2 ultrasonic TRIG | **16** | out | Trigger pulse |

| HC-SR04 ultrasonic | N2 ultrasonic ECHO | **17** | in | Echo timeout **20000 µs** |

| DHT11 | Ambient temp / humidity | **27** | in | Read at most every 2000 ms |

| UART1 | RX (from Node 1) | **25** | in | 9600 8N1 |

| UART1 | TX (to Node 1) | **26** | out | 9600 8N1 |

| UART2 | RX (from Node 3) | **32** | in | 9600 8N1 |

| UART2 | TX (to Node 3) | **33** | out | 9600 8N1 |

### Node 3 — Flow metering

`FreeRTOS_Implementation/Node3/Node3.ino`, lines 3–13.

```cpp

--8<-- "assets/snippets/node3-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>pin-definitions block</code> ·

lines 3–13 · commit <code>db6d9b8</code>
</div>

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| Flow sensor | Flow sensor pulse | **23** | in | `INPUT_PULLUP`; ISR on **FALLING**; `FLOW_CAL_FACTOR 5.5f` pulses/litre |

| UART1 | RX (from Node 2) | **25** | in | 9600 8N1 |

| UART1 | TX (to Node 2) | **26** | out | 9600 8N1 |

| UART2 | RX (from Node 4) | **32** | in | 9600 8N1 |

| UART2 | TX (to Node 4) | **33** | out | 9600 8N1 |

Node 3 is the only node with **no display** and no I2C bus.

### Node 4 — Effluent (TCV / EV)

`FreeRTOS_Implementation/Node4/Node4.ino`, lines 10–41. The `Node4_SMTP`

sketch uses an **identical pin map**.

```cpp

--8<-- "assets/snippets/node4-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>pin-definitions block</code> ·

lines 10–41 · commit <code>db6d9b8</code>
</div>

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| HC-SR04 ultrasonic | Effluent ultrasonic TRIG | **4** | out | Trigger pulse; timeout **25000 µs** |

| HC-SR04 ultrasonic | Effluent ultrasonic ECHO | **2** | in | Range rejection: `< 0` or `> TANK_HEIGHT + 20` → invalid |

| Analog probe | pH analog | **13** | in (ADC2) | `ADC_11db`, 12-bit |

| Analog probe | Turbidity analog | **14** | in (ADC2) | `ADC_11db`, 12-bit |

| Analog probe | EC analog | **12** | in (ADC2) | `ADC_11db`, 12-bit |

| DS18B20 | Submerged temperature | **27** | 1-Wire | `setResolution(10)`, **blocking** conversion |

| DHT11 | Ambient temp / humidity | **5** | in | Read at most every 2000 ms |

| UART1 | RX (from Node 3) | **25** | in | 9600 8N1 |

| UART1 | TX | **26** | out | 9600 8N1 |

| UART2 | RX (from controller) | **32** | in | 9600 8N1 |

| UART2 | TX (to controller) | **33** | out | 9600 8N1 |

| 16×4 I2C LCD | SDA | **21** | — | I2C address `0x27` |

| 16×4 I2C LCD | SCL | **22** | — | I2C address `0x27` |

## Cross-node GPIO table, sorted by pin number

Read this as *"which nodes mention this pin"*, **not** as *"what this pin does

in the cluster"*. The same pin number carries a completely different function

on different nodes.

| GPIO | Node 1 | Node 2 | Node 3 | Node 4 / SMTP |

|---|---|---|---|---|

| **2** | ultrasonic **TRIG** (out) | — | — | ultrasonic **ECHO** (in) |

| **4** | — | DS18B20 **water temp** (1-Wire) | — | ultrasonic **TRIG** (out) |

| **5** | — | — | — | DHT11 (in) |

| **12** | — | — | — | EC analog (in, ADC2) |

| **13** | — | — | — | pH analog (in, ADC2) |

| **14** | — | — | — | Turbidity analog (in, ADC2) |

| **16** | — | ultrasonic **TRIG** (out) | — | — |

| **17** | ultrasonic **ECHO** (in) | ultrasonic **ECHO** (in) | — | — |

| **21** | LCD **SDA** | — | — | LCD **SDA** |

| **22** | LCD **SCL** | — | — | LCD **SCL** |

| **23** | — | — | Flow **pulse** (in, pull-up, ISR) | — |

| **25** | — | UART1 **RX** ← Node 1 | UART1 **RX** ← Node 2 | UART1 **RX** ← Node 3 |

| **26** | — | UART1 **TX** → Node 1 | UART1 **TX** → Node 2 | UART1 **TX** → Node 3 |

| **27** | — | DHT11 (in) | — | DS18B20 **submerged** (1-Wire) |

| **32** | UART1 **RX** ← Node 2 | UART2 **RX** ← Node 3 | UART2 **RX** ← Node 4 | UART2 **RX** ← controller |

| **33** | UART1 **TX** → Node 2 | UART2 **TX** → Node 3 | UART2 **TX** → Node 4 | UART2 **TX** → controller |

| **34** | — | DO analog (in, ADC1) | — | — |

### Shared-pin facts you must know

These are the specific coincidences that cause miswiring. All are

**Firmware implementation** facts; the hazard statement is

**Engineering interpretation**.

1. **GPIO 17 is ECHO on both Node 1 and Node 2.** Two different ultrasonic

   sensors, on two different controllers, both echo to pin 17. The two boards

   are interchangeable at this pin but must never be joined together.

2. **GPIO 2 is TRIG on Node 1 and ECHO on Node 4.** An **output** on one node

   and an **input** on another. Joining these two by number would drive an

   ESP32 output pin against another ESP32's echo input.

3. **GPIO 4 is DS18B20 1-Wire on Node 2 and ultrasonic TRIG on Node 4.** Again

   a bidirectional 1-Wire data line versus a driven output.

4. **GPIO 27 is DHT11 on Node 2 and submerged DS18B20 on Node 4.** Both are

   single-wire digital sensors but with entirely different protocols and

   electrical expectations.

5. **GPIO 21 and 22 are the LCD I2C bus on both Node 1 and Node 4.** Same bus

   pins, same device address `0x27`. Only one controller per bus.

6. **GPIO 25/26 and 32/33 are the UART pairs on Nodes 2, 3 and 4.** The firmware

   reuses the same two pin *pairs* on every downstream node: 25/26 always

   faces upstream, 32/33 always faces downstream. This is a deliberate and

   elegant pattern — see <a href="../communication/serial-links.html">Serial

   Links</a> — but it means the connector pinout looks identical on three

   different boards while the *peer* at the other end is different.

!!! warning "Pin numbers do not carry across nodes"

    Cross-wiring two nodes' peripherals by number is a real hazard, not a

    theoretical one. GPIO 2 on Node 1 is a driven trigger output; GPIO 2 on

    Node 4 is an echo input. GPIO 4 on Node 2 is a 1-Wire data line; GPIO 4

    on Node 4 is a driven trigger output. **Recommendation:** label every

    inter-node and node-to-sensor wire with both the *node identity* and the

    *signal name*, never with a bare pin number. Before connecting any two

    boards, confirm the node identity first.

## Pin-technology notes

### 1-Wire (DS18B20)

Used on Node 2 (GPIO 4, water temperature) and Node 4 (GPIO 27, submerged

temperature).

* **Firmware implementation.** Node 2 uses `setWaitForConversion(false)` plus

  `requestTemperatures()` each cycle — non-blocking, and the previous

  conversion result is read. Node 4 uses `setResolution(10)` (0.25 °C) with

  `setWaitForConversion(true)` — a **blocking** conversion, roughly 187.5 ms

  at 10-bit resolution.

* **Engineering knowledge.** 1-Wire is a single-wire bus with an open-drain

  data line that requires a pull-up resistor to the logic supply. The DS18B20

  is capable of **parasite power**, in which the data line itself both supplies

  the device and carries the data.

* **Not verified from the current source.** Whether external pull-up resistors

  are fitted, and whether parasite powering is used. The firmware does not

  configure `INPUT_PULLUP` on either 1-Wire pin, which is consistent with

  external pull-ups being present, but does not prove it.

* **Recommendation.** Fit an external pull-up (4.7 kΩ to 3.3 V) unless the

  installed board has been confirmed to include one, and confirm the actual

  wiring at the sensor before power-up.

### ADC1 versus ADC2

* **Firmware implementation.** Node 2's dissolved oxygen input is on GPIO 34,

  which is an **ADC1** channel (`ADC1_CH6`). Node 4's pH, turbidity and EC

  inputs are on GPIO 13, 14 and 12, all **ADC2** channels.

* **Engineering interpretation.** ADC2 on the ESP32 is shared with the

  Wi-Fi and Bluetooth radio path and is not readable while Wi-Fi is active.

  This is why the `Node4_SMTP` variant — the only sketch that enables Wi-Fi —

  is the one place where this distinction becomes operationally significant.

  See <a href="controllers.html">Controllers</a>.

### Input-only and strapping-capable pins

* **Engineering knowledge, not from the source.** On the ESP32, GPIO 34, 35,

  36 and 39 are **input-only**: they have no output driver and no internal

  pull-up or pull-down. Node 2's DO input on GPIO 34 uses it only as an input,

  which is correct. Note that an input-only pin also cannot be used to hold an

  ultrasonic module's TRIG line, so the trigger must be on an output-capable

  pin.

* **Recommendation.** When adding or moving any input, verify it is not one of

  the strapping pins (GPIO 0, 2, 5, 12, 15) unless the pull state during

  reset is compatible with the intended function. GPIO 2 is Node 1's ultrasonic

  trigger, GPIO 5 is Node 4's DHT11, and GPIO 12 is Node 4's EC input — all

  three are strapping pins in the ESP32 family.

## What must still be documented

> **Not verified from the current source.**

>

> * Board-level pin headers actually used on each node.

> * Whether pin multiplexing, level shifters, dividers or buffer stages exist on

>   any node.

> * Physical connector types, keying and pinouts for inter-node cables.

> * Whether the LCD backpack modules carry their own I2C pull-ups (see

>   <a href="wiring.html">Wiring</a>).

## Related pages

* <a href="controllers.html">Controllers</a> — ESP32 capabilities used.

* <a href="wiring.html">Wiring</a> — connection tables derived from this map.

* <a href="../communication/serial-links.html">Serial Links</a> — the UART pair

  assignments in chain order.

* <a href="../field-service/node-identification.html">Node Identification</a> —

  identifying a node in the field before touching a pin.


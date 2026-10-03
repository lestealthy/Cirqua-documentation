---

title: Node 1 (Collection Tank A Level)

description: Field-service manual for CIRQUA Node 1 — the cluster head: TAV ultrasonic level, LCD, and the upstream UART frame originator.

---

# Node 1 (Collection Tank A Level)

## Identity card

--8<-- "assets/generated/node-cards/node1.html"

## Responsibilities

Node 1 does four things, and only these four:

1. **Measures the Collection Tank A (TAV) level** with an HC-SR04 ultrasonic

   head and converts the echo to a volume in litres using the tank cylinder

   geometry. The task runs at 2 Hz (500 ms).

2. **Originates the upstream frame.** Node 1 is the only node that creates a

   frame from nothing. It emits `TAV` and its own health flag every 500 ms.

3. **Merges reverse telemetry.** Node 2 echoes Node 2's own values (DO, water

   temperature, TBV, ambient temperature, ambient humidity) back up the link;

   Node 1 parses that echo and holds it for display.

4. **Renders the local 16×4 I²C LCD**, including the cluster status string.

Node 1 does **not** measure temperature, dissolved oxygen, humidity, flow, pH,

turbidity or conductivity. It only reports what other nodes send it.

### The `* 2.0f` volume doubling — read this before you trust a TAV number

The cylinder formula gives the geometric volume, and then the firmware

**doubles it**:

```cpp

float volumeLiters = (3.14159f * TANK_RADIUS * TANK_RADIUS * waterHeight) / 1000.0f;

currentRead.volumeLiters = (int)(volumeLiters * 2.0f);

```

!!! warning "Empirical compensation factor, not geometry"

    The `* 2.0f` factor is **not derivable** from the cylinder formula. It is a

    hard-coded compensation factor that the authors added empirically — most

    likely to compensate for a systematic under-reading of the ultrasonic head

    (for example displacement by the probe body, foam, or an unaccounted sensor

    offset). The firmware gives no derivation and no comment explaining it.

    **Treat every TAV litre value as uncalibrated until you have calibrated the

    node against a known volume.** See

    [Ultrasonic Calibration](../calibration/ultrasonic.md) and

    [Validation Strategy](../validation/test-strategy.md).

## Inputs

| Sensor | Device | Signal | Notes |

|---|---|---|---|

| Collection Tank A level | [HC-SR04 ultrasonic](../sensors/ultrasonic.md) | `TRIG` GPIO 2, `ECHO` GPIO 17 | 30 ms echo timeout; converted to litres |

| Dissolved oxygen (echoed) | Node 2 probe, displayed only | `DO` field from Node 2 | mg/L |

| Water temperature (echoed) | Node 2 DS18B20, displayed only | `Temp` field from Node 2 | °C |

| Feeding Tank B volume (echoed) | Node 2 HC-SR04, displayed only | `TBV` field from Node 2 | litres |

| Ambient temperature / humidity (echoed) | Node 2 DHT11, displayed only | `AT`, `AH` fields | °C and % RH |

| Serial link to Node 2 | [UART](../communication/serial-links.md) | GPIO 32 RX / GPIO 33 TX | Frame reception and ageing |

## Outputs

| Output | Field | Format | Notes |

|---|---|---|---|

| Upstream UART frame | `TAV` | integer litres | **Doubled value**, see above |

| Upstream UART frame | `node1` | `1` / `0` | `1` = local ultrasonic reading valid |

| Reverse telemetry (received) | `DO`, `Temp`, `TBV`, `AT`, `AH`, `node2` | — | Used for the LCD and status string only |

| Local display | 16×4 I²C LCD, address `0x27` | — | Rendered every 500 ms |

| Debug UART | `Serial`, 115200 baud | text | Fatal trap message only |

Node 1 emits **no e-mail**. E-mail reporting exists only on the

[Node 4 SMTP variant](node4-smtp.md).

Frame actually transmitted:

```text

|TAV:<litres>|node1:<0 or 1>;

```

## Controller

| Property | Value |

|---|---|

| MCU | ESP32 |

| Framework | Arduino ESP32 (`.ino` sketch) |

| RTOS | FreeRTOS with dual-core pinning via `xTaskCreatePinnedToCore` |

| Debug UART | `Serial.begin(115200)` |

| Board variant | > **Not verified from the current source.** |

`setup()` creates the mutexes and the three tasks. `loop()` calls

`vTaskDelete(NULL)` to reclaim the Arduino loop task — **`setup()`/`loop()` are

not the runtime**; all periodic work happens in FreeRTOS tasks.

## GPIO Map

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| N1 ultrasonic | TRIG | 2 | out | 2 µs low, 10 µs high trigger |

| N1 ultrasonic | ECHO | 17 | in | `pulseIn(..., HIGH, 30000)` — 30 ms timeout |

| UART1 | RX (from N2) | 32 | in | Receives the Node 2 echo frame |

| UART1 | TX (to N2) | 33 | out | `PIN_N1_UART_TX 33` |

| LCD (I²C) | SDA | 21 | — | `Wire.begin(21, 22)` |

| LCD (I²C) | SCL | 22 | — | `LiquidCrystal_I2C lcd(0x27, 16, 4)` |

!!! danger "Do not carry pin numbers between nodes"

    Node 1 uses **GPIO 17** for ECHO and **GPIO 2** for TRIG. Node 2 uses

    **GPIO 17** for its own ECHO; on Node 4, **GPIO 2** is the ECHO. Node 1 and

    Node 2 share the number 17 for different physical pins on different boards.

    Always work from the node's own table.

The pin table above is transcribed from the `#define` block:

```cpp

--8<-- "assets/snippets/node1-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>pin assignments, tank geometry, thresholds</code> ·

lines 5–35 · commit <code>db6d9b8</code>
</div>

### Thresholds and geometry

| Constant | Value | Meaning |

|---|---|---|

| `TANK_HEIGHT` | 260.0 cm | Collection Tank A full height |

| `TANK_RADIUS` | 110.0 cm | Collection Tank A radius |

| `TAV_LOW_ALERT_TH` | 5000 L | Low-level alert for Collection Tank A |

| `TBV_LOW_ALERT_TH` | 500 L | Low-level alert for Feeding Tank B (echoed from Node 2) |

| `TEMP_ALERT_TH` | 45.0 °C | Enclosure over-temperature alert |

| `HUMID_ALERT_TH` | 80.0 % RH | Condensation alert |

| `RX_TIMEOUT_MS` | 3000 ms | Silence from Node 2 before the status line shows `ERROR` |

| `TX_INTERVAL_MS` | 500 ms | Upstream transmit interval |

| Ultrasonic speed constant | `0.0343f` cm/µs, halved for the round trip | |

| Cylinder constant | `3.14159f` | |

Node 1 clamps `waterHeight` to `[0, TANK_HEIGHT]` on the low side (it only

clamps below zero; see the snippet). Node 2 additionally clamps above.

## Power

> **Supply voltage and current draw are NOT verified from the current source.**

> There are no power rails, regulator part numbers, current budgets or battery

> topology in the repository. No schematic exists.

What the firmware does imply:

* The controller is an ESP32, which operates from a **3.3 V logic domain**; the

  ultrasonic, LCD and UART pins are all 3.3 V logic.

* The ultrasonic trigger sequence is generated by GPIO, and the LCD runs over

  I²C at 3.3 V logic levels.

Nothing in the source states the rail voltage for the HC-SR04, the LCD

backlight, or the node as a whole. Do not assume 5 V for the ultrasonic module.

See [Power](../hardware/power.md).

## Communication

| Aspect | Detail |

|---|---|

| Upstream | Node 2, on UART1 (GPIO 32 RX) |

| Downstream | **None.** Node 1 has no downstream link; it only originates |

| Protocol | Delimiter-separated ASCII key/value |

| Baud | 9600, `SERIAL_8N1` (`INTERNODE_BAUD`) |

| Frame | `\|TAV:%d\|node1:%d;\n` — integer litres |

| Reverse frame received | `\|DO:%.2f\|Temp:%.2f\|TBV:%.2f\|AT:%.2f\|AH:%.2f\|node2:%d;\n` |

| Timing / cadence | Transmit every `TX_INTERVAL_MS` = 500 ms; RX task polls with a 1 ms delay; sensors 500 ms; LCD 500 ms |

| Receive buffer | Arduino `String`, `reserve(256)`, reset when length exceeds 250 |

| Integrity | **No checksum, no CRC, no sequence number, no acknowledgement, no retry.** Node 1 accepts the echo if all six expected keys are present |

| Ageing | `g_lastNode2Rx` updated only when all six fields are non-empty; older than `RX_TIMEOUT_MS` → status `ERROR` |

### Failure behaviour

* **No echo from Node 2.** After 3000 ms the LCD status line reads `ERROR`

  (unless the node has never received a frame at all, in which case it reads

  `WAITING`).

* **Local ultrasonic timeout.** `pulseIn` returns 0 after 30 ms; `isValid` is

  set false and `node1` is emitted as `0`. The last volume reading is *not*

  cleared — the transmitted `TAV` value becomes `0` only because `localSnap`

  is initialised to `{0, false}` and only overwritten when the mutex is taken

  *and* a reading exists.

* **Buffer overflow.** The RX buffer index is reset and the frame is dropped.

* **Mutex timeout.** 50 ms for the sensor commit, 10 ms for the transmit

  snapshot, 20 ms for the LCD snapshot. A timeout means a **stale snapshot is

  used**, not a reset.

* **Mutex or task creation failure.** `systemFatalTrap()` prints

  `[FATAL ERROR] System Initialization Failed: <name>. Halted.` on the debug

  UART and then delays forever (`vTaskDelay`, not a busy loop).

## RTOS Architecture

| Task name | Function | Stack | Priority | Core | Period |

|---|---|---|---|---|---|

| `N1_Sensors` | `Task_Sensors_Node1` | 3072 | 2 | 1 | 500 ms (`vTaskDelayUntil`) |

| `N1_UART` | `Task_UART_Node1` | 3072 | 3 | 0 | 1 ms loop |

| `N1_LCD` | `Task_LCD_Node1` | 3072 | 1 | 1 | 500 ms (`vTaskDelayUntil`) |

Mutexes: **`xLocalDataMutex`** (protects `g_localSensors`) and

**`xNode2DataMutex`** (protects `g_node2Data` and `g_lastNode2Rx`). Both are

created with `xSemaphoreCreateMutex()`; failure calls `systemFatalTrap`.

Shared data:

| Object | Protected by | Contents |

|---|---|---|

| `g_localSensors` | `xLocalDataMutex` | `volumeLiters`, `isValid` |

| `g_node2Data` | `xNode2DataMutex` | DO, water temp, TBV, ambient temp, humidity, `node2Health`, `packetValid` |

| `g_lastNode2Rx` | `xNode2DataMutex` | `millis()` of the last complete echo frame |

UART task, core 0:

```cpp

--8<-- "assets/snippets/node1-uart-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>Task_UART_Node1</code> ·

lines 161–204 · commit <code>db6d9b8</code>
</div>

Sensor task, core 1 — the source of the `* 2.0f` doubling:

```cpp

--8<-- "assets/snippets/node1-ultrasonic-measurement.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>Task_Sensors_Node1</code> ·

lines 77–116 · commit <code>db6d9b8</code>
</div>

## Firmware

Two functions do the real work on this node.

**Frame field extraction** — a `String` helper that finds `|key:` and reads to

the next `|` or `;`. This is the entire parsing strategy; there is no tokeniser

and no schema:

```cpp

--8<-- "assets/snippets/node1-frame-parser.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>getFieldFromFrame</code> ·

lines 120–132 · commit <code>db6d9b8</code>
</div>

**Echo processing** — note that each field is only applied when it is non-empty,

so a partially truncated frame updates the fields it does contain but does not

set `packetValid` or refresh `g_lastNode2Rx`:

```cpp

--8<-- "assets/snippets/node1-packet-processing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>processNode2Packet</code> ·

lines 133–157 · commit <code>db6d9b8</code>
</div>

## Sensors

| Page | Sensor | Used by Node 1 |

|---|---|---|

| [Ultrasonic (HC-SR04)](../sensors/ultrasonic.md) | HC-SR04 | **Yes** — TAV measurement |

| [Water Temperature (DS18B20)](../sensors/temperature.md) | DS18B20 | No — value is echoed from Node 2 |

| [Dissolved Oxygen](../sensors/dissolved-oxygen.md) | Analogue DO probe | No — echoed from Node 2 |

| [Flow](../sensors/flow.md) | Pulse flow meter | No |

| [Humidity / Ambient (DHT11)](../sensors/humidity.md) | DHT11 | No — echoed from Node 2 |

| [pH](../sensors/ph.md) | Analogue pH probe | No |

| [Turbidity](../sensors/turbidity.md) | SEN0189 / DFRobot analogue | No |

| [Conductivity (EC)](../sensors/conductivity.md) | Analogue EC probe | No |

## Calibration

Node 1 has **no calibration console and no non-volatile calibration store**. The

only calibration-sensitive quantity is the TAV volume, and it is the geometry

constants plus the hard-coded doubling factor.

| Item | Where | Value |

|---|---|---|

| Tank height | `Node1.ino` | `TANK_HEIGHT = 260.0f` cm |

| Tank radius | `Node1.ino` | `TANK_RADIUS = 110.0f` cm |

| Cylinder constant | `Node1.ino` | `3.14159f` |

| Compensation factor | `Node1.ino` | `* 2.0f` — **empirical, undocumented, requires calibration** |

| Echo timeout | `Node1.ino` | 30000 µs |

Procedures:

* [Ultrasonic Calibration](../calibration/ultrasonic.md) — how to establish the

  true height-to-volume relationship and how to justify or remove the doubling

  factor.

* [Dissolved Oxygen Calibration](../calibration/dissolved-oxygen.md) — not

  applicable to this node; the DO probe lives on Node 2.

!!! note "Recommendation"

    If you need a trustworthy TAV litre value in the field, measure the tank's

    true cross-section rather than trusting `TANK_RADIUS = 110.0`. The tank

    geometry was never verified against a physical tank, and the `* 2.0f` factor

    suggests the original values did not agree with reality.

## Display / UI

16×4 character LCD over I²C at address `0x27`, refreshed every 500 ms by the

`N1_LCD` task (core 1). Each line is truncated and space-padded to 16

characters by `printLCDLine()`.

```text

Line 1  C<TAV>L F<TBV>L

Line 2  DO<mg/l> T<Temp>C

Line 3  AT<AT>C H<AH>%

Line 4  STATUS: <status>

```

| Line | Format | Placeholder behaviour |

|---|---|---|

| 1 | `C{TAV}L F{TBV}L` | `----` shown after `F` when `TBV < 0` (i.e. never received) |

| 2 | `DO{mg/l} T{Temp}C` | `--` when DO `< 0`; `--` when water temp `<= -100.0`; the **decimal point is replaced by a comma** |

| 3 | `AT{AT}C H{AH}%` | `--` when ambient temp `<= -100.0`; `--` when humidity `< 0`; humidity printed with 0 decimals; decimal point replaced by a comma |

| 4 | `STATUS: {status}` | see precedence below |

Note the asymmetry in line 1: the TAV value is always printed from the last

ultrasonic result (or `0`), while the TBV value is only printed when a

non-negative number has been received.

### Status string precedence (exact order)

This is the precedence implemented in `Task_LCD_Node1`. The **first** matching

condition wins:

| Order | Condition | Displayed |

|---|---|---|

| 1 | `lastRx == 0` — no frame ever received | `STATUS: WAITING` |

| 2 | `millis() - lastRx > 3000` (`RX_TIMEOUT_MS`) | `STATUS: ERROR` |

| 3 | `ambientTemp >= 45.0` **and** `humidity >= 80.0` | `STATUS: HOT+HUM` |

| 4 | `ambientTemp >= 45.0` | `STATUS: OVERTEMP` |

| 5 | `humidity >= 80.0` | `STATUS: HI HUMID` |

| 6 | `TAV < 5000` **and** `TBV < 500` | `STATUS: LOW C+F` |

| 7 | `TAV < 5000` | `STATUS: LOW TAV` |

| 8 | `TBV < 500` | `STATUS: LOW TBV` |

| 9 | `!node2Health` | `STATUS: FAULT` |

| 10 | otherwise | `STATUS: NORMAL` |

!!! important "Read the precedence in order"

    * `WAITING` beats everything, including a dead link: if the node has never

      received a complete echo it says `WAITING`, not `ERROR`.

    * `ERROR` beats every environmental and volume alarm. A link problem hides

      the reason you would be reading the display in the first place.

    * The two low-volume tests are **gated on validity**: `lowTav` requires

      `isValid`, and `lowTbv` requires `TBV >= 0`. An empty tank with no

      ultrasonic reading will *not* raise `LOW TAV`.

    * `FAULT` (Node 2 reported unhealthy) is the **last** check, so it is only

      visible once temperature, humidity and both volumes are within limits.

### LCD task source

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

## Troubleshooting

| Symptom | Likely cause | Check | Action |

|---|---|---|---|

| LCD blank, backlight off | LCD not initialised, I²C wiring, or wrong LCD address | Check SDA = GPIO 21, SCL = GPIO 22; confirm the display's actual address is `0x27` | Re-seat the I²C cable; if the module answers at another address, the sketch must be changed — the address is hard-coded |

| `STATUS: WAITING` permanently | Node 2 is not echoing, or the echo never completes | Check TX 33 → Node 2 RX 25 and Node 2 TX 26 → RX 32; confirm ground continuity | Restore the link. `WAITING` means *no complete frame ever arrived*, so check both directions and the baud (9600) |

| `STATUS: ERROR` after a working period | Link silent for > 3 s | Look for a reboot or power loss on Node 2; check the cable | Restore the link; no node-1 action is needed |

| `STATUS: LOW TAV` when the tank is clearly full | `* 2.0f` doubling, wrong tank radius, ultrasonic offset | Compare the displayed litres with a known volume | Recalibrate; see [Ultrasonic Calibration](../calibration/ultrasonic.md) |

| `STATUS: LOW TAV` but line 1 shows `0L` | Ultrasonic never returns a valid echo; `pulseIn` timed out at 30 ms | Check TRIG (GPIO 2) and ECHO (GPIO 17) wiring; look for condensation on the transducer face | Clean the transducer; verify ECHO is not floating; check the 5 V supply to the HC-SR04 |

| `TAV` never changes | Sensor stuck, or the display is showing a stale value because the mutex timed out | Watch line 1 while filling the tank | Check the ultrasonic head physically |

| `----` after `F` on line 1 | Node 2's `TBV` has never arrived | Node 2 page: is Node 2's own ultrasonic working? | Fix Node 2, not Node 1 |

| `--` on line 2/3 values | Node 2's DO, water temp, ambient temp or humidity is invalid (`node2:0`) | Read Node 2's own sensors | Repair Node 2; Node 1 has no fallback |

| `STATUS: FAULT` | Node 2 reports `node2:0`, i.e. one of its five sensors is invalid | Diagnose on Node 2 | Repair Node 2 |

| `STATUS: OVERTEMP` / `HOT+HUM` | Ambient readings from Node 2's DHT11 exceed 45 °C / 80 % | Compare with a handheld meter at the enclosure | Ventilate or relocate the Node 2 enclosure |

| Debug UART prints `[FATAL ERROR] … Halted.` | Mutex or task creation failed | — | The node is dead by design; check for stack/task exhaustion, then reflash |

| Everything looks fine but the controller sees no data | Node 2 is not forwarding downstream | Follow the chain: [Node 2](node2.md), [Node 3](node3.md) | Work downstream link by link |

## Validation

Observable behaviour you can actually check:

1. **LCD text.** Power the node and confirm:

   * Line 1 begins `C` and ends `L`; line 4 begins `STATUS: `.

   * A fresh boot shows `STATUS: WAITING` until Node 2's echo arrives, then

     `STATUS: NORMAL` (or another state).

   * If you unplug the Node 2 link, line 4 changes to `STATUS: ERROR` within

     about 3 s. That confirms both the RX path and the timeout logic.

2. **Serial debug output.** Connect the debug UART at **115200 baud**. The node

   is silent during normal operation; the only expected print is the fatal trap

   message `[FATAL ERROR] System Initialization Failed: <name>. Halted.`

3. **Link capture on Node 2's RX.** At 9600 baud you should see, every 500 ms:

   ```text

   |TAV:NNNNN|node1:1;

   ```

   The value must change when you move the water surface, and `node1` must be

   `0` while the transducer is blocked or disconnected.

4. **Volume plausibility.** Compute the expected geometric volume

   `π × 110² × (260 − distance) / 1000` from a measured distance, multiply by

   2, and compare with the displayed litres. Record the ratio; that ratio *is*

   the effective compensation and belongs in

   [Ultrasonic Calibration](../calibration/ultrasonic.md).

5. **Cross-node consistency.** The `TBV`, `DO`, `Temp`, `AT` and `AH` values on

   Node 1's LCD must match what [Node 2](node2.md) is measuring within one

   500 ms LCD refresh. If they do not, the echo path is broken.

## Source

* Firmware file at the pinned commit:

  [`FreeRTOS_Implementation/Node1/Node1.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino)

* Directory listing:

  [`FreeRTOS_Implementation/Node1`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1)

* Extracted snippets used on this page:

  [node1-pin-definitions](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L5-L35),

  [node1-ultrasonic-measurement](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L77-L116),

  [node1-frame-parser](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L120-L132),

  [node1-packet-processing](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L133-L157),

  [node1-uart-task](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L161-L204),

  [node1-lcd-task](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L220-L310)

* Commit: [`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/commit/db6d9b896341a9c7d8fd01913e854b663c110d55)

* Firmware Source Map: [../firmware/source-map.html](../firmware/source-map.md)

* Related: [Node 2](node2.md) ·

  [Serial Links](../communication/serial-links.md) ·

  [Message Format](../communication/message-format.md) ·

  [RTOS Tasks](../rtos/tasks.md) ·

  [GPIO Map](../hardware/gpio-map.md)
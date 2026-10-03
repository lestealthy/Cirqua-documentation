---

title: Node 2 (Router and Water Quality Probe Node)

description: Field-service manual for CIRQUA Node 2 — the cluster router: dissolved oxygen, water temperature, TBV level, ambient DHT11.

---

# Node 2 (Router and Water Quality Probe Node)

## Identity card

--8<-- "assets/generated/node-cards/node2.html"


<div class="cirqua-photo-slot">
  <span class="cirqua-photo-slot__label">Photo required</span>
  <p class="cirqua-photo-slot__title">Node 2 — Feeding Tank B and water probes — no photograph on record</p>
  <p class="cirqua-photo-slot__note">
    Photograph the node, the dissolved oxygen module, the DS18B20 and DHT11 positions, and the two UART links leaving the enclosure.
    No photograph of CIRQUA hardware was found in the firmware repository or
    the local workspace, so this slot is intentionally empty. A stock or
    generated image is not used, because that would misrepresent the hardware.
  </p>
</div>

## Responsibilities

Node 2 is the **router** of the cluster. It has four duties:

1. **Measures four things** at 1 Hz: DS18B20 water temperature, analogue

   dissolved oxygen, HC-SR04 level in Feeding Tank B (TBV), and DHT11 enclosure

   ambient temperature and humidity (the DHT11 is paced to at most one read per

   2000 ms).

2. **Consolidates** Node 1's upstream frame (`TAV`, `node1`) with its own five

   measurements into a single downstream frame, and sends that to Node 3 every

   50 ms.

3. **Echoes its own values back to Node 1** every 50 ms so that Node 1 can

   display them. The echo deliberately carries *only* Node 2's fields — no `TAV`.

4. **Computes its own health flag** (`node2`) as the logical AND of five

   per-sensor validity flags.

Node 2 has **no LCD and no downstream acknowledgement logic**. If the downstream

link is broken, Node 2 keeps sending into an open UART.

### Observed inconsistency: the `SerialNode3` parser is dead code in practice

Node 2 opens a **second** UART, `SerialNode3` on UART2 (GPIO 32 RX / 33 TX), and

contains a parser `parseNode3ReversePacket()` that looks for `|FR:` and

`|node3:`:

```cpp

--8<-- "assets/snippets/node2-parse-node3.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>parseNode3ReversePacket</code> ·

lines 240–254 · commit <code>db6d9b8</code>
</div>

!!! warning "Documented as observed — do not assume reverse flow works"

    * The parser requires a field named **`FR:`**. Node 3's real emitted flow key

      is **`FLM:`** (the source comment reads

      "Standardized key name FLM for downstream controller compatibility").

    * Node 3 **sends only downstream**. It writes nothing back up the chain towards

      Node 2; its only downstream write is to Node 4.

    * Therefore `parseNode3ReversePacket()` can never succeed with a real Node 3

      on the wire: `g_n3Data` stays at its initial `{ 0.0f, false, false }` and

      is never read by the routing task.

    **Engineering interpretation:** this is dead code left over from an earlier

    design where Node 3 sent reverse flow telemetry upstream under the key `FR`.

    Do not rely on `g_n3Data` for diagnosis. If you need reverse flow telemetry,

    the firmware would have to be changed on both Node 2 and Node 3; nothing in

    the current source provides it.

## Inputs

| Sensor | Device | Signal | Notes |

|---|---|---|---|

| Water temperature | [DS18B20](../sensors/temperature.md) | 1-Wire, GPIO 4 | **Non-blocking** conversion |

| Dissolved oxygen | [Analogue DO probe](../sensors/dissolved-oxygen.md) | ADC, GPIO 34 (ADC1) | mg/L, temperature-compensated |

| Feeding Tank B level | [HC-SR04 ultrasonic](../sensors/ultrasonic.md) | TRIG GPIO 16, ECHO GPIO 17 | 20 ms timeout |

| Ambient temperature / humidity | [DHT11](../sensors/humidity.md) | GPIO 27 | Read at most every 2000 ms |

| Upstream frame | [UART1](../communication/serial-links.md) | GPIO 25 RX | `\|TAV:`, `\|node1:` |

| Downstream link | [UART2](../communication/serial-links.md) | GPIO 32 RX / 33 TX | TX to Node 3; RX parser unused in practice |

## Outputs

| Output | Field | Format | Notes |

|---|---|---|---|

| Downstream to Node 3 | `TAV` | `%.2f` | Passed through from Node 1, or `0.00` if no valid Node 1 frame |

| Downstream to Node 3 | `node1` | `1` / `0` | `1` only if Node 1's frame parsed **and** `node1:1` |

| Downstream to Node 3 | `DO` | `%.2f` | mg/L, or `0.00` if invalid |

| Downstream to Node 3 | `Temp` | `%.2f` | °C, or `0.00` if invalid |

| Downstream to Node 3 | `TBV` | `%.2f` | litres, or `0.00` if invalid |

| Downstream to Node 3 | `AT` | `%.2f` | °C, or `0.00` if invalid |

| Downstream to Node 3 | `AH` | `%.2f` | % RH, or `0.00` if invalid |

| Downstream to Node 3 | `node2` | `1` / `0` | AND of all five local validity flags |

| Echo upstream to Node 1 | `DO`, `Temp`, `TBV`, `AT`, `AH`, `node2` | `%.2f` | No `TAV`; drives the Node 1 LCD |

| Local display | **None** | — | Node 2 has no LCD |

| E-mail | **None** | — | E-mail exists only on [Node 4 SMTP](node4-smtp.md) |

Downstream frame:

```text

|TAV:%.2f|node1:%d|DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;

```

Echo frame to Node 1:

```text

|DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;

```

## Controller

| Property | Value |

|---|---|

| MCU | ESP32 |

| Framework | Arduino ESP32 (`.ino` sketch) |

| RTOS | FreeRTOS, `xTaskCreatePinnedToCore` |

| Debug UART | `Serial.begin(115200)` |

| Board variant | > **Not verified from the current source.** |

## GPIO Map

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| DS18B20 | water temperature 1-Wire | 4 | 1-Wire | `setWaitForConversion(false)` |

| DO probe | analogue output | 34 | in (ADC1) | `analogReadResolution(12)`; input-only pin |

| N2 ultrasonic | TRIG | 16 | out | 2 µs low, 10 µs high |

| N2 ultrasonic | ECHO | 17 | in | `pulseIn(..., HIGH, 20000)` — 20 ms timeout |

| DHT11 | data | 27 | in | `DHTTYPE DHT11` |

| UART1 | RX (from N1) | 25 | in | 9600 8N1 |

| UART1 | TX (to N1) | 26 | out | Echo frame |

| UART2 | RX (from N3) | 32 | in | Parser present but unused in practice |

| UART2 | TX (to N3) | 33 | out | Consolidated downstream frame |

!!! warning "GPIO 17 appears on both Node 1 and Node 2"

    Node 1's ECHO is GPIO 17 and Node 2's ECHO is **also** GPIO 17, on different

    boards. Do not use a Node 1 pinout when wiring a Node 2 (or vice versa).

```cpp

--8<-- "assets/snippets/node2-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>pin assignments, DO constants, tank geometry</code> ·

lines 10–32 · commit <code>db6d9b8</code>
</div>

### Constants and geometry

| Constant | Value | Meaning |

|---|---|---|

| `TANK_HEIGHT` | 178.0 cm | Feeding Tank B full height |

| `TANK_RADIUS` | 59.5 cm | Feeding Tank B radius |

| Ultrasonic timeout | 20000 µs | ≈ 3.4 m of range per the source comment |

| `VREF` | 5000.0 mV | DO ADC reference |

| `ADC_RESOLUTION` | 4095.0 | 12-bit ADC |

| `TWO_POINT_VOLTAGE` | 1000.0 mV | DO calibration voltage threshold |

| `SATURATION_DO_25C` | 8.26 mg/L | Saturation dissolved oxygen at 25 °C |

## Power

> **Supply voltage and current draw are NOT verified from the current source.**

> No regulator, rail, current budget or battery topology appears in the

> repository, and no schematic exists.

What the source does state:

* The DO ADC reference comment reads

  `#define VREF 5000.0f // ADC Reference Voltage (mV) on 3.3V ESP32` — the

  firmware assumes a **3.3 V ESP32 logic domain** and models the probe's output

  against a 5000 mV full-scale reference.

* The DS18B20, DHT11, HC-SR04 and both UART links are all 3.3 V logic

  peripherals from the controller's point of view.

The DO conversion chain is worth reading carefully in the field, because it is

the one place where the code assumes a 0–5 V probe output scaled through a 3.3 V

ADC span:

```text

doVoltage (mV) = (raw / 4095.0) × 5000.0

```

See [Power](../hardware/power.md).

## Communication

| Aspect | Detail |

|---|---|

| Upstream | Node 1, UART1, GPIO 25 RX |

| Downstream | Node 3, UART2, GPIO 33 TX (TX only in practice; RX parser unused) |

| Protocol | Delimiter-separated ASCII key/value |

| Baud | 9600, `SERIAL_8N1` (`INTERNODE_BAUD`) |

| Frame | See Outputs above |

| Timing / cadence | Sensor task 1000 ms; UART task 50 ms (20 Hz polling); DHT11 paced to ≥ 2000 ms; DS18B20 requested every cycle, read non-blocking |

| Receive buffers | `char rxBufferN1[128]` and `char rxBufferN3[128]`, one per link |

| Frame detection | Character `;` terminates a frame; `\n` and `\r` are skipped |

| Send buffers | `char downstreamPayload[256]`, `char echoToN1[256]` |

| Integrity | **No checksum, no CRC, no sequence number, no acknowledgement, no retry.** Node 1's frame is validated structurally by the presence of `\|TAV:` and `\|node1:` |

### Failure behaviour

* **No Node 1 frame.** `n1Snap.isValid` stays false; `TAV` is sent as `0.00` and

  `node1` as `0`. Node 2 keeps sending at 20 Hz.

* **Sensor invalid.** The corresponding field is sent as `0.00` and its validity

  flag is false; if any of the five is false then `node2` is `0`. Node 1 shows

  `STATUS: FAULT`.

* **Dissolved oxygen invalid** when `rawDO == 0`. There is **no range gating** on

  Node 2's DO value beyond that — see [Dissolved Oxygen](../sensors/dissolved-oxygen.md).

* **DHT11 invalid** only when `isnan()` is true. Node 2 applies **no** ambient

  range gate; Node 4 does. This is a real behavioural difference between nodes.

* **Buffer overflow.** The RX index resets to 0 and the frame is dropped. At

  128 bytes, a full-length downstream frame is comfortably inside the limit, so

  overflow should not occur in normal operation.

* **Mutex timeout.** 50 ms for the sensor commit, 20 ms for the UART snapshots.

  A timeout means a **stale snapshot** is used, not a reset.

* **Mutex or task creation failure.** `systemFatalTrap()` prints

  `[FATAL ERROR] Node 2 Task Failed: <name>` and then delays forever.

## RTOS Architecture

| Task name | Function | Stack | Priority | Core | Period |

|---|---|---|---|---|---|

| `N2_Sensors` | `Task_Sensors_Node2` | 4096 | 2 | 1 | 1000 ms (`vTaskDelayUntil`) |

| `N2_UART` | `Task_UART_Node2` | 4096 | 3 | 0 | 50 ms (`vTaskDelayUntil`) |

Mutexes — **three** on this node:

| Mutex | Protects | Timeout used |

|---|---|---|

| `xSensorsMutex` | `g_n2Sensors` (all local sensor values and validity flags) | 50 ms commit, 20 ms read |

| `xN1DataMutex` | `g_n1Data` (TAV, `node1Status`, `isValid`) | 20 ms |

| `xN3DataMutex` | `g_n3Data` (flow, `node3Status`, `isValid`) | 20 ms |

`g_n3Data` is written but never read — see the inconsistency note in

Responsibilities.

The sensor task reads the current state under `xSensorsMutex` at the top of each

cycle, which is what preserves previously valid values across a cycle in which

one sensor fails:

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

The routing task shows the consolidation and the health AND:

```cpp

--8<-- "assets/snippets/node2-uart-routing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>Task_UART_Node2</code> ·

lines 259–370 · commit <code>db6d9b8</code>
</div>

## Firmware

The upstream parser is the mirror image of Node 1's — `strstr` for the two

expected keys, `sscanf` for the values:

```cpp

--8<-- "assets/snippets/node2-parse-node1.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>parseNode1Packet</code> ·

lines 225–239 · commit <code>db6d9b8</code>
</div>

Node 2's own validity rules, from the sensor task above:

| Measurement | Valid when | Unit |

|---|---|---|

| Water temperature | `!= DEVICE_DISCONNECTED_C` and `-55 < T < 125` | °C |

| Dissolved oxygen | `rawDO != 0` | mg/L |

| TBV volume | `pulseIn` returned > 0 after the 20 ms timeout | litres |

| Ambient temp / humidity | `!isnan()` only — **no range gate** | °C, % RH |

The dissolved oxygen conversion, exactly as implemented:

```text

doVoltage    = (rawDO / 4095.0) × 5000.0            [mV]

compFactor   = 1.0 + (T − 25.0) × (−0.02)          [T = water temp, else 25.0]

DO           = (doVoltage / 1000.0) × 8.26 × compFactor,  clamped ≥ 0   [mg/L]

```

Node 1's parser and Node 2's health flag are what make `STATUS: FAULT` on

Node 1 possible; there is no other health path in the cluster.

## Sensors

| Page | Sensor | Used by Node 2 |

|---|---|---|

| [Water Temperature (DS18B20)](../sensors/temperature.md) | DS18B20, 1-Wire | **Yes** — non-blocking |

| [Dissolved Oxygen](../sensors/dissolved-oxygen.md) | Analogue probe, ADC1 | **Yes** |

| [Ultrasonic (HC-SR04)](../sensors/ultrasonic.md) | HC-SR04 | **Yes** — TBV |

| [Humidity / Ambient (DHT11)](../sensors/humidity.md) | DHT11 | **Yes** |

| [Flow](../sensors/flow.md) | Pulse flow meter | No — flow is measured on Node 3 |

| [pH](../sensors/ph.md) | Analogue pH probe | No |

| [Turbidity](../sensors/turbidity.md) | Analogue turbidity | No |

| [Conductivity (EC)](../sensors/conductivity.md) | Analogue EC probe | No |

### The DS18B20 is deliberately non-blocking here

```cpp

sensorsN2.setWaitForConversion(false);

```

Node 2 calls `requestTemperatures()` and then reads on the *next* cycle, so the

reading returned in cycle *n* was started in cycle *n−1*. Node 4 uses the

opposite, blocking approach. If you swap the two firmwares, the timing

behaviour changes — see [Temperature](../sensors/temperature.md).

## Calibration

| Item | Where | Value / rule |

|---|---|---|

| `VREF` | `Node2.ino` | 5000.0 mV |

| `ADC_RESOLUTION` | `Node2.ino` | 4095.0 |

| `TWO_POINT_VOLTAGE` | `Node2.ino` | 1000.0 mV |

| `SATURATION_DO_25C` | `Node2.ino` | 8.26 mg/L at 25 °C |

| Temperature compensation | `Node2.ino` | `1.0 + (T − 25.0) × (−0.02)` |

| `TANK_HEIGHT` / `TANK_RADIUS` | `Node2.ino` | 178.0 cm / 59.5 cm |

| Ultrasonic timeout | `Node2.ino` | 20000 µs |

| DHT11 read interval | `Node2.ino` | ≥ 2000 ms |

**There is no calibration console and no NVS storage on Node 2.** Every constant

above is compiled in and can only be changed by editing and reflashing the

sketch.

Procedures:

* [Dissolved Oxygen Calibration](../calibration/dissolved-oxygen.md) — the

  two-point 1000 mV / 8.26 mg/L model and its temperature compensation.

* [Ultrasonic Calibration](../calibration/ultrasonic.md) — the TBV cylinder

  volume.

!!! note "Node 2 vs Node 4 TBV geometry"

    Node 2 (TBV) and Node 4 (TCV / EV) use **identical** constants

    (178.0 cm × 59.5 cm). Node 1 uses a different tank entirely

    (260.0 cm × 110.0 cm) **and** applies the `* 2.0f` doubling. Node 4's

    ultrasonic task additionally rejects distances outside

    `[0, TANK_HEIGHT + 20]`; Node 2 does not.

## Display / UI

**Node 2 has no LCD.** It emits no display output of any kind.

The only way to see Node 2's values is:

* on [Node 1's LCD](node1.md), lines 2 and 3, in the echo frame; or

* on the downstream controller at the end of the chain; or

* on the debug UART at 115200 baud — but note that Node 2 prints **nothing**

  during normal operation. The only debug output is the fatal trap message.

Because there is no local display, the field diagnostic sequence is: read the

values on Node 1, then decide whether the fault is upstream (Node 1's `TAV`) or

local to Node 2.

## Troubleshooting

| Symptom | Likely cause | Check | Action |

|---|---|---|---|

| Node 1 shows `STATUS: WAITING` | Node 2 is not echoing | TX 26 → Node 1 RX 32; ground continuity | Restore the link |

| Node 1 shows `STATUS: ERROR` after working | Node 2 stopped echoing | Is Node 2 alive? Check its debug UART for `[FATAL ERROR]` | Power-cycle Node 2, then re-check the cable |

| Node 1 shows `STATUS: FAULT` | `node2:0` — one of Node 2's five sensors is invalid | Compare Node 1's line 2 and line 3 for `0.00`-style or `--` values | Identify which sensor is reading zero or NaN and repair that sensor |

| `TBV` on Node 1 reads `0.00` or the field looks wrong | Node 2's ultrasonic failed | Check TRIG GPIO 16 and ECHO GPIO 17; clean the transducer | Repair the ultrasonic head |

| `TBV` reads a plausible-looking but wrong volume | Tank geometry never verified against the physical tank | Measure the real tank diameter and height | Recalibrate — see [Ultrasonic Calibration](../calibration/ultrasonic.md) |

| `DO` reads exactly `0.00` on the downstream frame | `rawDO == 0`, or a negative result clamped to 0 | Measure the probe output voltage; check the probe's supply | Check wiring on GPIO 34 and the probe's own excitation |

| `DO` drifts with temperature | The compensation factor is applied against the DS18B20 reading; if that probe is invalid, 25.0 °C is assumed | Check the DS18B20 on GPIO 4 reads a sane temperature | Repair the 1-Wire probe so compensation works |

| `DO` is implausibly high | `VREF = 50000` model applied to a probe powered/outputs referenced to 3.3 V | Measure the probe output with a meter | See [Dissolved Oxygen](../sensors/dissolved-oxygen.md); the constant may need to match your probe |

| Water temp reads `0.00` | DS18B20 not found or out of range | Check 1-Wire on GPIO 4, and that the probe is not `DEVICE_DISCONNECTED_C` | Check the data pin pull-up and probe connection |

| `AT` / `AH` stuck at the last good value, or `0.00` | DHT11 read failed (`isnan`) | DHT11 on GPIO 27; note it is read only every ≥ 2000 ms | Replace the DHT11 if it repeatedly returns NaN |

| Ambient values look impossible (e.g. 200 °C) and are still transmitted | Node 2 applies **no** range gate on the DHT11 | Compare with a handheld meter | Treat as a sensor fault; the firmware will not flag it |

| Downstream frame not seen by Node 3 | TX 33 → Node 3 RX 25; or Node 3 is not powered | Capture at 9600 baud on the link | Restore the link |

| Downstream frame contains `TAV:0.00\|node1:0` | Node 1's frame is not arriving or is malformed | Node 1 page: is Node 1 transmitting `\|TAV:…\|node1:1;`? | Fix the Node 1 → Node 2 link |

| Debug UART silent | Expected — Node 2 does not log during normal operation | — | Only a fatal trap prints anything |

## Validation

1. **Read Node 1's LCD.** Node 2's five values appear there in real time:

   line 2 `DO…mg/l T…C`, line 3 `AT…C H…%`, and line 1 `F<volume>L`.

   Confirm they track physical changes: stir the water for the DS18B20, blow

   across the DHT11, raise the TBV water level.

2. **Capture the two link frames at 9600 baud.** On a PC connected to Node 2's

   GPIO 25 and 26 you should see, every 50 ms:

   ```text

   |TAV:NNNN.NN|node1:1|DO:N.NN|Temp:N.NN|TBV:NNNN.NN|AT:N.NN|AH:NN.NN|node2:1;

   |DO:N.NN|Temp:N.NN|TBV:NNNN.NN|AT:N.NN|AH:NN.NN|node2:1;

   ```

   The first line goes to Node 3, the second to Node 1. Field diagnostic: if

   the second line updates but the first does not, Node 2's upstream receive

   path is the fault.

3. **Check the health flag.** `node2:1` requires **all five** of temp, DO, TBV,

   AT and AH to be valid. To test a single channel, disconnect that one sensor

   and confirm `node2` flips to `0` — and that Node 1 then shows `STATUS: FAULT`.

4. **Buffered-ADC plausibility.** Log the raw `analogRead(34)` value; with the

   probe disconnected it should read 0 and invalidate the DO channel; in air it

   should sit near mid-scale. A constant 0 or a constant maximum both indicate a

   wiring fault.

5. **Non-blocking DS18B20 check.** Change the water temperature and confirm the

   reported value follows **one second later**, not two. That confirms the

   non-blocking conversion pipeline is behaving as intended.

6. **DHT11 pacing check.** The DHT11 fields must not change faster than once

   every two seconds. Rapidly varying values indicate a marginal sensor or a

   noisy connection.

## Source

* Firmware file at the pinned commit:

  [`FreeRTOS_Implementation/Node2/Node2.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino)

* Directory listing:

  [`FreeRTOS_Implementation/Node2`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2)

* Extracted snippets used on this page:

  [node2-pin-definitions](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L10-L32),

  [node2-sensor-task](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L98-L220),

  [node2-parse-node1](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L225-L239),

  [node2-parse-node3](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L240-L254),

  [node2-uart-routing](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L259-L370)

* Commit: [`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/commit/db6d9b896341a9c7d8fd01913e854b663c110d55)

* Firmware Source Map: [../firmware/source-map.html](../firmware/source-map.md)

* Related: [Node 1](node1.md) ·

  [Node 3](node3.md) ·

  [Serial Links](../communication/serial-links.md) ·

  [RTOS Tasks](../rtos/tasks.md) ·

  [Message Format](../communication/message-format.md)
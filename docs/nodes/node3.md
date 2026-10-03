---

title: Node 3 (Flow Meter and Frame Forwarder)

description: Field-service manual for CIRQUA Node 3 — pulse-counted flow measurement on GPIO 23, plus the upstream frame forwarder.

---

# Node 3 (Flow Meter and Frame Forwarder)

## Identity

<div class="cirqua-identity">

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Node name</span>

    <span class="cirqua-identity__value">Node 3</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Purpose</span>

    <span class="cirqua-identity__value">Flow injector — forwards the upstream frame to Node 4 and appends the cluster's flow reading</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Physical role</span>

    <span class="cirqua-identity__value">Inline flow measurement at the transfer line between Feeding Tank B and the treatment train</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware variant</span>

    <span class="cirqua-identity__value">FreeRTOS_Implementation/Node3 <span class="cirqua-badge cirqua-badge--current">Current</span></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware commit</span>

    <span class="cirqua-identity__value"><code>db6d9b8</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware file</span>

    <span class="cirqua-identity__value"><code>FreeRTOS_Implementation/Node3/Node3.ino</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Controller</span>

    <span class="cirqua-identity__value">ESP32</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Hardware revision</span>

    <span class="cirqua-identity__value">Not verified from the current source.</span>

  </div>

</div>

## Responsibilities

Node 3 is the smallest node in the cluster and has **three** duties:

1. **Counts flow pulses.** An interrupt on the falling edge of GPIO 23

   increments a 32-bit counter inside a critical section. At 1 Hz the task

   reads the counter, resets it, and divides by the calibration factor to obtain

   a flow rate in **L/min**.

2. **Validates and forwards the upstream frame.** Everything received from Node 2

   is checked structurally, the trailing `;` is stripped, and the frame is

   re-emitted with `FLM` and `node3` appended.

3. **Raises a fallback frame on upstream silence.** If no valid upstream frame

   arrives for `TIMEOUT_MS` (2000 ms), it emits a synthetic minimum frame

   **once**, then stays silent until a good frame returns.

Node 3 has **no LCD, no local sensor other than the flow input, and no

downstream acknowledgement**. It also originates no upstream frame of its own.

!!! important "Node 3 has no frame of its own to originate"

    Unlike Node 1, Node 3 cannot start a chain of communication. Every field it

    sends downstream — `TAV`, `node1`, `DO`, `node2` — was produced upstream. If

    the Node 2 → Node 3 link is down, Node 3 can only emit the one-shot fallback

    frame described above; it cannot regenerate real telemetry.

Node 3 also does **not** send anything back up towards Node 2. The only write it

performs is downstream to Node 4.

## Inputs

| Input | Device | Signal | Notes |

|---|---|---|---|

| Flow pulses | [Pulse flow meter](../sensors/flow.md) | GPIO 23, `INPUT_PULLUP`, ISR on **FALLING** | Part number > **Not verified from the current source.** |

| Upstream frame | [UART](../communication/serial-links.md) | GPIO 25 RX (UART1) | From Node 2; structurally validated |

| Downstream link | [UART](../communication/serial-links.md) | GPIO 33 TX (UART2) | To Node 4 |

| Downstream RX | [UART](../communication/serial-links.md) | GPIO 32 RX (UART2) | Opened by `DownstreamSerial.begin()`; **no bytes are read from it in the current source** |

## Outputs

| Output | Field | Format | Notes |

|---|---|---|---|

| Downstream to Node 4 | entire upstream frame | verbatim | Node 3 does not rewrite upstream values |

| Downstream to Node 4 | `FLM` | `%.2f` | Flow rate, **L/min**, or `0.00` when invalid |

| Downstream to Node 4 | `node3` | `1` / `0` | `1` when the flow sample is valid |

| Upstream to Node 2 | **Nothing** | — | No reverse write exists |

| Local display | **None** | — | Node 3 has no LCD |

| E-mail | **None** | — | E-mail exists only on [Node 4 SMTP](node4-smtp.md) |

Normal downstream frame: upstream frame with `FLM` and `node3` appended, e.g.

```text

|TAV:NNNN.NN|node1:1|DO:N.NN|Temp:N.NN|TBV:NNNN.NN|AT:N.NN|AH:NN.NN|node2:1|FLM:0.00|node3:1;

```

Fallback frame on upstream timeout, emitted once:

```text

|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:%.2f|node3:%d;

```

!!! note "The fallback frame is a synthetic minimum, not a measurement"

    It hard-codes `TAV:0.00`, `node1:0`, `DO:0.00` and `node2:0` — a

    "nothing upstream, everything invalid" marker. It carries the *real* current

    flow value, so the flow channel keeps reporting while the rest of the chain

    is marked invalid. A downstream consumer must treat `node1:0` / `node2:0` in

    this frame as "upstream link lost", not as a genuine zero reading.

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

| Flow sensor | pulse input | 23 | in, `INPUT_PULLUP` | ISR `IRAM_ATTR pulseISR()` on **FALLING** |

| UART1 | RX (from N2) | 25 | in | 9600 8N1 |

| UART1 | TX (to N2) | 26 | out | Not written by the current source |

| UART2 | RX (from N4) | 32 | in | Declared; no data is read from it |

| UART2 | TX (to N4) | 33 | out | Forwarded frame and fallback frame |

```cpp

--8<-- "assets/snippets/node3-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>pin assignments, flow constant, timeout</code> ·

lines 3–13 · commit <code>db6d9b8</code>
</div>

### Constants

| Constant | Value | Meaning |

|---|---|---|

| `FLOW_CAL_FACTOR` | 5.5 | Pulses per litre |

| `TIMEOUT_MS` | 2000 | Upstream silence before the one-shot fallback |

| Flow period | 1000 ms | Counter is read and reset once per second |

| Counter type | `volatile uint32_t` | Free-running, no overflow detection |

## Power

> **Supply voltage and current draw are NOT verified from the current source.**

> The repository contains no regulator, rail, current budget, battery or solar

> topology for this node, and no schematic exists.

What the source does imply:

* `pinMode(PIN_FLOW_SENSOR, INPUT_PULLUP)` enables the ESP32's internal

  pull-up on GPIO 23. The flow sensor's output is therefore an **open-collector /

  pull-to-ground style signal**, referenced to the ESP32's 3.3 V logic domain,

  not a push-pull 5 V output.

* If the flow sensor board drives its output from a 5 V supply, that output must

  not exceed the ESP32's input range; nothing in the source confirms it does or

  does not.

The flow sensor's own supply voltage, and the sensor's part number, are both

> **Not verified from the current source.**

## Communication

| Aspect | Detail |

|---|---|

| Upstream | Node 2, UART1, GPIO 25 RX |

| Downstream | Node 4, UART2, GPIO 33 TX |

| Reverse link to Node 2 | **None in practice** — see the Node 2 page's note on the unused `\|FR:` / `\|node3:` parser |

| Downstream RX (GPIO 32) | Opened but never read |

| Protocol | Delimiter-separated ASCII key/value |

| Baud | 9600, `SERIAL_8N1` (`INTERNODE_BAUD`) |

| Frame | upstream frame verbatim + `\|FLM:%.2f\|node3:%d;` |

| Timing / cadence | UART task 50 ms; flow task 1000 ms; timeout `TIMEOUT_MS` = 2000 ms |

| Receive buffer | `char rxBuffer[256]`; assembled frame `char clusterPacket[320]`; fallback `char fallbackPacket[128]` |

| Frame detection | Character `;` terminates; `\n` and `\r` are skipped |

| Integrity | **No checksum, no CRC, no sequence number, no acknowledgement, no retry.** Structural validation only |

### Validation logic

```cpp

--8<-- "assets/snippets/node3-frame-validation.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>validateUpstreamFrame</code> ·

lines 71–78 · commit <code>db6d9b8</code>
</div>

The check requires `TAV:` (or `|TAV:`), `|node1:`, `|DO:` and `|node2:`. Note

that `Temp`, `TBV`, `AT` and `AH` are **not** required — a frame missing only

those would still be forwarded.

### Failure behaviour

* **Upstream silent > 2000 ms.** Emits the fallback frame **once**, sets

  `timeoutAlertSent = true`, and then goes silent. A good upstream frame clears

  the flag so the next outage reports again.

* **Structurally invalid frame.** Silently discarded — no forwarding, no

  logging, no flag change.

* **Buffer overflow.** RX index resets to 0 and the frame is dropped.

* **Pulse counter overflow.** There is **no** overflow detection; `g_pulseCount`

  is a free-running 32-bit counter. It is read and zeroed every second, so

  overflow would require an implausible pulse rate, but the firmware does not

  guard against it.

* **Zero pulses.** `flowRate` becomes exactly `0.00` and is still marked valid

  (`isValid = true`). **Zero flow and no flow are indistinguishable** in the

  frame — a stopped impeller and a disconnected sensor look identical.

## RTOS Architecture

| Task name | Function | Stack | Priority | Core | Period |

|---|---|---|---|---|---|

| `N3_Flow` | `Task_Flow_Node3` | 3072 | 2 | 1 | 1000 ms (`vTaskDelayUntil`) |

| `N3_UART` | `Task_UART_Node3` | 3072 | 3 | 0 | 50 ms (`vTaskDelayUntil`) |

Mutex: **`xFlowMutex`** protects `g_flowData`. 20 ms timeout on both the read

(snapshot for forwarding) and the write (flow commit).

Extra synchronisation primitive — this is unique to Node 3 in the cluster:

| Primitive | Type | Purpose |

|---|---|---|

| `g_pulseMux` | `portMUX_TYPE` (`portMUX_INITIALIZER_UNLOCKED`) | Guards `g_pulseCount` |

| `g_pulseCount` | `volatile uint32_t` | Free-running pulse counter |

| ISR-side guard | `portENTER_CRITICAL_ISR` / `portEXIT_CRITICAL_ISR` | Inside `IRAM_ATTR pulseISR()` |

| Task-side guard | `portENTER_CRITICAL` / `portEXIT_CRITICAL` | Read-and-reset in `Task_Flow_Node3` |

This is a spinlock-style critical section, not a mutex: the counter is shared

between an interrupt context and a task, and the task's read-and-reset is

atomic against the ISR.

```cpp

--8<-- "assets/snippets/node3-pulse-isr.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>pulseISR</code> ·

lines 15–23 · commit <code>db6d9b8</code>
</div>

The 1 Hz flow computation:

```cpp

--8<-- "assets/snippets/node3-flow-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>Task_Flow_Node3</code> ·

lines 43–69 · commit <code>db6d9b8</code>
</div>

## Firmware

Forwarding and the one-shot timeout fallback:

```cpp

--8<-- "assets/snippets/node3-uart-forwarding.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>Task_UART_Node3</code> ·

lines 82–154 · commit <code>db6d9b8</code>
</div>

The pulse counting chain, end to end:

```text

GPIO 23 falling edge

  -> IRAM_ATTR pulseISR()           [critical ISR section]

  -> g_pulseCount++                 [volatile uint32_t]

  -> Task_Flow_Node3 every 1000 ms  [critical section: read and reset]

  -> flowRate = pulses / 5.5        [L/min]

  -> g_flowData under xFlowMutex

  -> appended as |FLM:%.2f|node3:%d

```

Setup creates the mutex and the two tasks; `loop()` calls `vTaskDelete(NULL)`:

```cpp

--8<-- "assets/snippets/node3-setup.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>setup</code> ·

lines 158–170 · commit <code>db6d9b8</code>
</div>

## Sensors

| Page | Sensor | Used by Node 3 |

|---|---|---|

| [Flow](../sensors/flow.md) | Pulse flow meter on GPIO 23 | **Yes** — the node's only measurement |

| [Ultrasonic (HC-SR04)](../sensors/ultrasonic.md) | HC-SR04 | No |

| [Water Temperature (DS18B20)](../sensors/temperature.md) | DS18B20 | No |

| [Dissolved Oxygen](../sensors/dissolved-oxygen.md) | Analogue DO probe | No |

| [Humidity / Ambient (DHT11)](../sensors/humidity.md) | DHT11 | No |

| [pH](../sensors/ph.md) | Analogue pH probe | No |

| [Turbidity](../sensors/turbidity.md) | Analogue turbidity | No |

| [Conductivity (EC)](../sensors/conductivity.md) | Analogue EC probe | No |

## Calibration

| Item | Where | Value |

|---|---|---|

| `FLOW_CAL_FACTOR` | `Node3.ino` | `5.5f` pulses per litre |

| Flow period | `Task_Flow_Node3` | 1000 ms — flow rate is per-minute but computed from a 1 s window |

| `TIMEOUT_MS` | `Node3.ino` | 2000 |

| Pin mode | `Task_Flow_Node3` | `INPUT_PULLUP`, interrupt on `FALLING` |

| Counter reset | `Task_Flow_Node3` | Read and zeroed each 1000 ms |

!!! warning "The pulse-per-litre factor is a single hard-coded number"

    `FLOW_CAL_FACTOR = 5.5` is not stored in NVS, is not exposed on any console,

    and cannot be changed without editing and reflashing the sketch. It has never

    been verified against a physical meter of known accuracy. Every flow figure

    in the cluster inherits whatever error that constant carries.

There is **no calibration page** for flow in this documentation set — the

procedure has to be built from the measurement chain:

* Engineering interpretation, not a verified procedure: to establish your own

  factor, run a known volume through the sensor, count the pulses, and compute

  `pulses / litres`. Compare with 5.5 and record the result.

* Note the unit arithmetic: the task sums pulses over 1000 ms and divides by 5.5.

  The source labels the result **L/min**, but a 1-second measurement window

  yields the instantaneous flow in **L/s** scaled by the factor. Confirm the

  intended unit against a known duty cycle before using the value for billing,

  dosing or mass balance.

## Display / UI

**Node 3 has no LCD.** It emits no display output and prints nothing on the

debug UART during normal operation. The only debug output is the fatal trap

message `[FATAL ERROR] Node 3 Task Failed: <name>`.

The flow value is observable only downstream, as the `FLM` field on the frame

that reaches [Node 4](node4.md) and the controller.

## Troubleshooting

| Symptom | Likely cause | Check | Action |

|---|---|---|---|

| `FLM` always `0.00` | No pulses counted, or the K-factor is wrong for your sensor | Tap the impeller or flow the line; watch for a change | Check GPIO 23 wiring, the sensor's own supply, and the pull-up |

| `FLM` always `0.00` **and** `node3:1` | The flow task is working but counting zero — sensor, wiring or K-factor | Note that `node3` is still `1` | Verify the K-factor against a measured volume; see Calibration |

| `FLM` stuck at a non-zero value with no flow | Sticky impeller, or partial obstruction | Compare with a bucket-and-stopwatch measurement | Clean or replace the flow sensor |

| `FLM` roughly 60× too high or too low | Unit mismatch: the value is derived from a 1 s window but labelled L/min | Measure a known litre per minute and compare | Reconcile the unit before using the value |

| Controller sees `TAV:0.00\|node1:0\|DO:0.00\|node2:0` frames | Node 3's upstream timeout fallback fired — the Node 2 → Node 3 link is down | Node 2 page: is Node 2 transmitting? | Restore the Node 2 → Node 3 link |

| Fallback frames repeat every few seconds | The link is flapping — frames arrive and drop alternately | Watch the upstream RX LED, capture the link at 9600 baud | Fix the cable or the Node 2 transmit side |

| Downstream frame never appears | TX 33 → Node 4 RX 25 open, or Node 4 not powered | Verify ground continuity and baud | Restore the link |

| Frames forwarded but truncated | Frame exceeded `rxBuffer[256]` | Compare the incoming and outgoing frame lengths | Check for an unexpectedly long upstream frame |

| Frame forwarded without `FLM` | An older Node 3 firmware is flashed | Compare the file with commit `db6d9b8` | Reflash |

| Frame contains `FR:` instead of `FLM:` | A legacy/older flow key | Search the wire capture for `FLM:` | See [Legacy Firmware](../historical/legacy-firmware.md); reflash the current sketch |

| `TBV`, `Temp`, `AT` or `AH` missing from the forwarded frame | These keys are not required by `validateUpstreamFrame` | Inspect the incoming frame | Not a Node 3 fault; the upstream frame was already incomplete |

| Fatal trap on the debug UART | Mutex or task creation failure | — | The node is dead by design; reflash |

## Validation

1. **Generate flow and read `FLM` downstream.** Capture Node 4's UART RX at

   9600 baud, run water through the meter, and confirm the `FLM` field changes.

   With no flow it must read exactly `0.00`.

2. **Verify the 1-second window.** Read `FLM` repeatedly while holding a steady

   flow. The value should update about once per second, tracking any change with

   at most one second of lag. Faster updates would indicate a stale or

   duplicated measurement path.

3. **Test the ISR edge.** Because the interrupt is on **FALLING** with an internal

   pull-up, a sensor that idles LOW and pulses HIGH-to-LOW will count; one that

   idles HIGH and pulses LOW will not be counted at all by this configuration.

   Confirm the sensor's output idle state with a meter before concluding the

   sensor is faulty.

4. **Confirm `node3` health.** `node3` is `1` whenever the flow task has produced

   a sample — including a zero-flow sample. It therefore says nothing about

   whether the sensor is physically working. Only a measured non-zero flow under

   known conditions proves the input is live.

5. **Test the timeout path.** Disconnect the Node 2 → Node 3 link. Within about

   2 s you must see exactly **one** fallback frame:

   ```text

   |TAV:0.00|node1:0|DO:0.00|node2:0|FLM:0.00|node3:1;

   ```

   It must **not** repeat. If it repeats every 2 s, the mute flag is not being

   honoured or a good frame is intermittently resetting it.

6. **Reconnect and confirm recovery.** Restore the link; the first valid frame

   must be forwarded immediately and the mute flag cleared, so a later outage

   reports again.

7. **Loop test.** Pump a known volume through the sensor and compare the implied

   litres against the measured volume. The ratio is the correction factor for

   `FLOW_CAL_FACTOR`; record it.

## Source

* Firmware file at the pinned commit:

  [`FreeRTOS_Implementation/Node3/Node3.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino)

* Directory listing:

  [`FreeRTOS_Implementation/Node3`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3)

* Extracted snippets used on this page:

  [node3-pin-definitions](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L3-L13),

  [node3-pulse-isr](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L15-L23),

  [node3-flow-task](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L43-L69),

  [node3-frame-validation](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L71-L78),

  [node3-uart-forwarding](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L82-L154),

  [node3-setup](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L158-L170)

* Commit: [`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/commit/db6d9b896341a9c7d8fd01913e854b663c110d55)

* Firmware Source Map: [../firmware/source-map.html](../firmware/source-map.md)

* Related: [Node 2](node2.md) ·

  [Node 4](node4.md) ·

  [Flow](../sensors/flow.md) ·

  [Serial Links](../communication/serial-links.md) ·

  [RTOS Tasks](../rtos/tasks.md)
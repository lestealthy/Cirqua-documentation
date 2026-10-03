---

title: Queues and Buffers

description: The CIRQUA firmware uses no FreeRTOS queues — all inter-task data moves through mutex-guarded global structs plus fixed-size C buffers for serial reassembly.

---

# Queues and Buffers

!!! important "No FreeRTOS queues are used"

    This firmware does **not** use FreeRTOS queues, semaphores-as-notifications,

    or event groups. There is no `xQueueCreate`, `xQueueSend`, `xQueueReceive`,

    `xSemaphoreGiveFromISR` or `xEventGroupCreate` anywhere in the cluster.

    All inter-task data exchange happens through exactly two mechanisms:

    1. **Shared global structs**, written by the sensor task and read by the UART

       and LCD tasks, protected by **mutexes**.

    2. **Fixed-size C character buffers**, used only to reassemble incoming

       serial bytes into complete frames.

    This is a real and deliberate architectural property of the firmware, not an

    omission in this documentation. The rest of this page documents the

    mechanisms that are actually used.

## The shared structs

**Firmware implementation.** Each node declares its inter-task state as global

structs, with one struct per producer/consumer concern.

| Node | Struct | Written by | Read by | Protected by |

|---|---|---|---|---|

| Node 1 | `g_localSensors` | `N1_Sensors` | `N1_UART`, `N1_LCD` | `xLocalDataMutex` |

| Node 1 | `g_node2Data` | `N1_UART` (from the Node 2 reverse echo) | `N1_LCD` | `xNode2DataMutex` |

| Node 2 | `g_n2Sensors` | `N2_Sensors` | `N2_UART` | `xSensorsMutex` |

| Node 2 | `g_n1Data` | `N2_UART` (from the Node 1 upstream frame) | `N2_UART` | `xN1DataMutex` |

| Node 2 | `g_n3Data` | `N2_UART` (from the Node 3 reverse telemetry) | `N2_UART` | `xN3DataMutex` |

| Node 3 | `g_flowData` | `N3_Flow` | `N3_UART` | `xFlowMutex` |

| Node 4 / SMTP | `g_localN4` | `N4_Sensors` | `N4_UART`, `N4_LCD` | `xLocalN4Mutex` |

Note the asymmetry on Node 1: `g_localSensors` is **produced** locally and

`g_node2Data` is **produced** from the wire. Node 1 is the only node that both

measures a tank and receives another node's measurements.

Note also that `g_n1Data` and `g_n3Data` are both written *and* read by

`N2_UART` on Node 2. They exist because the parse step and the transmit step are

separated by a lock acquisition, so the parsed result must survive between them.

This is a struct standing in for what would otherwise be a one-slot queue.

### What replaces a queue, and what is lost

**Engineering interpretation.** Because there is no queue, there is **no

buffering depth and no back-pressure**:

* There is exactly **one** copy of each measurement in the system. If the UART

  task is late, the previous sample is simply overwritten — it is not queued

  for later transmission.

* The system therefore reports **the most recent sample**, never a backlog.

* A consumer cannot tell whether the value it is reading is fresh or stale; there

  is no timestamp or generation counter on the struct.

This is a perfectly reasonable design for a telemetry chain that publishes once

per second, but it is not the right shape for a system that must not lose data.

See <a href="../communication/fault-handling.html">Fault Handling</a> — there is

**no store-and-forward**, and a stalled UART task means data is genuinely lost.

## The copy-on-read snapshot pattern

**Firmware implementation.** Readers do not hold a mutex while they format a

frame. Instead they:

1. `xSemaphoreTake(mutex, timeout)`

2. copy the whole struct into a **local** variable

3. `xSemaphoreGive(mutex)`

4. build and transmit the frame from the local copy

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

### Why this is safe

**Engineering interpretation.** Three properties make the pattern correct:

1. **The critical section is short and bounded.** Only a struct copy happens

   under the lock. Serial transmission — which at 9600 baud takes milliseconds

   per frame — happens entirely outside it. This is why the lock timeouts can

   be as short as 10 ms and still work.

2. **The copy is atomic with respect to the writer.** The producer commits the

   *entire* struct under the same mutex. A reader therefore either sees the

   whole previous sample or the whole new one; it can never see a half-written

   struct. There is no torn read.

3. **The snapshot is internally consistent.** Because all fields come from one

   copy taken in one critical section, a frame never mixes values from two

   different samples. This matters for Node 2, which emits `DO`, `Temp`, `TBV`,

   `AT` and `AH` in a single frame from one snapshot — the dissolved oxygen

   compensation factor and the water temperature it depends on always come from

   the same acquisition cycle.

### What happens if the take times out

**Firmware implementation.** The takes are bounded — **50 ms** for a sensor

commit, **20 ms** for a UART snapshot, **10 ms** for Node 1's transmit snapshot

— and the code **proceeds** on timeout.

**Engineering interpretation, stated plainly.** Proceeding on timeout means the

task formats its frame from a **zero-initialised local snapshot**. The visible

consequence is that a frame can legitimately go out on the wire carrying `0.00`

for every field, or `0` for the health flag, even though no sensor actually read

zero. A reader at the far end cannot distinguish that from a genuine zero

reading.

The practical trigger for a timeout is a producer task holding its mutex for an

unusually long time — most plausibly Node 4's blocking DS18B20 conversion if it

were to hold the mutex across it, or simply mutex contention on a loaded core.

The timeout therefore acts as a **fail-safe that publishes zeros** rather than as

a mechanism that reports the failure.

This is one of the genuine protocol weaknesses recorded in

<a href="../communication/fault-handling.html">Fault Handling</a>: a zero reading

is ambiguous between *"the sensor genuinely read zero"* and *"the snapshot was

not available"*.

## Serial reassembly buffers

**Firmware implementation.** Incoming bytes are accumulated into fixed C

buffers until a frame terminator arrives. Every node implements the **same

overflow policy: reset the index and drop the frame.** No partial frame is ever

transmitted.

| Node | Buffer | Type | Size | Overflow behaviour |

|---|---|---|---|---|

| Node 1 | UART1 receive | `String` | capped at **256**, index reset at **250** | Index reset, frame dropped |

| Node 2 | UART1 receive (from Node 1) | `char` | **128** | Index reset, frame dropped |

| Node 2 | UART2 receive (from Node 3) | `char` | **128** | Index reset, frame dropped |

| Node 3 | UART1 receive (from Node 2) | `char` | **256** | Index reset, frame dropped |

| Node 4 | UART1 receive (from Node 3) | `char` | **384** | Index reset, frame dropped |

| Node 4 | Assembled downstream packet | `char` | **512** | Used to build the frame sent to the controller |

**Engineering interpretation.** These sizes are generous relative to the actual

frames — the largest real frame is well under 200 characters — so a healthy link

never comes close to them. They only matter when something is wrong: a

truncated read, a corrupted terminator, or noise that prevents a `;` from ever

being seen. In those cases the buffer fills, the index resets, and the partial

content is discarded. The node recovers cleanly at the next `;`, and no partial

or garbage frame reaches the controller.

**Node 1's buffer is the exception.** It is an Arduino `String` rather than a

fixed `char` array, so it is heap-allocated and grows on demand up to its 256

character cap. It carries the 250-character reset threshold to stop before the

cap is reached. This is a different memory model from the other nodes and is

worth knowing when reasoning about fragmentation — Node 1's LCD task and UART

task both allocate `String` objects while parsing.

### Relationship between buffer size and frame rate

**Engineering interpretation.** At 9600 baud, 8N1, each byte occupies 10 bits,

so the wire carries roughly **960 bytes per second**. A 128-character buffer is

therefore about **0.13 seconds** of wire time. None of the buffers can overflow

at the nominal one- or two-frames-per-second rate; overflow implies a fault

condition, which is exactly why the drop-and-reset policy is safe.

## ISR-side state

Node 3 has one piece of genuinely asynchronous shared state:

| Item | Detail |

|---|---|

| `g_pulseCount` | `volatile uint32_t`, incremented by `pulseISR()` |

| `pulseISR()` | `IRAM_ATTR`, triggered on **FALLING** at GPIO 23 |

| Protection | `portMUX_TYPE` spinlock with `portENTER_CRITICAL` / `portEXIT_CRITICAL` |

| Consumer | `N3_Flow`, once per 1000 ms, then the count is reset |

```cpp

--8<-- "assets/snippets/node3-pulse-isr.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>pulseISR</code> and the <code>portMUX_TYPE</code> declaration ·

lines 15–23 · commit <code>db6d9b8</code>
</div>

`volatile` alone would not be sufficient here: a 32-bit increment is not

atomic on the ESP32's 32-bit architecture when preemption is possible, so a

read-modify-write can be interrupted and lose a count. The critical section

closes that window. Full discussion in

<a href="synchronisation.html">Synchronisation</a>.

Note that this counter is the one piece of shared state in the cluster that is

**not** a struct and **not** mutex-protected — a mutex cannot be taken from an

ISR, which is precisely why a critical section is used instead.

## Summary of the data-flow mechanisms

| Mechanism | Used? | Where |

|---|---|---|

| FreeRTOS queue (`xQueue*`) | **No** | — |

| Binary/counting semaphore as notification | **No** | — |

| Event group | **No** | — |

| Task notification | **No** | — |

| Mutex-protected global struct | **Yes** | All four nodes |

| Fixed C buffer for serial reassembly | **Yes** | All four nodes |

| `portMUX_TYPE` critical section | **Yes** | Node 3, `g_pulseCount` only |

| Stream/task polling | **Yes** | UART tasks poll their ports on a fixed period |

## Related pages

* <a href="synchronisation.html">Synchronisation</a> — mutex inventory and lock

  timeouts.

* <a href="tasks.html">RTOS Tasks</a> — which task owns which struct.

* <a href="../communication/message-format.html">Message Format</a> — why frame

  sizes are what they are.

* <a href="../architecture/data-flow.html">Data Flow</a> — the end-to-end

  sequence.


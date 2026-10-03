---

title: Message Format

description: Authoritative reference for the CIRQUA ASCII telemetry protocol — field dictionary, real frame examples per link, and what the format does not guarantee.

---

# Message Format

**Authoritative protocol page.** Every format string, field name and example on

this page is transcribed from the `snprintf` calls in the firmware at commit

`db6d9b8`. Link parameters are **9600 baud, 8N1**.

## Grammar

The protocol is plain **ASCII** with no binary framing of any kind.

| Element | Character | Role |

|---|---|---|

| Field separator | `\|` | Separates one key/value pair from the next |

| Key/value separator | `:` | Separates the key from its value |

| Frame terminator | `;` | Marks the end of the frame |

| Line terminator | `\n` | Follows the `;`; completes the byte sequence |

| Leading field separator | `\|` | **Every frame begins with `|`** |

| Character set | ASCII | No escaping, no encoding |

A frame therefore looks like:

```

|KEY:VALUE|KEY:VALUE|KEY:VALUE;\n

```

with the first character after the opening quote being a `|`.

### Why the leading `|` is needed

**Firmware implementation.** Frames start with `|`, and every receiver resets

its reassembly index on overflow and re-synchronises on the next `;`.

**Engineering interpretation.** Because `|` both *terminates* a field and

*precedes* a key, and because `;` can be lost — a frame dropped in transit, a

buffer reset, a power cycle mid-frame — the receiver can be left holding a

partial field with no terminator in sight. The leading `|` resolves this

unambiguously:

* If a `|` arrives while the receiver is mid-frame, everything accumulated since

  the last field boundary is discarded and a new frame is started.

* Without it, the receiver would have to guess whether `0.50|TAV:` is a new

  frame or a truncated continuation, and would most likely produce a silently

  corrupt reading.

So the leading `|` is the protocol's only **resynchronisation mechanism**. It is

cheap and it works — but it only guarantees *framing*, not *integrity*. A frame

can be perfectly well-framed and still have the wrong number in it.

## Field dictionary

Every key that appears anywhere in the protocol, with the format specifier

actually used by its emitter.

| Key | Meaning | Unit | Emitted by | Format specifier |

|---|---|---|---|---|

| `TAV` | Total available volume — Collection Tank A, Node 1 | litres (integer on Node 1) | Node 1 | `%d` — Node 1's own frame, value doubled |

| `TAV` | Total available volume, as forwarded | litres | Node 2 | `%.2f` |

| `DO` | Dissolved oxygen | mg/L | Node 2 | `%.2f` |

| `Temp` | Water temperature, DS18B20 | °C | Node 2 | `%.2f` |

| `TBV` | Total bioavailable volume — Feeding Tank B, Node 2 | litres | Node 2 | `%.2f` |

| `AT` | Ambient temperature, DHT11 | °C | Node 2 | `%.2f` |

| `AH` | Ambient humidity, DHT11 | % RH | Node 2 | `%.2f` |

| `FLM` | Flow rate | **L/min** | Node 3 | `%.2f` |

| `pH` | Acidity | pH units | Node 4 | `%.1f` |

| `Turb` | Turbidity | NTU | Node 4 | `%d` |

| `EC` | Electrical conductivity — µS/cm variant | µS/cm | Node 4 | `%.0f` |

| `EC` | Electrical conductivity — mS/cm variant | mS/cm | Node 4 SMTP | `%.1f` |

| `TCV` | Total effluent volume, Node 4 | litres | Node 4 | `%d` |

| `EV` | Effluent volume, Node 4 SMTP field name | litres | Node 4 SMTP | `%d` |

| `ST` | Submerged temperature, DS18B20 | °C | Node 4 SMTP | `%.1f` |

| `node1` | Node 1 health flag | boolean | Node 1, and forwarded by Node 2 | `%d` |

| `node2` | Node 2 health flag | boolean | Node 2, and forwarded by Node 3 | `%d` |

| `node3` | Node 3 health flag | boolean | Node 3 | `%d` |

| `node4` | Node 4 health flag | boolean | Node 4, Node 4 SMTP | literal `1` |

!!! warning "`EC`, `TCV`/`EV` and `ST` differ between the Node 4 variants"

    `Node4` emits `EC` in **µS/cm** with temperature compensation and an

    explicit ×1000 scaling, plus a `TCV` volume field. `Node4_SMTP` emits `EC`

    in **mS/cm** with no temperature compensation and no scaling, and uses the

    field name `EV` instead of `TCV`, plus an `ST` submerged temperature field.

    A downstream consumer must be told which variant it is talking to. This is

    a real divergence in the committed firmware, not a documentation artefact.

## Health flag semantics

**Firmware implementation.** Every frame carries a health flag per contributing

node: `|node1:`, `|node2:`, `|node3:`, `|node4:`. A value of **`1` means every

local sensor validity flag on that node was true** at the moment the sample was

taken. `0` means at least one sensor on that node failed its own validity

test.

Node 2 is the strictest case: its `node2` flag requires **all five** of its

validity flags to be true.

**Engineering interpretation.** The flags are **per-node, not per-field**. A

`node2:0` frame does not tell you *which* Node 2 sensor failed — the consumer

must infer it. And because invalid values are transmitted as `0.00` rather than

being omitted, a `0.00` in the frame is ambiguous: it may be a genuine zero

reading or an invalid one. The health flag disambiguates the *node*, not the

*field*. See <a href="fault-handling.html">Fault Handling</a>.

## Real frames, link by link

All examples below are the actual `snprintf` formats from the source, with

representative values.

### Link 1 — Node 1 → Node 2 (upstream, frame origin)

```

|TAV:12480|node1:1;

```

| Part | Detail |

|---|---|

| Format | `\|TAV:%d\|node1:%d;\n` |

| `TAV` | Integer litres. Node 1's computed volume is **doubled**: `volumeLiters = (int)(volumeLiters * 2.0f)` |

| `node1` | Node 1's own validity flag |

| Emitted | Every `TX_INTERVAL_MS` = **500 ms** |

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

### Link 2 — Node 2 → Node 1 (reverse echo, for the Node 1 display)

```

|DO:6.41|Temp:24.50|TBV:2841.75|AT:31.20|AH:58.00|node2:1;

```

| Part | Detail |

|---|---|

| Format | `\|DO:%.2f\|Temp:%.2f\|TBV:%.2f\|AT:%.2f\|AH:%.2f\|node2:%d;\n` |

| Contents | Node 2's five local measurements. **No `TAV`** — Node 1 already knows it |

| Consumer | `N1_UART` → `g_node2Data` → the Node 1 display and its `STATUS:` precedence chain |

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

### Link 3 — Node 2 → Node 3 (consolidated upstream)

```

|TAV:12480.00|node1:1|DO:6.41|Temp:24.50|TBV:2841.75|AT:31.20|AH:58.00|node2:1;

```

| Part | Detail |

|---|---|

| Format | `\|TAV:%.2f\|node1:%d\|DO:%.2f\|Temp:%.2f\|TBV:%.2f\|AT:%.2f\|AH:%.2f\|node2:%d;\n` |

| Contents | Node 1's frame merged with Node 2's measurements. `TAV` is re-emitted as `%.2f`, **not** as the `%d` integer Node 1 produced |

| Note | This is the frame that carries the whole upstream cluster state |

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

### Link 4 — Node 3 → Node 2 (reverse telemetry)

Node 3 responds to Node 2 with a compact frame carrying only its own flow data,

which Node 2 parses into `g_n3Data` via `parseNode3ReversePacket()`. See the

Node 3 forwarding task for the exact shape.

### Link 5 — Node 3 → Node 4 (upstream plus flow)

```

|TAV:12480.00|node1:1|DO:6.41|Temp:24.50|TBV:2841.75|AT:31.20|AH:58.00|node2:1|FLM:14.55|node3:1;

```

| Part | Detail |

|---|---|

| Format | upstream frame **+** `\|FLM:%.2f\|node3:%d;\n` |

| Content | Node 3 does not rebuild the upstream frame — it **appends** to what it received, after validating it |

| Validation | `validateUpstreamFrame()` requires the `TAV`, `node1`, `DO` and `node2` keys to be present |

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

### Node 3 timeout fallback frame

```

|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:14.55|node3:1;

```

| Part | Detail |

|---|---|

| Format | `\|TAV:0.00\|node1:0\|DO:0.00\|node2:0\|FLM:%.2f\|node3:%d;\n` |

| Emitted | **Once**, after `TIMEOUT_MS` = 2000 ms of upstream silence |

| Muted | Guarded by `timeoutAlertSent` until the link recovers |

| Meaning | Upstream data is **absent**, not zero. `node1:0` and `node2:0` both flag it |

Note that `Temp`, `TBV`, `AT` and `AH` are **omitted entirely** from the

fallback frame — the format is deliberately incomplete, which is how a

structurally-aware receiver can distinguish it from a real frame containing

genuine zeros.

### Link 7 — Node 4 → Controller (the `Node4` variant)

```

|TAV:12480.00|node1:1|DO:6.41|Temp:24.50|TBV:2841.75|FLM:14.55|node3:1|pH:7.21|Turb:412|EC:9980|TCV:3315|node4:1;

```

| Part | Detail |

|---|---|

| Format | cleaned upstream **+** `\|pH:%.1f\|Turb:%d\|EC:%.0f\|TCV:%d\|node4:1;\n` |

| `EC` | µS/cm, temperature-compensated, scaled ×1000 |

| `TCV` | Effluent volume in litres |

| `node4` | Written as the **literal `1`** — this variant does not compute a per-sensor health flag for the downstream field |

**`AT` and `AH` are stripped.** `cleanUpstreamPacket()` removes the Node 2

ambient tokens, so the controller receives **one** ambient pair — Node 4's own

DHT11. In the committed code Node 4 appends its own fields but does not add

`AT:`/`AH:` to this frame shape, which means **no ambient pair reaches the

controller at all** from the plain `Node4` variant. That is worth noting

against the stated intent of the cleaner.

### Link 7 — Node 4 SMTP → Controller (the `Node4_SMTP` variant)

```

|TAV:12480.00|node1:1|DO:6.41|Temp:24.50|TBV:2841.75|FLM:14.55|node3:1|pH:7.21|Turb:412|EC:9.98|EV:3315|ST:23.10|node4:1;

```

| Part | Detail |

|---|---|

| Format | cleaned upstream **+** `\|pH:%.1f\|Turb:%d\|EC:%.1f\|EV:%d\|ST:%.1f\|node4:1;\n` |

| `EC` | **mS/cm**, `%.1f`, no temperature compensation, no ×1000 |

| `EV` | Replaces `TCV` as the effluent volume field name |

| `ST` | Submerged DS18B20 temperature, °C — **not present** in the plain `Node4` frame |

**A downstream consumer cannot treat the two variants interchangeably.** Same

link, same baud, same grammar, different field names and different units.

```cpp

--8<-- "assets/snippets/node4-uart-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_UART_Node4</code> ·

lines 996–1181 · commit <code>db6d9b8</code>
</div>

### Node 4 packet cleaning

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

## What the format does **not** guarantee

This is the most important section on the page.

| Absent mechanism | Consequence |

|---|---|

| **No checksum** | A single flipped bit in a digit changes the reading silently |

| **No CRC** | As above — no error detection at all |

| **No sequence number** | A consumer cannot detect a **dropped** frame. A missing frame is indistinguishable from a slow one |

| **No acknowledgement** | A sender never learns that its frame was not received |

| **No retry** | Nothing is resent. Ever |

| **No escaping** | A value containing `\|`, `:`, `;` or `\n` would corrupt the frame. No sensor output can produce these today, but nothing prevents it |

| **No length field** | The receiver must scan for `;` to find the end |

| **No timestamp** | Frames carry no time. A late frame is indistinguishable from a current one |

| **No field count** | The receiver cannot detect a **truncated but terminated** frame; it only knows a terminator arrived |

**Engineering interpretation — the combined risk.** Absences that are

individually tolerable combine badly in one specific case: **bit corruption

without a framing error.** A flipped bit inside a digit leaves the `|` and `;`

structure perfectly intact, so the receiver accepts the frame, reports it as

well-formed, and publishes a wrong number with a healthy flag set to `1`. There

is no mechanism anywhere in the chain that would catch this.

At 9600 baud over short point-to-point cables with a shared ground, the

probability is low — but it is not zero, and it is undetectable when it happens.

**Recommendation.** If the data must be defensible, add a two-character CRC to

each frame. The bandwidth cost at 9600 baud is negligible, and it converts an

undetectable silent error into a droppable frame. This is a firmware change, not

a documentation change.

## Frame size and reassembly buffers

**Firmware implementation.**

| Node | Buffer | Size | Policy on overflow |

|---|---|---|---|

| Node 1 | `String` | 256 cap, index reset at 250 | Reset index, drop frame |

| Node 2, per link | `char` | 128 | Reset index, drop frame |

| Node 3 | `char` | 256 | Reset index, drop frame |

| Node 4 | `char` | 384 | Reset index, drop frame |

| Node 4 assembled packet | `char` | 512 | Used to build the controller frame |

**Engineering interpretation.** Real frames are 40–120 bytes, so the buffers are

generous by a factor of two or more. They only fill if a terminator is never

seen — a broken link, noise, or a power cycle mid-frame. Because every receiver

resynchronises on the leading `|`, recovery is immediate and clean: no partial

frame ever reaches the controller.

## Sequence diagram — one full telemetry pass

```mermaid

sequenceDiagram

  autonumber

  participant S1 as Node 1 sensor task

  participant N1 as Node 1 UART task

  participant N2 as Node 2

  participant N3 as Node 3

  participant N4 as Node 4

  participant CTRL as Controller

  Note over S1,N1: Node 1 measures TAV, 2 Hz

  S1->>S1: commit g_localSensors under xLocalDataMutex (≤50 ms)

  N1->>S1: snapshot under mutex (≤10 ms), format on TX_INTERVAL_MS

  Note over N1,N2: Upstream frame origin — Node 1 only

  N1->>N2: |TAV:%d|node1:%d;\n (9600 8N1, TX33 → RX25)

  Note over N2: Parse TAV and node1 into g_n1Data

  Note over N2: Snapshot g_n2Sensors under xSensorsMutex (≤20 ms)

  N2->>N3: |TAV:%.2f|node1:%d|DO|Temp|TBV|AT|AH|node2:%d;\n (TX33 → RX25)

  N2->>N1: |DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;\n (TX26 → RX32)

  N1->>N1: store g_node2Data; N1_LCD renders STATUS: line

  Note over N3: validateUpstreamFrame() — structural check on TAV/node1/DO/node2

  N3->>N3: append flow to g_flowData, snapshot under xFlowMutex

  N3->>N4: upstream frame + |FLM:%.2f|node3:%d;\n (TX33 → RX25)

  alt Upstream silent for TIMEOUT_MS 2000 ms

    N3->>N4: |TAV:0.00|node1:0|DO:0.00|node2:0|FLM:%.2f|node3:%d;\n (once, then muted)

  end

  Note over N4: cleanUpstreamPacket() strips AT: and AH:

  N4->>N4: append pH, Turb, EC, TCV — snapshot g_localN4 under xLocalN4Mutex

  N4->>CTRL: |TAV|node1|DO|Temp|TBV|FLM|node3|pH:%.1f|Turb:%d|EC:%.0f|TCV:%d|node4:1;\n (TX33 → RX32)

```

The SMTP variant differs only in the final step, where `EC` becomes `%.1f` in

mS/cm and `TCV` is replaced by `EV`, with `ST` appended.

## Related pages

* <a href="serial-links.html">Serial Links</a> — the physical links these frames

  travel over.

* <a href="fault-handling.html">Fault Handling</a> — timeouts, validation and the

  fault-mode matrix.

* <a href="../architecture/data-flow.html">Data Flow</a> — the same sequence

  from the architecture layer.

* <a href="../sensors/index.html">Sensors</a> — where each measurement's units and

  calibration come from.


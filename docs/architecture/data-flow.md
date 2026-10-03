---

title: Data Flow

description: How a telemetry frame travels from Node 1 through Nodes 2, 3 and 4 to the controller, with the real snprintf formats at each hop.

---

# Data Flow

## Wire format

* ASCII, delimiter-separated key/value pairs.

* Field separator `|`, key/value separator `:`, frame terminator `;` followed by

  a newline.

* Frames **start with a leading pipe** — `|TAV:...`. Because `|` also terminates

  a field, the leading pipe is what disambiguates the start of a new frame from

  the tail of the previous one.

* Every frame carries a **node health flag** for the node that produced the

  immediately preceding data: `|node1:`, `|node2:`, `|node3:`, `|node4:`, where

  `1` means all of that node's local sensor validity flags are true.

> **Engineering interpretation.** This format is *self-delimiting by

> construction*, which is what makes it survivable on a link with no framing

> discipline — but it also means the receiver trusts the delimiters completely.

## What the format does not provide

| Missing | Consequence |

|---|---|

| No checksum, no CRC | A corrupted byte that still looks like a delimiter is accepted as data |

| No sequence number | A dropped or duplicated frame cannot be detected by the receiver |

| No acknowledgement | No node knows whether its data arrived |

| No retry | Loss is silent |

Validation is therefore **structural only**: `validateUpstreamFrame` checks for

the *presence of expected keys*. See

<a href="../communication/fault-handling.html">Fault Handling</a>.

## One full pass, hop by hop

### Hop 0 — Node 1 originates

Node 1 measures tank A level, converts to a volume, and emits the opening frame.

The value is an **integer** number of litres, and the computed volume has already

been doubled (see the calibration warning below).

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

### Hop 1 — Node 1 → Node 2, over UART1

```

|TAV:%d|node1:%d;\n

```

Typical frame:

```

|TAV:4120|node1:1;

```

### Hop 1b — Node 2 → Node 1, reverse echo, over UART1

Before forwarding, Node 2 emits a subset of its own values back to the head for

the Node 1 display:

```

|DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;\n

```

Typical frame:

```

|DO:6.41|Temp:23.50|TBV:980.00|AT:28.50|AH:61.00|node2:1;

```

### Hop 2 — Node 2 → Node 3, over UART2

Node 2 rebuilds the upstream frame with the tank A volume carried as a **float

with two decimals**, then appends all five of its own measurements:

```

|TAV:%.2f|node1:%d|DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;\n

```

Typical frame:

```

|TAV:4120.00|node1:1|DO:6.41|Temp:23.50|TBV:980.00|AT:28.50|AH:61.00|node2:1;

```

### Hop 3 — Node 3 → Node 4, over UART2

Node 3 appends flow and its health flag to whatever it received:

```

<upstream frame>|FLM:%.2f|node3:%d;\n

```

Typical frame:

```

|TAV:4120.00|node1:1|DO:6.41|Temp:23.50|TBV:980.00|AT:28.50|AH:61.00|node2:1|FLM:12.73|node3:1;

```

### Hop 3b — Node 3 timeout fallback

If Node 3 sees no upstream frame for its `TIMEOUT_MS` of 2000 ms it emits a

**substitute frame once, then stays muted**:

```

|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:%.2f|node3:%d;\n

```

Typical frame:

```

|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:11.98|node3:1;

```

Note that this fallback carries a **structurally valid but semantically empty**

upstream: the keys are present, the values are zero, and the health flags are

zero. Structural validation alone cannot tell it apart from a real all-zero

reading. This is the single most important caveat in the data flow.

### Hop 4 — Node 4 → Controller, over UART2

Node 4 first runs `cleanUpstreamPacket()`, which strips the `AT:` and `AH:` tokens

carried from Node 2 so the controller receives exactly one ambient pair — from

Node 4's own DHT11. It then appends its effluent fields:

**`Node4` build:**

```

<cleaned upstream>|pH:%.1f|Turb:%d|EC:%.0f|TCV:%d|node4:1;\n

```

Typical frame:

```

|TAV:4120.00|node1:1|DO:6.41|Temp:23.50|TBV:980.00|node2:1|FLM:12.73|node3:1|pH:7.2|Turb:184|EC:1120|TCV:640|node4:1;

```

**`Node4_SMTP` build** — a genuinely different downstream field set:

```

<cleaned upstream>|pH:%.1f|Turb:%d|EC:%.1f|EV:%d|ST:%.1f|node4:1;\n

```

Typical frame:

```

|TAV:4120.00|node1:1|DO:6.41|Temp:23.50|TBV:980.00|node2:1|FLM:12.73|node3:1|pH:7.2|Turb:184|EC:1.1|EV:640|ST:23.5|node4:1;

```

!!! warning "`EC` means different things in the two builds"

    `Node4` reports `EC` in **µS/cm** (temperature-compensated, ×1000) and

    accompanies it with `TCV`. `Node4_SMTP` reports `EC` in **mS/cm** (no

    temperature compensation, no ×1000) and emits `EV` and `ST` instead. A

    consumer that reads `EC` without knowing which build is at the end of the

    chain will be wrong by roughly three orders of magnitude.

## Sequence diagram for one full pass

```mermaid

sequenceDiagram

    autonumber

    participant N1 as Node 1 (head)

    participant N2 as Node 2

    participant N3 as Node 3

    participant N4 as Node 4 (tail)

    participant CTL as Controller (Mega)

    Note over N1: Sensors task, 500 ms

    N1->>N2: |TAV:4120|node1:1;

    N2->>N1: |DO:..|Temp:..|TBV:..|AT:..|AH:..|node2:1;  (reverse echo)

    Note over N1: LCD task renders merged values

    N2->>N3: |TAV:4120.00|node1:1|DO:..|Temp:..|TBV:..|AT:..|AH:..|node2:1;

    N3->>N4: upstream + |FLM:12.73|node3:1;

    Note over N4: cleanUpstreamPacket() strips AT: and AH:

    N4->>CTL: cleaned upstream + |pH:7.2|Turb:184|EC:1120|TCV:640|node4:1;

    Note over CTL: No ACK, no sequence number, no retry

```

## Buffers and overflow

| Location | Buffer | Cap note |

|---|---|---|

| Node 1 | `String` | 256-byte cap, index reset at 250 |

| Node 2 | `char[128]` | per link, so two buffers |

| Node 3 | `char[256]` | |

| Node 4 | `char[384]` | plus an assembled packet buffer of `char[512]` |

On overflow a receiver **resets its index**, which drops the frame being

assembled. Because Node 2's per-link buffer is the smallest at 128 bytes, and

because the Node 2 → Node 3 frame is the longest in the chain, that link is the

most exposed to a drop when a neighbour is slow.

> **Engineering interpretation.** With no checksum or sequence number, a dropped

> frame is indistinguishable from a quiet period at the controller. Treat gaps in

> the controller's data as a possible link symptom, not only as a sampling gap.

> See <a href="../validation/known-limitations.html">Known Limitations</a>.

## Continue

* <a href="communications.html">Communications</a> — the physical and framing contract

* <a href="../communication/message-format.html">Message Format</a>

* <a href="../communication/serial-links.html">Serial Links</a>

* <a href="timing.html">Timing</a> — how often each of these hops actually fires


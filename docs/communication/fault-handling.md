---

title: Fault Handling

description: Fault mechanisms in the CIRQUA cluster — RX and upstream timeouts, structural frame validation, the zero-reading ambiguity, and the fault-mode matrix.

---

# Fault Handling

## No store-and-forward

!!! danger "A broken link loses data permanently"

    There is **no store-and-forward** anywhere in the cluster. No node buffers a

    frame for retransmission, no queue holds unacknowledged data, and no disk or

    NVS record survives a link outage.

    **Firmware implementation.** Each node has exactly **one** copy of its

    current measurement state, in a shared global struct. The next acquisition

    overwrites it. If the downstream link is not being serviced when a new value

    arrives, the previous value is gone and the new one is sent instead. If a

    frame is in the reassembly buffer when the link drops, it is discarded on

    overflow or at reset.

    **Engineering interpretation.** The consequence is that the telemetry record

    is **sampled, not logged**. A node that runs normally produces a stream at

    1–2 Hz; a node whose link is down produces a **gap**, not a backlog. When the

    link recovers, transmission resumes at the current values with no replay of

    the missing interval. Any downstream consumer that requires a complete

    record must obtain it elsewhere — there is no on-node facility for this.

## Mechanisms actually implemented

### Node 1 — receive timeout and the waiting state

**Firmware implementation.**

| Constant | Value | Meaning |

|---|---|---|

| `RX_TIMEOUT_MS` | **3000** ms | Silence from Node 2 before declaring the link down |

The Node 1 LCD status derivation has two link-related steps, in strict order:

| Order | Condition | Status shown |

|---|---|---|

| 1 | **No frame has ever been received** | `WAITING` |

| 2 | `millis() - lastRx > RX_TIMEOUT_MS` | `ERROR` |

This distinction is deliberate and useful in the field: **`WAITING` means "the

link has never worked", `ERROR` means "the link worked and then stopped"**. The

first points at wiring, power or baud configuration at installation; the second

points at something that broke after the system was running.

Both **outrank every thermal and volume condition**, so the display always tells

you about the link before it tells you about the enclosure.

### Node 3 — upstream timeout and the one-shot fallback

**Firmware implementation.**

| Constant | Value | Meaning |

|---|---|---|

| `TIMEOUT_MS` | **2000** ms | Upstream silence before the fallback is emitted |

| `timeoutAlertSent` | boolean flag | Ensures the fallback is emitted **once** |

On upstream silence longer than 2000 ms, Node 3 emits:

```

|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:14.55|node3:1;

```

and then **mutes** further fallback frames until the link recovers. Flow is

still measured and still reported — only the upstream contribution is missing.

**Engineering interpretation.** Two design choices are worth reading carefully:

1. **The fallback is one-shot, not periodic.** A continuously repeating

   "upstream dead" frame every 2000 ms would swamp a 1 Hz data log with

   synthetic rows. Emitting once gives the consumer an unambiguous marker of

   *when* the outage began.

2. **The fallback omits `Temp`, `TBV`, `AT` and `AH` entirely.** This is a

   structural discriminator: a structurally-aware receiver can tell this frame

   from a real one by the missing keys, even though the numeric values look like

   zeros.

Note the timeout asymmetry: Node 3 gives up on upstream after **2000 ms**,

while Node 1 gives up on Node 2 after **3000 ms**. Node 3 is more impatient

because it sits downstream of more stages.

### Node 3 — structural frame validation

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

**Firmware implementation.** `validateUpstreamFrame()` checks for the presence

of four keys: **`TAV`**, **`node1`**, **`DO`** and **`node2`**. If any is

missing, the frame is rejected and not forwarded.

**Engineering interpretation.** This is **structural validation only**. It

detects a frame that is obviously wrong — truncated, empty, or from an

unexpected source — but it cannot detect a frame that is well-formed and

numerically incorrect. A frame with a corrupted digit inside `TBV` passes this

check unchanged.

### All nodes — buffer overflow

**Firmware implementation.** Every receiver resets its reassembly index when the

buffer fills and discards the partial content. Node 1 resets at 250 of its 256

character `String`; Nodes 2, 3 and 4 reset at the limit of their `char` buffers.

In all cases **no partial frame is ever transmitted**, and recovery is immediate

because the leading `|` resynchronises the parser.

### Node 2 — frame-completeness gating

This is the most consequential fault behaviour in the system, and it needs

stating carefully.

**Firmware implementation.** Node 2's `node2Healthy` flag requires **all five**

of its local validity flags to be true:

| Field | Validity test |

|---|---|

| DS18B20 water temperature | Not `DEVICE_DISCONNECTED_C`, and strictly between −55 °C and 125 °C |

| Dissolved oxygen | `rawDO != 0` |

| HC-SR04 volume | Distance within `[0, TANK_HEIGHT]`, `TANK_HEIGHT` = 178.0 cm |

| DHT11 temperature | `!isnan()` |

| DHT11 humidity | `!isnan()` |

**Invalid fields are still transmitted, as `0.00`, with `node2:0` set.**

**Engineering interpretation — the zero ambiguity, stated plainly.** This is a

genuine protocol weakness, and it is worth documenting rather than smoothing

over:

* A consumer reading `|DO:0.00|...|node2:0|` cannot tell from the **field

  itself** whether the sensor read zero or failed.

* The health flag resolves it only at **node granularity**: `node2:0` says

  *something* on Node 2 was invalid, not *what*. If DO, temperature and humidity

  all fail at once, `DO:0.00` is indistinguishable from a genuine zero DO

  reading.

* A genuine zero reading with a **healthy** flag is indistinguishable from a

  failed reading on a node that formats a snapshot it could not take. See

  <a href="../rtos/synchronisation.html">Synchronisation</a> — a timed-out mutex

  take causes the task to proceed with a zero-initialised snapshot.

* Because Node 2 forwards its measurements onward, the ambiguity propagates to

  Node 3, Node 4 and the controller. **Every downstream stage inherits it.**

**Recommendation.** If unambiguous data matters, the protocol would need a

per-field validity marker — for example an `NaN` sentinel, or a validity

suffix per key. The current format cannot express "this field is invalid"

distinctly from "this field is zero".

### Node 4 — range rejection rules

**Firmware implementation.** Node 4 is the strictest node about rejecting

implausible values:

| Channel | Rule | Rationale recorded in the source |

|---|---|---|

| Ultrasonic volume | Reject if `distance < 0` or `distance > TANK_HEIGHT + 20` — that is, beyond **198 cm** | Rejects a physically impossible distance in a 178 cm tank |

| pH | Valid iff `0.02 <= V <= 3.30` **and** `0.0 <= pH <= 14.0` | pH cannot be outside 0–14 |

| Turbidity | Valid iff `0.0 <= V <= 3.30`. **Deliberately does not invalidate at the range ends** | Saturation at either end is *physically valid*, not a fault |

| EC | Valid iff `0.0 <= V <= 3.30`. **Zero EC accepted as legitimate** | Distilled water has near-zero conductivity |

| DHT11 ambient | Temperature within −20…80 °C, humidity within 0…100 % | Beyond the DHT11's credible range |

| DS18B20 | Not `DEVICE_DISCONNECTED_C`, and −55 < T < 125 | Datasheet operating range |

The turbidity and EC cases are worth noting: the firmware makes a deliberate

distinction between "out of range, therefore broken" and "at the extreme of

range, therefore saturated but working". A sensor reading 3000 NTU is reported

as 3000 NTU with a valid flag, not discarded.

### Node 4 SMTP — threshold-based alerting

**Firmware implementation.** `hasError` is raised when **any** validity flag is

false, **or** `ambTemp > 45`, **or** `ambHum > 90`. Fault e-mails itemise each

failed sensor individually in an HTML `<ul>`, with a **12 hour error cooldown**

between alerts. A **24 hour** heartbeat is sent independently, and a startup

e-mail is sent on **every boot**.

Note the humidity threshold differs by context: **80 %** on Node 1's display,

**90 %** in the SMTP alert logic.

### Boot-time checks

**Firmware implementation.**

| Check | Node | Behaviour |

|---|---|---|

| `getDeviceCount() == 0` | Node 4 | Warns that the DS18B20 is absent |

**Engineering interpretation.** This is the only sensor-presence check in the

cluster. There is **no equivalent for the ultrasonic modules, the DHT11, the

flow sensor or any of the analogue probes** — a disconnected sensor is detected

by its output falling outside the validity range, not by an identity check. For

a DHT11 returning `!isnan()` checks this is usually adequate, but a

disconnected probe board that happens to sit at a plausible voltage would read

as healthy.

## Fault-mode matrix

| Fault | Detected by | Where surfaced | Recovery |

|---|---|---|---|

| Node 2 unreachable from Node 1, never connected | No frame ever received | Node 1 LCD: `WAITING` | Automatic on first valid frame |

| Node 2 unreachable from Node 1, after working | `millis() - lastRx > 3000` | Node 1 LCD: `ERROR` | Automatic on next valid frame |

| Node 2 sensor fails its validity test | Per-sensor validity flag | `node2:0` in every downstream frame; value reads `0.00` | Automatic when the sensor reads valid again |

| Node 2 → Node 3 link silent | Node 3 `millis() - lastRx > 2000` | One-shot fallback frame with `node1:0`, `node2:0` | Automatic; `timeoutAlertSent` resets |

| Node 1 → Node 2 link silent | Node 1 `RX_TIMEOUT_MS` after 3000 ms | Node 1 LCD: `ERROR` | Automatic |

| Frame truncated or malformed | `validateUpstreamFrame()` missing keys | Frame **not forwarded**; receiver waits for the next | Automatic at the next `;` |

| Frame partially received, no terminator | Buffer index reaches its limit | Index reset, frame dropped, nothing transmitted | Immediate on the next leading `\|` |

| Bit error inside a digit | **Nothing** | **Nowhere** — the wrong value is published with a healthy flag | **Does not recover** |

| Mutex take times out | Bounded take (50 / 20 / 10 ms) | Frame built from a **zero-initialised snapshot** | Automatic next cycle |

| DS18B20 absent on Node 4 | `getDeviceCount() == 0` at boot | Boot warning only | Requires the sensor to be reconnected |

| Ultrasonic echo out of range (Node 4) | `distance < 0` or `> TANK_HEIGHT + 20` | Field marked invalid; `node4` flag affected | Automatic |

| pH outside 0–14 or voltage outside 0.02–3.30 V | Validity gates | Field invalid | Automatic |

| Turbidity saturated (0 or 3000 NTU) | **Not a fault** — reported as a valid reading | Display and frame show the extreme value | n/a |

| EC reads zero | **Not a fault** — accepted as legitimate | Zero reported with a valid flag | n/a |

| Node 4 ambient above 45 °C or 90 % RH (SMTP) | `hasError` | Fault e-mail, 12 h cooldown | Automatic when the condition clears |

| Wi-Fi association fails (SMTP) | 30 attempts × 500 ms, then give up | No e-mail is sent — the failure is silent to the operator | Requires a reboot |

| Task or mutex creation fails | Return value check in `setup()` | `systemFatalTrap()` halts the node | Requires a power cycle |

| Node 3 pulse counter wraps | **No detection** | Not detected | n/a |

## What is not detected

**Engineering interpretation.** The honest list of blind spots:

* **Silent data corruption.** No checksum means a bit error inside a numeric

  field is undetectable and unrecoverable.

* **Dropped frames.** No sequence number means a consumer cannot distinguish

  "nothing happened" from "a frame was lost in transit".

* **Which field failed.** Health flags are per-node, not per-field.

* **Sensor identity.** Only the Node 4 DS18B20 is checked for presence.

* **Ground faults.** A lifted or missing common ground presents as intermittent

  link failure, not as a distinct fault.

* **Wi-Fi failure on the SMTP variant.** The e-mail path fails silently; there is

  no local indication that reporting has stopped.

**Recommendation.** The highest-value additions, in order of benefit per unit of

change: a per-frame CRC (converts silent corruption into a droppable frame), and

a sequence number (converts undetectable loss into detectable loss). Both are

small firmware changes with negligible bandwidth cost at 9600 baud.

## Related pages

* <a href="message-format.html">Message Format</a> — the frame structure and what

  it does not guarantee.

* <a href="serial-links.html">Serial Links</a> — the physical links.

* <a href="../rtos/synchronisation.html">Synchronisation</a> — the zeroed

  snapshot on a timed-out lock.

* <a href="../field-service/troubleshooting.html">Troubleshooting</a> — the

  field procedure for each row in this matrix.


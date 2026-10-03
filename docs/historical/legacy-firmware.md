---

title: Historical and legacy firmware

description: Provenance and differences of the archived _OLD sketches, which are retained for reference but are not the current CIRQUA firmware architecture.

---

# Historical and legacy firmware

The CIRQUA firmware repository contains a directory named `_OLD/`. Its contents

are **retained for provenance and design-history reference only**.

!!! danger "Historical / Legacy — not the current firmware architecture"

    Nothing in `_OLD/` describes how the deployed system behaves today. Its GPIO

    assignments, serial protocols, task structures, sensor conversions and

    calibration constants **must not** be used when servicing hardware, building

    a board, or interpreting a live telemetry frame.

    The current architecture is documented entirely from

    [`FreeRTOS_Implementation/`](../firmware/source-map.md).

## Why this page exists

Keeping the legacy sketches has genuine engineering value:

* it explains the origin of several constants that survive into the current code;

* it records bugs that were found and fixed, which is useful during future

  redesign;

* it documents the origin of the downstream controller's expected frame format.

## Current versus legacy

| Aspect | Current (`FreeRTOS_Implementation/`) | Legacy (`_OLD/`) |

|---|---|---|

| Concurrency model | FreeRTOS, dual-core, pinned tasks, mutex-guarded shared state | Single-threaded `setup()` / `loop()` with `delay()` |

| Node 1 UART pin pair | `HardwareSerial NodeSerial(1)` on RX 32 / TX 33 | `OutSerial(2)` / `InSerial(1)` on RX 25 / TX 26 |

| Node 1 volume | `int` litres, doubled by `2.0f` | Different formatting and structure |

| Node 3 pulse counter | `volatile uint32_t` guarded by `portMUX_TYPE` | `volatile uint16_t` guarded by bare `noInterrupts()` |

| Node 3 flow cadence | FreeRTOS `vTaskDelayUntil`, 1000 ms | `lastFlowMillis += 1000` in `loop()` |

| Node 4 pH | NVS-calibrated slope/offset plus temperature compensation | Hard-coded `3.5 * voltage + 0.0` |

| Node 4 EC | NVS K-factor, temperature compensated, reported µS/cm | Hard-coded `1.0 * voltage`, reported mS/cm |

| Node 4 turbidity ADC reference | Real voltage at the ESP32 pin (5.0 V reference removed) | Scaled as if a 5.0 V reference applied |

| Node 4 upstream cleaning | `cleanUpstreamPacket()` removes `AT:` and `AH:` | No token cleaning |

!!! warning "Turbidity readings are not comparable across the two trees"

    The current firmware corrected the turbidity ADC reference. A turbidity value

    produced by a legacy build and one produced by a current build are **not

    comparable**, because the legacy path applied an incorrect voltage reference.

    See [Turbidity → Calibration](../calibration/turbidity.md).

## Legacy inventory

All paths are relative to the firmware repository root

([`lestealthy/Cirqua`](https://github.com/lestealthy/Cirqua) at commit

`db6d9b8`).

| Legacy unit | Path | Status | Role |

|---|---|---|---|

| Controller master | `_OLD/cirqua/cirqua.ino` | Historical | Arduino Mega master, see below |

| Node 1 | `_OLD/Node1/Node1.ino` | Historical | Tank A level, LCD, single-loop UART |

| Node 2 | `_OLD/node2_fixed/node2_fixed.ino` | Historical | Water sensors, bidirectional UART |

| Node 3 | `_OLD/node3_fixed/node3_fixed.ino` | Historical | Flow metering and forwarding |

| Node 4 | `_OLD/Node4/Node4.ino` | Historical | Water-quality analytics |

| Cluster dump | `_OLD/all_code_cluster.txt` | Historical | Concatenated cluster text |

## The legacy Arduino Mega controller

`_OLD/cirqua/cirqua.ino` is **not a CIRQUA node**. Its internal title is

`Cirqua_Node5_Master.ino`, and it is the controller that the current Node 4

forwards telemetry to — the `// To Controller (Mega)` comment on Node 4's UART2

pins refers to this role.

Its documented USB serial protocol was:

| Command | Behaviour |

|---|---|

| `SET_JP<num>:1|0` | Drive jumper output `num` (1–20); replies `ACK` |

| `READ_JP<num>` | Reply `JP<num>:1` (on, active low) or `JP<num>:0` (off) |

| `READ_SENSORS` | Reply with one JSON line built from the cached telemetry |

| `KILL` | Force all outputs off and report all sensors as zero; replies `ACK` |

| `RESET` | Clear the kill state, all outputs off; replies `ACK` |

It parsed the incoming chain stream with an `extractValue()` helper over the same

`|KEY:value;` token format that the current nodes still use, and cached

`TAV`, `DO`, `Temp`, `TBV`, `FLM`, `pH`, `Turb`, `EC` and `TCV` into globals.

!!! warning "The controller is not part of the current firmware tree"

    No equivalent Mega controller source exists under

    `FreeRTOS_Implementation/`. The current chain therefore terminates at a

    controller whose implementation is not published in this repository. The

    frame that Node 4 emits is documented in

    [Message format](../communication/message-format.md), but the receiver is

    **not verified from the current source**.

## Node 3: two legacy bugs worth recording

The legacy Node 3 sketch documents its own defects in comments, which makes it a

useful design record.

```cpp

--8<-- "assets/snippets/legacy-node3-ping.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/_OLD/node3_fixed/node3_fixed.ino">lestealthy/Cirqua</a> ·

<code>_OLD/node3_fixed/node3_fixed.ino</code> ·

<span class="cirqua-badge cirqua-badge--historical">Historical</span> ·

lines 1–40 · commit <code>db6d9b8</code>
</div>

| Legacy defect | Comment in source | How the current Node 3 differs |

|---|---|---|

| Timing drift | `lastFlowMillis += 1000; // Fixed timing drift bug` | FreeRTOS `vTaskDelayUntil` wakes at a fixed period with no accumulating drift |

| Timeout spam | `lastReceivedTime = millis() + 100000; // Mutes spam until new data resets it` | A `timeoutAlertSent` flag mutes the fallback until a valid frame is received |

| Non-atomic counter | `noInterrupts()` / `interrupts()` around a `uint16_t` counter | `portENTER_CRITICAL` around a `volatile uint32_t` counter with `IRAM_ATTR` ISR |

The legacy fallback frame was also structurally different: it omitted `TAV` and

`DO` entirely, emitting only `node1:0|node2:0|FLM:…|node3:…`. The current Node 3

emits a complete frame with zeroed values so the receiver's structural

validation still succeeds.

## Related pages

* [Source map](../firmware/source-map.md) — where each documented behaviour lives in the current tree

* [Firmware repository](../firmware/repository.md) — repository layout and revision pinning

* [Revision history](../firmware/revision-history.md) — what Git actually records

* [Known limitations](../validation/known-limitations.md) — unresolved issues in the current tree
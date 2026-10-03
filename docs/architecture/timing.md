---
title: Timing
description: Task periods, poll cadence, lock timeouts and RX timeouts for the CIRQUA ESP32 node chain, and how they bound end-to-end data latency.
---

# Timing

## Task periods

Every periodic task is driven by `vTaskDelayUntil`, so periods are nominal
cadences rather than fixed intervals — each activation is scheduled from the
previous *scheduled* time, not from the previous wake-up.

| Node | Task | Function | Core | Period | Implied rate |
|---|---|---|---|---|---|
| 1 | `N1_Sensors` | `Task_Sensors_Node1` | 1 | 500 ms | 2 Hz |
| 1 | `N1_UART` | `Task_UART_Node1` | 0 | 1 ms loop | 1 kHz |
| 1 | `N1_LCD` | `Task_LCD_Node1` | 1 | 500 ms | 2 Hz |
| 2 | `N2_Sensors` | `Task_Sensors_Node2` | 1 | 1000 ms | 1 Hz |
| 2 | `N2_UART` | `Task_UART_Node2` | 0 | 50 ms | 20 Hz |
| 3 | `N3_Flow` | `Task_Flow_Node3` | 1 | 1000 ms | 1 Hz |
| 3 | `N3_UART` | `Task_UART_Node3` | 0 | 50 ms | 20 Hz |
| 4 | `N4_Sensors` | `Task_Sensors_Node4` | 1 | 1000 ms | 1 Hz |
| 4 | `N4_UART` | `Task_UART_Node4` | 0 | 50 ms | 20 Hz |
| 4 | `N4_LCD` | `Task_LCD_Node4` | 1 | 500 ms | 2 Hz |
| 4 SMTP | `N4_EmailUART` | `Task_Email_And_UART_Node4` | 0 | 50 ms | 20 Hz |

Two observations follow directly from this table:

* **The UART tasks all run at priority 3, the highest on the node**, and all run
  on core 0. Link handling cannot be starved by sensor work.
* **The slowest measurement in the chain is 1 Hz.** Node 2's water temperature,
  Node 2's dissolved oxygen, Node 3's flow rate and all of Node 4's chemistry
  are each updated once per second at best. Faster display or forwarding does
  not make the data fresher.

## Sensor-internal timing

| Constraint | Value | Where |
|---|---|---|
| Node 1 ultrasonic timeout | 30000 µs | worst-case echo wait in the 500 ms sensor task |
| Node 2 ultrasonic timeout | 20000 µs | 1000 ms sensor task |
| Node 4 ultrasonic timeout | 25000 µs | 1000 ms sensor task |
| Ultrasonic trigger pulse | 2–3 µs low, 10 µs high | all three ultrasonic nodes |
| DHT11 minimum read interval | 2000 ms | paced by `xLastDHTTick`; enforced on Node 2 and Node 4 |
| Node 2 DS18B20 conversion | non-blocking | `setWaitForConversion(false)` + `requestTemperatures()` each cycle |
| Node 4 DS18B20 conversion | **blocking, by design** | `setWaitForConversion(true)` at 10-bit resolution (0.25 °C); the source comment states ~187.5 ms is acceptable at 1 Hz |

Node 4's blocking DS18B20 conversion is the single largest synchronous block in
a sensor task. At a 1000 ms period it consumes roughly 19 % of the task's
budget. It does not block the UART task, because those are on different cores.

## Lock timeouts

Mutex waits are bounded. If the timeout expires the code proceeds without the
lock — it does not block indefinitely.

| Timeout | Applies to |
|---|---|
| 50 ms | Sensor commit |
| 20 ms | UART snapshot |
| 10 ms | Node 1 transmit snapshot |

`systemFatalTrap` is used when a mutex cannot be created at all. It halts the
node and uses `vTaskDelay`, not a busy loop.

Node 3's shared `g_pulseCount` is protected by `portENTER_CRITICAL` /
`portEXIT_CRITICAL` around a `portMUX_TYPE`, not by a mutex, because it is
written from an ISR on the **falling** edge of GPIO 23.

## RX timeouts

| Timeout | Value | Behaviour when exceeded |
|---|---|---|
| Node 1 `RX_TIMEOUT_MS` | 3000 ms | Node 1 LCD status line shows `ERROR` instead of a normal state |
| Node 3 `TIMEOUT_MS` | 2000 ms | Node 3 emits a **substitute frame once**, then mutes further fallbacks until upstream resumes |

The Node 3 fallback frame is:

```
|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:%.2f|node3:%d;\n
```

!!! warning "The fallback is structurally valid"
    It contains the expected keys, so `validateUpstreamFrame` passes. A
    downstream consumer that checks only key presence cannot distinguish it from
    a genuine reading. It is also emitted **once** — so the visible symptom of a
    long upstream outage is a single zero-filled record, not a stream of them.

Node 1's LCD status precedence, in order, is: no frame ever received → `WAITING`;
`millis() - lastRx > 3000` → `ERROR`; then `HOT+HUM`, `OVERTEMP`, `HI HUMID`,
`LOW C+F`, `LOW TAV`, `LOW TBV`, `FAULT` (when `node2Health` is false) and
finally `NORMAL`.

## Transmission cadence

Frame emission happens inside the UART tasks, so its ceiling is the UART task
period.

| Node | Emits | Bounded by |
|---|---|---|
| 1 | The originating `TAV` frame and any re-send of merged state | 1 ms UART loop |
| 2 | The reverse echo to Node 1, and the forwarded frame to Node 3 | 50 ms poll (20 Hz) |
| 3 | The forwarded frame to Node 4, or the one-shot fallback | 50 ms poll (20 Hz) |
| 4 | The assembled packet to the controller | 50 ms poll (20 Hz) |

> **Not verified from the current source.** The exact per-frame send rate, any
> deliberate inter-frame gap or rate limiter, and any retry logic. What the
> audited source fixes is the containing task period; the number of frames put on
> the wire per activation is not stated.

## Latency budget

> **Engineering interpretation.** The following is a worst-case reading of the
> task table, not a measured figure. No timing measurement exists in the
> repository.

A value seen by the downstream controller is at least one sensor cycle old at
the node where it was measured, and each hop adds up to one poll period of
queueing:

| Stage | Contribution |
|---|---|
| Node 1 measurement age at emission | up to 500 ms (500 ms task period) |
| Node 1 → Node 2 queueing | up to 50 ms |
| Node 2's own data age at emission | up to 1000 ms |
| Node 2 → Node 3 queueing | up to 50 ms |
| Node 3's own data age at emission | up to 1000 ms |
| Node 3 → Node 4 queueing | up to 50 ms |
| Node 4's own data age at emission | up to 1000 ms |
| Node 4 → controller queueing | up to 50 ms |
| **Indicative worst-case age of Node 1's `TAV` at the controller** | **≈ 3.7 s** |
| **Indicative worst-case age of Node 4's `pH` at the controller** | **≈ 1.1 s** |

The figures are not additive in practice because the tasks are independent, but
they set the correct order of magnitude: **the chain adds roughly 150 ms of
queueing on top of whatever age the originating measurement already had.** A
value that looks a second or two old at the controller is normal, not a fault.

## What happens when the 20 Hz poll overruns

The 50 ms (20 Hz) UART polls on Nodes 2, 3 and 4 are the highest-priority tasks
on their nodes, but they are still not preemptible against other work on core 0,
and they can be delayed by work on core 1 through shared-memory contention and
mutex waits.

* **Because the periods are `vTaskDelayUntil`-based, a missed activation is not
  back-to-back.** The next wake-up is rescheduled from the previous scheduled
  time, so a long overrun results in a *shorter* following gap while the task
  catches up — it does not accumulate a permanent lag.
* **An overrun does not corrupt the frame.** The receive index is only advanced
  as characters arrive; a pause simply means the frame takes longer to complete.
* **The realistic consequence is a delayed frame**, and therefore a value that
  is older than the table above suggests.
* **A long enough overrun approaches the receiver's timeout.** If a link delivers
  no complete frame within Node 3's 2000 ms window, Node 3 substitutes its
  one-shot fallback. Node 1 raises `ERROR` after 3000 ms.

!!! note "Not verified from the current source."
    Measured execution times, CPU loading, jitter figures and a verified
    worst-case end-to-end latency. None of these are recorded in the repository.
    See <a href="../validation/known-limitations.html">Known Limitations</a>.

## Continue

* <a href="../rtos/scheduling.html">RTOS: Scheduling</a>
* <a href="../rtos/tasks.html">RTOS: Tasks</a>
* <a href="../rtos/synchronisation.html">RTOS: Synchronisation</a>
* <a href="data-flow.html">Data Flow</a> — what each hop carries

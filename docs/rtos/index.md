---
title: RTOS
description: The CIRQUA concurrency model — tasks pinned to ESP32 cores, mutex-guarded shared structs, periodic vTaskDelayUntil timing and ISR critical sections.
---

# RTOS

## `setup()` and `loop()` are not the runtime

**Firmware implementation.** Every node is an Arduino ESP32 sketch, but the
Arduino entry points are only used for initialisation. `setup()` creates the
tasks and hardware handles, and then `loop()` calls:

```cpp
vTaskDelete(NULL);
```

`NULL` here means *the calling task* — that is, the Arduino `loopTask`. It
deletes itself. From that point on, **only FreeRTOS tasks exist on the node**.
There is no background Arduino loop competing for the CPU, and nothing runs
outside a task except interrupts.

This matters for everything else in this section: a function that is not called
from a task body or an ISR does not execute, regardless of where it is
declared in the `.ino`.

## The concurrency model

Every node follows the same three-part shape:

| Part | What it is | Where |
|---|---|---|
| **Acquisition** | A sensor task that samples hardware and writes results into a shared global struct | Core 1, priority 2 |
| **Transport** | A UART task that reads the links, forwards frames and snapshots the shared structs under a mutex | Core 0, priority 3 |
| **Presentation** | An LCD task on Nodes 1 and 4 that renders a snapshot of the same structs | Core 1, priority 1 |

**Firmware implementation.** Node 3 replaces the sensor task with a flow task
(`N3_Flow`), and has no LCD task. Node 2 has no LCD task either. Node 4's SMTP
variant replaces the plain UART task with a combined
`Task_Email_And_UART_Node4` and a larger 5120-word stack.

## Core affinity

**Firmware implementation.** Every task is created with
`xTaskCreatePinnedToCore`:

* **Core 0** carries the UART tasks (priority 3) on all four nodes.
* **Core 1** carries the sensor and LCD tasks (priority 1 and 2).

**Engineering interpretation.** Pinning all serial servicing to one core and
all sensing to the other means a long blocking sensor operation — such as
Node 4's DS18B20 conversion — cannot delay the UART task, and a burst of serial
traffic cannot delay acquisition. The split also keeps core 0's behaviour more
predictable, since the ESP32's Wi-Fi and Bluetooth radio stack lives on core 0
by convention and would otherwise contend with serial servicing on the SMTP
variant.

Full reasoning in <a href="scheduling.html">Scheduling</a>.

## Inter-task data exchange

!!! important "No FreeRTOS queues are used"

    This firmware does **not** use FreeRTOS queues, counting semaphores used as
    notifications, or event groups. There is not a single `xQueueCreate`,
    `xQueueSend` or `xQueueReceive` call in the cluster.

    Instead, all inter-task data exchange is:

    1. **Shared global structs**, written by the sensor task and read by the
       UART and LCD tasks, with mutual exclusion provided by
       `xSemaphoreCreateMutex()`.
    2. **Fixed-size C character buffers**, used only to reassemble incoming
       serial bytes into frames.

    Details, including every buffer size and overflow behaviour, are in
    <a href="queues.html">Queues and Buffers</a>.

## Failure policy

**Firmware implementation.** If **any** mutex or task creation fails, the node
calls `systemFatalTrap()`, which stops the node rather than continuing
partially initialised. `systemFatalTrap` uses `vTaskDelay`, not a busy loop,
so it does not hard-lock the CPU before halting.

The design intent — **engineering interpretation** — is that a node running with
a missing mutex would have unprotected shared structs and could publish torn or
garbage telemetry. Halting is preferable, because a halted node produces a
visible absence that the upstream timeout logic can detect, whereas silent
corruption cannot.

## This section

| Page | What it covers |
|---|---|
| <a href="tasks.html">Tasks</a> | Authoritative task table — names, functions, stacks, priorities, cores and periods — plus a relationship diagram |
| <a href="queues.html">Queues and Buffers</a> | The shared structs and serial buffers that replace queues, and their overflow behaviour |
| <a href="synchronisation.html">Synchronisation</a> | Mutex inventory, lock timeouts, and the `portMUX_TYPE` critical section on Node 3 |
| <a href="scheduling.html">Scheduling</a> | Priority hierarchy, core rationale, periodicity and what happens on overrun |

## Related pages

* <a href="../architecture/system-architecture.html">System Architecture</a> —
  the layered view.
* <a href="../architecture/timing.html">Timing</a> — end-to-end latency budget.
* <a href="../communication/index.html">Communication</a> — the links these
  tasks service.

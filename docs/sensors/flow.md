---
title: Flow Rate
description: Pulse-counting flow metering on Node 3 (GPIO 23) — FALLING-edge ISR, critical-section counter, 5.5 pulses/litre calibration and the 1 Hz L/min recomputation.
---

# Flow Rate

Flow is measured on **Node 3 only**, which exists solely for this purpose. The
sensor presents a pulse train; the firmware counts pulses in an interrupt
service routine and converts a one-second count into a volumetric flow rate in
litres per minute.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Node</span>
    <span class="cirqua-identity__value">3 (only)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">GPIO</span>
    <span class="cirqua-identity__value"><code>PIN_FLOW_SENSOR</code> <code>23</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Interface</span>
    <span class="cirqua-identity__value">Digital pulse input, configured <code>INPUT_PULLUP</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Signal type</span>
    <span class="cirqua-identity__value">Interrupt-driven pulse count on the **FALLING** edge</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Firmware reading function</span>
    <span class="cirqua-identity__value"><code>pulseISR()</code> → <code>Task_Flow_Node3</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Output unit</span>
    <span class="cirqua-identity__value">L/min</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Status</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--unknown">device unverified</span></span>
  </div>
</div>

## Purpose and measured quantity

Node 3 carries a single measurement: the volumetric flow rate in the line
between Feeding Tank B and the effluent side. It is carried in the frame as the
`FLM` field, in **litres per minute**.

Node 3 has no LCD and no analogue inputs. Its entire sensor function is this
one channel.

## Physical principle

> **Manufacturer specification.** **Not verified from the current source.** The
> firmware contains no manufacturer name or part number for the flow sensor.
> Whether it is a Hall-effect turbine, an impeller, a magnetic reed or another
> mechanism is not established, and no K-factor, minimum flow rate, maximum flow
> rate, pressure loss, pulse specification or accuracy figure is asserted on
> this page.

Generic principle, common to the sensor class the firmware implies by using
`INPUT_PULLUP` and a FALLING-edge interrupt: an open-collector or open-drain
output pulls its line low once per unit volume that passes through the sensor
body. A rotating or oscillating element interrupts an internal magnetic circuit
on each pass, and each event produces one low-going edge. Counting edges over a
known interval and dividing by a pulses-per-unit-volume constant gives a
volumetric flow rate.

The `INPUT_PULLUP` configuration and the FALLING-edge interrupt are consistent
with such an open-drain output: the pull-up holds the line high while the
transistor is off, and each sensed event pulls it low.

## Electrical interface

A single digital input.

| Property | Value |
|---|---|
| Pin | GPIO 23 |
| Mode | `INPUT_PULLUP` — internal pull-up enabled, no external pull-up assumed |
| Interrupt edge | `FALLING` |
| ISR location | IRAM (`IRAM_ATTR`) |
| Counter | `volatile uint32_t g_pulseCount` |
| Mutual exclusion | `portMUX_TYPE` + `portENTER_CRITICAL` / `portEXIT_CRITICAL` |

```cpp
#define PIN_FLOW_SENSOR   23

#define FLOW_CAL_FACTOR   5.5f
#define TIMEOUT_MS        2000
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·
pin and constant definitions · lines 15–23 · commit <code>db6d9b8</code>
</div>

!!! NOTE
    The internal ESP32 pull-up is weak. For a cable run of any appreciable
    length, a floating input will be susceptible to noise. The firmware relies
    on the internal pull-up alone and the source documents no external
    conditioning, Schmitt trigger or cable shielding. Cable type, length and
    routing are **Not verified from the current source.**

## How CIRQUA uses it

### The interrupt service routine

```cpp
--8<-- "assets/snippets/node3-pulse-isr.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·
<code>pulseISR</code> · lines 15–23 · commit <code>db6d9b8</code>
</div>

The ISR increments a single free-running 32-bit counter and returns. It does no
work of any other kind — no filtering, no debounce, no pulse-width measurement,
no queue post.

The critical section protects the counter against the 32-bit read/write tearing
that would otherwise occur on a dual-core ESP32, since the sensor task reads
the counter while the ISR writes it.

### The rate computation

```cpp
--8<-- "assets/snippets/node3-flow-task.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·
<code>Task_Flow_Node3</code> · lines 43–69 · commit <code>db6d9b8</code>
</div>

The task runs at 1 Hz via `vTaskDelayUntil`. Each cycle it atomically reads the
counter, resets it to zero, and divides:

```text
flow_L_per_min = pulses_in_this_second / 5.5
```

The division is valid as L/min because the measurement window is exactly one
second: the count *is* the litres that passed, and litres-per-second equals
litres-per-minute numerically.

### The calibration constant

| Constant | Value | Meaning |
|---|---|---|
| `FLOW_CAL_FACTOR` | `5.5f` | Pulses per litre |

`5.5f` is a compile-time constant. It is a single K-factor expressed in pulses
per litre, which is the inverse of the more usual pulses-per-litre convention
used by some vendors. It is **not adjustable at runtime** and is **not stored in
NVS**.

> **Engineering interpretation.** 5.5 pulses/litre corresponds to
> approximately 3 087 pulses per US gallon, which is within the range of the K
> factor quoted for some common small flow meters. This is an observation about
> plausibility, not a verification: the fitted device is
> **Not verified from the current source**, and no measurement in the repository
> establishes that 5.5 is correct for it.

### Validity

```cpp
currentFlow.isValid = true;
```

The flow validity flag is **unconditionally true**. There is no condition under
which Node 3 reports its flow reading as invalid. This is worth stating plainly
because the flag participates in the cluster-wide health reporting.

### Frame integration

Node 3 forwards the upstream frame and appends its own field:

```text
upstream | FLM:%.2f | node3:%d;
```

If the upstream frame has been silent for longer than `TIMEOUT_MS` (2000 ms),
Node 3 emits a single fallback frame and then mutes that fallback:

```text
|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:%.2f|node3:%d;
```

The fallback concerns *upstream* data, not the flow channel — `FLM` in the
fallback frame is still a genuine measurement.

## Calibration

There is no runtime calibration path. The K-factor is a compile-time literal.

| Item | Adjustable? | Mechanism |
|---|---|---|
| `FLOW_CAL_FACTOR` (5.5) | No | Compile-time constant, edit and re-flash |
| Measurement window (1 s) | No | Compile-time, `pdMS_TO_TICKS(1000)` |
| Any offset, linearisation or pulse-width filter | Not implemented | — |

**Practical consequence:** if the K-factor is wrong for the fitted sensor, every
flow reading in the dataset is wrong by the same proportion, and the only
correction available is to re-flash the node. A volumetric check — comparing
`FLM` integrated over a known interval against a measured draw from the tank —
is the only way to establish the correct factor.

No calibration page exists for flow metering in the current documentation
structure, because there is nothing to calibrate through the firmware.

## Expected values and typical ranges

Derivable **strictly from the firmware**:

* Output unit: **L/min**, formatted `%.2f`.
* K-factor: **5.5 pulses/litre**.
* Measurement window: **1 second**, hence one update per second.
* Minimum non-zero resolvable reading: **1 / 5.5 = 0.18 L/min** — one pulse in a
  one-second window. Resolution is therefore quantised to about 0.18 L/min.
* Maximum unambiguous reading: bounded by what the hardware can count, and
  limited in practice by ISR response time rather than by the 32-bit counter.
* Validity flag: **always valid**, unconditionally.
* Reported as exactly `0.00` when no pulses arrive in a cycle — which is
  indistinguishable from a disconnected sensor.

Pipe size, working flow range, minimum flow below which the sensor does not
produce pulses, and achievable accuracy:

> **Not verified from the current source.** No datasheet, no part number and no
> field data are available to this documentation set.

## Failure modes

This channel has **no invalid state**. Every one of the following conditions is
reported as a valid flow reading:

* Sensor disconnected, or its output left floating.
* Sensor fitted but not primed — no flow, so `0.00` L/min, reported valid.
* Impeller jammed or partially obstructed — a reduced but plausible rate.
* Reverse flow, which produces the same positive L/min reading as forward flow,
  because the firmware counts edges and applies no direction information.
* Air lock or partial dry running.

What a field technician should look for:

* **`FLM:0.00` while water is visibly moving.** The strongest available
  indicator, because there is no fault flag to corroborate it. Cross-check
  against the upstream level channels: if `TBV` is falling, flow should be
  non-zero.
* **A constant reading with no correlation to upstream level change.** Compare
  against Node 2's `TBV` and Node 4's `TCV` — a flow channel that disagrees
  with the level channels is the practical fault test available.
* **A reading that scales with something other than flow.** Noise on a long or
  unshielded run with only the weak internal pull-up can inject counts. Because
  there is no pulse-width plausibility check, a noisy input can read as a low
  but persistent positive flow.
* **An implausibly high rate.** ISR latency at very high pulse rates will
  undercount; the firmware cannot report undercount, because the counter
  wrapping or missing edges is invisible to it.

Field verification note: the raw pulse count for the cycle is not exposed on
the debug serial port and cannot be read back through the frame, since only the
already-divided L/min value is transmitted. Diagnosing this channel means
observing the physical flow or instrumenting the node.

## Environmental considerations

* **Line position and orientation.** Flow meters of this class are usually
  orientation-sensitive and may need to be kept full of water. A dry or
  partially filled body will produce no pulses and no fault indication.
* **Air in the line.** Entrained air interrupts the flow of water across the
  sensing element and the pulse train stops. This is indistinguishable from
  zero flow at the firmware level.
* **Suspended solids and biofilm.** Build-up on an impeller reduces the pulse
  rate for a given true flow, producing a progressive under-reading that the
  firmware cannot detect.
* **Electrical noise.** The internal pull-up is the only protection against a
  noisy long cable run. This is a wiring concern, not a firmware one, and the
  repository contains no schematic or cable documentation against which to
  check it.
* **Supply stability.** Any brownout or reset of the ESP32 clears the pulse
  counter and produces a spurious zero for the first cycle afterwards.

## Limitations

Firmware-level limitations, stated plainly:

* **No overflow detection.** The counter is a free-running `uint32_t` that is
  reset every second, so wrap-around in practice cannot occur at realistic
  rates — but there is no check that the counter did not wrap *between* the
  read and the reset, and no wrap accounting anywhere.
* **No pulse-width plausibility check.** The ISR counts edges without measuring
  the interval between them. Bounce from a mechanically vibrating or
  intermittently-contacting sensor is counted as flow; there is no minimum
  interval filter and no debounce of any kind.
* **No validity flag under any condition.** `isValid` is hard-coded true.
* **No direction detection.** Reverse flow is reported as positive forward
  flow.
* **No totalising.** Only an instantaneous rate is reported. Integrating the
  rate to obtain a volume over time is the consumer's responsibility, and any
  gap in the frame stream becomes a gap in the total.
* **Single K-factor, compile-time only.** No runtime adjustment, no NVS
  storage, no serial console command.
* **Quantised resolution of about 0.18 L/min.** Low flow cannot be represented.
* **No zero-flow timeout.** A stuck-at-zero condition is indistinguishable from
  genuine zero flow.
* **No diagnostic output.** The raw pulse count is not exposed on the debug
  serial port or in the frame.
* **Intermittent ISR miscounting is undetectable.** At high pulse rates the ISR
  may not keep up; the resulting error is silent.

## Maintenance and replacement

Replacing the flow sensor is a wiring operation, but it must be followed by a
K-factor verification, because the firmware cannot be told what the new device's
pulses-per-litre is. A volumetric cross-check against a known draw is the only
available verification.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md).
Routine checks: [Maintenance](../field-service/maintenance.md).
Startup verification: [Startup Checklist](../field-service/startup-checklist.md).

> **Not verified from the current source.** Sensor part number, pipe size,
  cable type, length, gauge and connector pinout. No schematic exists in the
  repository.

## Where it is used

| Node | GPIO | Interface | Reading function | Frame field | Valid flag |
|---|---|---|---|---|---|
| 3 | 23 (`PIN_FLOW_SENSOR`) | Digital pulse, `INPUT_PULLUP`, FALLING ISR | `pulseISR` → `Task_Flow_Node3` | `FLM` | `node3` (always valid) |

The reading is consumed by:

* Node 3's UART task, which appends `FLM:%.2f` to the upstream frame before
  forwarding it to Node 4;
* the downstream controller, via Node 4.

Upstream timeout behaviour and frame handling:
[Message Format](../communication/message-format.md),
[Fault Handling](../communication/fault-handling.md).
Node detail: [Node 3](../nodes/node3.md).

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),
branch `main`, commit
[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)
(short `db6d9b8`).

| Snippet | Source path | Symbol | Lines |
|---|---|---|---|
| `node3-pin-definitions` | `FreeRTOS_Implementation/Node3/Node3.ino` | — | 3–13 |
| `node3-pulse-isr` | `FreeRTOS_Implementation/Node3/Node3.ino` | `pulseISR` | 15–23 |
| `node3-flow-task` | `FreeRTOS_Implementation/Node3/Node3.ino` | `Task_Flow_Node3` | 43–69 |
| `node3-uart-forwarding` | `FreeRTOS_Implementation/Node3/Node3.ino` | `Task_UART_Node3` | 82–154 |

Everything on this page is *firmware implementation*. No manufacturer
specification for the flow sensor exists in the source, and none is asserted.

Related: [Sensors overview](index.md) ·
[Sensor Replacement](../field-service/sensor-replacement.md) ·
[Known Limitations](../validation/known-limitations.md)

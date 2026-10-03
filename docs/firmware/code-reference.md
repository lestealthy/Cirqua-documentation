---
title: Code Reference
description: A guided tour of the CIRQUA firmware by engineering concern, with the real snippets and the reasoning behind each design choice.
---

# Code Reference

[Source Map](source-map.md)) tells you *where* a symbol lives. This page walks
through *why the code is shaped the way it is*, one concern at a time, with the
relevant snippet embedded and a permalink to the pinned commit.

Two rules govern how the rationale is written:

* Where the firmware's own comments state the reason, that is quoted as a
  **source comment**.
* Where the reason is inferred from the shape of the code, it is labelled
  **Engineering interpretation**. That label means the documentation author
  reasoned about the code; it is not a claim made by the firmware.

Everything here is read from commit
[`db6d9b8`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55).

## Sensor acquisition

**What it is.** Each node runs exactly one acquisition task, pinned to core 1,
which measures every local sensor once per period and commits the result into a
single guarded struct. The periods are 500 ms on Node 1 and 1000 ms on Nodes 2,
3 and 4. Node 1 samples twice as often as the rest because it has the smallest
sensor set and the fastest-changing quantity of the cluster — the collection
tank volume, which is the quantity that has to be right before anything else.

**The pattern is identical across the four nodes:** take a snapshot of the
existing state under the mutex at the top of the cycle, measure into a local
copy, then commit the whole struct back under the mutex at the end. Node 2's
comment says it plainly: *"Fetch current values under lock to keep prior valid
state if needed."* Each measurement independently sets or clears its own validity
flag, so one failing probe does not discard the other readings. That
per-quantity validity flag is what later becomes the `node1:`/`node2:`/`node3:`/
`node4:` health field on the wire, and what the LCD and the SMTP fault logic
consume.

> **Engineering interpretation.** Copying the struct in and out under the lock,
> rather than locking each field, keeps the critical section to a fixed-size
> struct copy and avoids a long lock hold during the sensor conversions — which
> matter on Node 4, where a single cycle includes two blocking DS18B20 reads, six batches of 16 ADC samples and an ultrasonic echo wait. The cost is that a snapshot is briefly stale relative to the newest measurement, which is harmless at 1 Hz.

Lock timeouts are explicit and short: 50 ms for a sensor commit, 20 ms for a
UART snapshot, 10 ms for Node 1's transmit snapshot. Every `xSemaphoreTake` in
the cluster is bounded this way, and a failed take simply skips the update for
that cycle.

## The ultrasonic measurement primitive

```cpp
--8<-- "assets/snippets/node1-ultrasonic-measurement.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·
<code>Task_Sensors_Node1</code> · lines 77–116 · commit <code>db6d9b8</code>
</div>

**The shape.** Pulse TRIG low for a few microseconds, high for 10 µs, low again;
then a single blocking `pulseIn()` on ECHO with a timeout; convert
`duration × 0.0343 / 2` to a distance; subtract from `TANK_HEIGHT`; multiply by
the cylinder area over 1000 to get litres.

**Why.** The 10 µs high pulse is the documented trigger width for this class of
sensor, and the divide-by-two is the round trip. The value `0.0343f` is the speed
of sound in air at room temperature in centimetres per microsecond — Node 1's own
comment calls this the *"True 0-offset ultrasonic calculation"*, i.e. the code
deliberately assumes the transducer face sits exactly at the configured tank
height, with **no** sensor offset correction and no temperature compensation on
the speed of sound. That is a calibration decision, and it is stated in the code
rather than hidden.

**The three per-node variations are the interesting part.** Node 1 waits 30 ms
(≈5.1 m of range), Node 2 waits 20 ms, Node 4 waits 25 ms. Node 2 clamps the
computed height into `[0, TANK_HEIGHT]`; Node 4 does the same **and** rejects an
implausible distance outright:

```cpp
// Reject physically impossible measurements
if (distance < 0.0f ||
    distance > TANK_HEIGHT + 20.0f) {
    return false;
}
```

That guard exists only on Node 4, and its comment says so. Node 4 is the tail
node whose numbers are consumed by the downstream controller and, on the SMTP
variant, by e-mail, so its author applied a plausibility filter that the
upstream nodes do not have. The consequence is an asymmetry worth knowing: a
short spurious echo on Node 1 or Node 2 becomes a *valid* full-tank reading,
while on Node 4 it becomes an *invalid* reading.

**The unexplained factor of two.** Node 1 then does
`currentRead.volumeLiters = (int)(volumeLiters * 2.0f);`. Nothing in the
cylinder formula produces that factor, and no comment explains it.

> **Engineering interpretation.** This is an empirical fudge factor. The most
> plausible reading is that it compensates for something geometric that the
> constants do not describe — a non-cylindrical tank, a sump, a tilted
> transducer, or a reconciliation against a manual measurement. It is
> *not* derivable from `TANK_HEIGHT` and `TANK_RADIUS`, and it means `TAV` must
> be treated as requiring empirical calibration rather than as a computed
> geometry. Documented in full on
> [Ultrasonic Level](../sensors/ultrasonic.md)) and in the
> [limitations register](../validation/known-limitations.md).

## The DS18B20 state machine

Two nodes use 1-Wire temperature probes, and they chose **opposite**
strategies — which is the clearest evidence in this firmware that the two were
written at different times by different reasoning.

**Node 2 uses non-blocking conversion.** It calls
`setWaitForConversion(false)` and `requestTemperatures()` once at task start and
once per cycle, so each cycle reads whatever the previous conversion produced.
The library's state machine absorbs the 750 ms conversion time at 12-bit and the
1000 ms task period covers it.

**Node 4 uses blocking conversion, deliberately.** Its comment states the
reason: *"We intentionally use blocking conversion here. At 10-bit resolution the
conversion takes approximately 187.5 ms, which is completely acceptable because
the sensor task runs at 1 Hz."* Node 4 also drops the resolution to 10 bits
(0.25 °C), which is what makes 187.5 ms acceptable in the first place. Choosing
resolution to fit a deadline, rather than fitting the deadline to the resolution,
is the design decision here.

Both reject `DEVICE_DISCONNECTED_C`, and both apply a plausibility window
(`−55 … 125 °C`). Node 4 goes one step further at boot: it prints the device
count and warns explicitly if it is zero, and it skips the conversion entirely
when `getDeviceCount() == 0` rather than repeatedly asking an empty bus.

**Consequence for the rest of Node 4:** the submerged temperature is not merely
a reading, it is the compensation input for both pH and conductivity. When the
DS18B20 is invalid, both conversions substitute 25 °C and continue — the node
degrades to an uncompensated measurement rather than to an invalid one. That is
a deliberate availability-over-accuracy trade, and it is invisible unless you
read the code.

## DHT pacing

Every DHT read on both nodes is gated by a `xLastDHTTick` timestamp so that at
most one read happens every 2000 ms, even though the acquisition tasks run at
1000 ms. The check is `xLastDHTTick == 0 || now - xLastDHTTick >= pdMS_TO_TICKS(2000)`.

> **Engineering interpretation.** The DHT11 is a single-wire digital sensor with
> a multi-byte frame and a slow, power-hungry conversion; reading it far faster
> than its own conversion returns stale or checksum-failed data. The 2000 ms gate
> is a data-integrity requirement of the sensor, not a scheduling preference. The
> `xLastDHTTick == 0` clause exists so the very first cycle reads immediately
> rather than waiting two seconds.

**The two variants gate validity differently.** Node 2 accepts any non-`NaN`
reading (`!isnan(tVal)`). Node 4 additionally requires `-20 ≤ T ≤ 80 °C` and
`0 ≤ H ≤ 100 %`. The SMTP variant reverts to Node 2's looser gate.

> **Engineering interpretation.** Node 4's stricter gate is a robustness choice
> consistent with the plausibility filter it applies to pH, turbidity and EC — the
> tail node distrusts its analogue inputs more than the middle nodes do. The
> SMTP variant, being a fork of Node 4 rather than a continuation of it, does not
> inherit that change. The divergence is real and is recorded in the
> [limitations register](../validation/known-limitations.md).

Ambient temperature and humidity are **not** compensated, extrapolated or
smoothed. They are used as measured, and they drive Node 1's status string and
the SMTP variant's fault thresholds.

## ADC filtering and attenuation

```cpp
--8<-- "assets/snippets/node4-adc-configuration.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>configureADC</code> · lines 161–189 · commit <code>db6d9b8</code>
</div>

**Attenuation.** `SENSOR_ADC_ATTENUATION` is `ADC_11db`, with the comment
*"11 dB gives the largest practical input range."* Node 4's file header adds a
caveat that is worth reading before touching any analogue wiring: *"ESP32 ADC is
NOT a true 0-5V ADC. The sensor boards may be powered from 5V, but their analog
output must remain within the ESP32 ADC input range."* That is why the
per-quantity validity gates are expressed as voltage windows (`0.02 ≤ V ≤ 3.30`,
`0.0 ≤ V ≤ 3.30`) rather than as raw-count windows.

**Resolution.** 12-bit, set globally with `analogReadResolution(12)`.

**Filtering.** Two acquisition helpers exist:

```cpp
--8<-- "assets/snippets/node4-filtered-adc.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>readADCFiltered</code> · lines 194–213 · commit <code>db6d9b8</code>
</div>

`readADCFiltered` averages `ADC_SAMPLES` (16) raw counts; `readSensorVoltage`
averages 16 `analogReadMilliVolts()` readings. Both **discard the first reading
after a channel switch**, and the source comment gives the reason: *"This helps
reduce channel-to-channel ADC residue."* Between samples each call waits
150 µs, and before the loop it waits 100 µs.

> **Engineering interpretation.** This is the standard remedy for the ESP32's
> known behaviour where the SAR ADC retains charge from the previously selected
> channel, so the first conversion after a mux change is biased. The 150 µs
> spacing also allows the sample-and-hold to settle. The cost is that each
> channel acquisition blocks the sensor task for roughly 2.5 ms, and Node 4
> performs six of them per cycle.

**A cost worth flagging.** `readADCFiltered` is called for pH, turbidity and EC
in every cycle, but the resulting raw counts (`phRaw`, `turbRaw`, `ecRaw`) are
never used in any conversion — the calibrated voltage from `readSensorVoltage`
is what feeds the maths. So the firmware pays for two averaged acquisitions per
channel per second and uses one. `adcToVoltage()` is likewise declared and
commented as *"only used for diagnostics if called directly"*, computes a
millivolt total, and then returns a value derived from `3.3f` instead — it is
dead code. Both are noted in the
[limitations register](../validation/known-limitations.md) as cleanup
candidates, not as defects.

## The calibration model

```cpp
--8<-- "assets/snippets/node4-calibration-struct.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
NVS calibration declaration · lines 53–66 · commit <code>db6d9b8</code>
</div>

The calibration model is three floats — `phSlope`, `phOffset`, `ecKFactor` —
persisted in the NVS namespace `node4_cal` and loaded once at boot.

**The key design statement is a comment**, not a computation. In the pH block:

> *"Existing calibration model preserved"* — with the formula written out
> below it: `pHcalculated = slope * voltage + offset`, followed by
> *"Temperature compensation also preserved."* The EC block repeats it:
> *"Existing K-factor behavior preserved. Original: EC(mS/cm) = voltage × K"*.

This is the one place in the current firmware where legacy behaviour was kept on
purpose, and the comments say so explicitly. See
[Revision History](revision-history.md)) for why that matters for provenance.

**Why a linear slope/offset for pH.** The model is a two-point affine fit
through the operating range of the probe board, not a Nernst law. A two-point
calibration (for example against pH 4 and pH 9 buffers) is exactly what a field
technician can perform in a tank shed with two solutions, and it needs two
numbers in flash. It is the right choice for a low-cost probe and a
maintainable field procedure.

**Why a K-factor for conductivity.** Conductivity cells are linear in voltage,
so a single multiplicative K converts the analogue output to µS/cm, which is
exactly what `ecKFactor` is. The 25 °C normalisation is then applied as a
divisor, and the `× 1000` converts to µS/cm for `Node4` — the SMTP variant drops
the compensation and the `× 1000` and therefore reports **mS/cm**, which is a real
divergence between the two variants, not a documentation artefact.

**Why turbidity has none.** The turbidity path uses the vendor's published
quadratic for the named sensor module and has no field-adjustable constant at
all: `ntu = -1120.4 V² + 5742.3 V - 4353.8`, with breakpoints at `3.20 V` and
`0.50 V` and a clamp to `[0, 3000]`. Its comments also correct a legacy bug
explicitly: *"The original code used 5.0 V as the ADC reference. That is
incorrect for the ESP32 ADC measurement. The voltage here is the actual voltage
measured at the ESP32 ADC input."*

**Why validity is gated per quantity.** Each channel has its own acceptance
window, and two of them are deliberately permissive at the range ends:

| Channel | Accepted | Comment in source |
|---|---|---|
| pH | `0.02 ≤ V ≤ 3.30` **and** `0 ≤ pH ≤ 14` | *"A completely saturated / disconnected ADC signal should not be reported as a valid pH measurement."* |
| Turbidity | `0.0 ≤ V ≤ 3.30` | *"Don't automatically invalidate the turbidity sensor just because it is reading near one end of its range. Saturation is a valid physical condition."* |
| EC | `0.0 ≤ V ≤ 3.30` | *"Reject impossible ADC conditions but do not reject a zero EC value — zero/very-low conductivity is a legitimate measurement."* |

That is a coherent and defensible policy: reject a physically impossible signal,
but never reject a physically extreme one. It is worth understanding because it
means a heavily fouled turbidity probe reads `3000` and reports itself healthy.

## The frame parser

There is one integrity check in the entire firmware:

```cpp
--8<-- "assets/snippets/node3-frame-validation.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·
<code>validateUpstreamFrame</code> · lines 71–78 · commit <code>db6d9b8</code>
</div>

It is a pure key-presence test. Nodes 2 and 4 have no equivalent: they parse
whatever arrives and rely on their own parsers failing.

**Why key presence is the whole strategy.** The protocol is
delimiter-separated ASCII with no checksum, no CRC, no sequence number and no
acknowledgement. Structural validation is the only validation available. A frame
missing `|node1:` has not been truncated in the middle of a field, which is the
only corruption mode the design can detect.

**Why `strstr` on the leading pipe.** Every field is prefixed with `|`, and
because `|` also terminates the previous field, a new frame always begins with
`|`. Searching for `"|DO:"` rather than `"DO:"` is what prevents a substring
false positive, and it is why the leading pipe in every frame is not merely
cosmetic. The `TAV:` check is written twice in the source
(`strstr(frame, "TAV:") || strstr(frame, "|TAV:")`) to accept a frame that
arrives without its leading pipe.

**Two parser styles coexist.** Node 1 uses a `String` helper,
`getFieldFromFrame(packet, fieldName)`, which searches for `|name:` and then
takes the substring up to the next `|`, the next `;`, or the end. Nodes 2 and 3
use `strstr` plus `sscanf` directly on a `char*` buffer. The `String` variant is
more readable and allocates on an ESP32; the `strstr`/`sscanf` variant is
cheaper and does not. Node 1 is also the only node that commits a partially
parsed frame field-by-field — it accepts whatever keys arrived and sets
`packetValid` only if all six were present, so a partial echo still updates the
display.

**A genuine divergence worth recording.** Node 2's reverse-telemetry parser
looks for `"|FR:"`:

```cpp
--8<-- "assets/snippets/node2-parse-node3.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·
<code>parseNode3ReversePacket</code> · lines 240–254 · commit <code>db6d9b8</code>
</div>

Node 3 emits `"|FLM:%.2f"`. The key names therefore never match, so in the
current source this parser cannot succeed, and the struct it populates is not
read by any other code. The rename to `FLM` was made for the downstream
controller's benefit — Node 3's own comment says *"Standardized key name FLM for
downstream controller compatibility"* — and the Node 2 parser was evidently not
updated. No behaviour is currently broken, because nothing consumes that struct;
the cost is that the reverse-telemetry path exists in the source but does not
function.

**Overflow handling is uniform and blunt.** Every receiver resets its index to
zero when its buffer is full, discarding the partial frame. Node 1's `String`
buffer reserves 256 bytes and resets at 250; Node 2 uses `char[128]` per link;
Node 3 uses `char[256]`; Node 4 uses `char[384]` with a 512-byte assembled
packet. Nothing resynchronises mid-frame, because nothing can — without a
checksum there is no way to find the next frame boundary. See
[Fault Handling](../communication/fault-handling.md)).

## Frame construction

**Node 1 originates.** It is the only node whose value appears first in the
frame, and it emits on a fixed 500 ms timer, independent of whether anybody is
listening:

```text
|TAV:<int>|node1:<0|1>;
```

The comment *"Standardized with leading pipe"* documents the interoperability
rule described above. The value is an **integer** because Node 1 truncates the
doubled volume.

**Node 2 consolidates.** Every 50 ms it takes its own sensor snapshot plus the
last valid Node 1 data and emits a full consolidated frame downstream, then a
**separate** reduced echo upstream. Both are `snprintf`-built into stack buffers
of 256 bytes, so no frame is ever partially written by a shared `String`.

```cpp
--8<-- "assets/snippets/node2-uart-routing.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·
<code>Task_UART_Node2</code> · lines 259–370 · commit <code>db6d9b8</code>
</div>

The echo exists so Node 1 can populate its LCD without Node 1 having to parse or
understand water temperature, dissolved oxygen or ambient conditions. The
**health flag is computed once** from all five Node 2 validity flags
(`tempValid && doValid && tbvValid && atValid && ahValid`) and reused in both
frames, which guarantees the two directions can never disagree about Node 2's
health.

Every field is emitted unconditionally, with `0.0f` substituted for an invalid
value:

> **Engineering interpretation.** A fixed field set makes the frame
> self-describing in shape — a downstream parser can rely on field order and on
> never having to handle a missing key — but it makes **zero ambiguous**: a
> legitimately zero reading and a failed probe are indistinguishable on the
> wire. The only disambiguator is the health flag, and it is per node rather
> than per quantity. This is the single most consequential design consequence
> of the protocol, and it is recorded as a limitation.

**Node 3 forwards and appends.** It validates, strips the trailing `;`, and
rebuilds the frame with its own field appended. On upstream silence it emits one
fallback frame and then mutes itself — the comment *"Mute spam until link
recovers"* shows this is deliberate. The fallback deliberately sets `node1:0`
and `node2:0` so the controller sees an explicit chain failure rather than
stale values.

**Node 4 extends and cleans.** It is the only node that both *removes* and
*adds* fields; see the next section.

## The packet cleaner

```cpp
--8<-- "assets/snippets/node4-packet-cleaner.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>cleanUpstreamPacket</code> · lines 936–990 · commit <code>db6d9b8</code>
</div>

**What it does.** It walks the incoming frame token by token on `|`, drops any
token beginning `AT:` or `AH:`, and re-joins the survivors with `|`.

**Why.** Node 2 originates the ambient temperature and humidity fields for the
Node 2 enclosure. Node 4 has its **own** DHT11 and its own ambient pair. Without
the cleaner the controller would receive two `AT:` fields and two `AH:` fields
and would have to guess which is which — and the first-match-wins behaviour of a
typical parser would silently pick the wrong one. Removing the upstream pair
means the controller receives exactly one ambient pair, measured at the
water-quality enclosure next to the water.

> **Engineering interpretation.** This is a protocol-level decision implemented
> at a single point in the chain. It also means the downstream consumer is
> structurally dependent on Node 4 always being present: if Node 4 is bypassed
> or its link is down, the controller receives no `AT:`/`AH:` at all, because no
> other node regenerates them.

The implementation is a straightforward `String` scan with single-character
`indexOf`. It allocates and concatenates per frame, which is acceptable at this
frame rate but is the obvious thing to replace with an in-place buffer rewrite
if the chain ever needs to run faster.

**The SMTP variant does not clean.** `Node4_SMTP` has no equivalent function and
appends `pH`, `Turb`, `EC`, `EV` and `ST` to the raw upstream frame. Its
downstream frame therefore still carries Node 2's `AT:` and `AH:` and adds no
ambient pair of its own — even though it has a DHT11 and displays it. That is a
functional divergence between two units that share a GPIO map, and it is
recorded as a limitation.

## The interrupt service routine

```cpp
--8<-- "assets/snippets/node3-pulse-isr.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·
<code>pulseISR</code> · lines 15–23 · commit <code>db6d9b8</code>
</div>

**What it does.** On the **falling** edge of GPIO 23, it increments a
`volatile uint32_t` inside `portENTER_CRITICAL_ISR` / `portEXIT_CRITICAL_ISR`
against a `portMUX_TYPE` spinlock, and it is declared `IRAM_ATTR` so the handler
resides in IRAM rather than being fetched from flash.

**Why each of those three choices.**

* `IRAM_ATTR` — during flash operations the cache is unavailable, so an ISR
  living in flash cannot run. The standard requirement.
* `volatile` — guarantees the compiler re-reads the counter instead of caching
  it in a register across the loop.
* `portMUX_TYPE` + critical section — on a dual-core ESP32 a task on the other
  core could read `g_pulseCount` while the ISR is mid-increment. The spinlock
  makes the 32-bit read-and-reset in the flow task atomic against the ISR. The
  matching `portENTER_CRITICAL` in `Task_Flow_Node3` reads the count **and
  resets it to zero in the same critical section**, so no pulse can be lost
  between the read and the clear. That pairing is the whole correctness argument
  for the counter.

**Why a counter and not a rate.** Measuring flow by counting pulses in an ISR and
dividing by a one-second window is the standard approach for a cheap turbine flow
meter: it puts the timing burden on the RTOS tick instead of on the interrupt,
and it survives jitter. The consequences follow from that choice — the counter is
free-running `uint32_t` with **no overflow detection**, and the reported value is
a *rate* (L/min from `pulses / 5.5`), not a totalised volume. A downstream
consumer that integrates the rate inherits any rate error.

The ISR is attached inside `Task_Flow_Node3` rather than in `setup()`, so pulses
arriving before the task first runs are not counted. On a 1 Hz task that is a
sub-second window at boot.

## The LCD renderers

**Node 1** builds four `String`s and prints them through a `printLCDLine()` helper
that truncates to 16 characters and pads with spaces — the padding matters,
because an HD44780 retains whatever was there previously and an unpadded row
leaves stale characters at the end.

```cpp
--8<-- "assets/snippets/node1-lcd-task.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·
<code>Task_LCD_Node1</code> · lines 220–310 · commit <code>db6d9b8</code>
</div>

Node 1 is the only node with a **status line**, and its precedence is a strict
`if / else if` chain: `WAITING` before `ERROR` before the environmental
conditions before the low-volume conditions before `FAULT` before `NORMAL`. The
order is the behaviour — a technician reading the display sees the most
fundamental fault first. It is worth memorising, because "why does it say
`ERROR` and not `FAULT`?" has a one-line answer: no frame has ever been
received, so Node 1 has nothing to declare Node 2 faulty about.

Node 1 also substitutes `--` and `----` placeholders for absent values and
replaces the decimal point with a comma (`String::replace(".", ",")`), which is
a deliberate readability choice for a European display. Note that the
*placeholder text is shorter than the real value*, so a value that changes width
can leave residue unless the padding works out.

**Node 4** takes a different approach: no row helper, no padding, and an explicit
DDRAM row address written with `lcdN4.command(0x80 | addr)` for the HD44780's
non-contiguous row starts (`0x00, 0x40, 0x10, 0x50`). That is the correct way to
address rows on this controller, and it is why Node 4's formatter strings carry
their own trailing spaces.

```cpp
--8<-- "assets/snippets/node4-lcd-task.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>Task_LCD_Node4</code> · lines 1187–1259 · commit <code>db6d9b8</code>
</div>

Node 4 prints the **stored** values unconditionally, with no invalid-value
substitution and no status line. An invalid pH therefore appears as `pH:0.0`,
indistinguishable from a real reading of zero. The SMTP variant differs only in
`EC:%.1fmS` instead of `EC:%duS`.

> **Engineering interpretation.** Node 4's display is a *live instrument
> readout*, not a status display — it is the panel a technician reads while
> adjusting a probe, and the transaction block on the debug UART carries the
> validity information alongside it. Node 1's display is the opposite: an
> at-a-glance health summary for a node that is physically away from the water
> it is measuring.

## The fatal trap

Every sketch has an identically named function, and this is one of the few
genuinely consistent patterns across all five files:

```cpp
--8<-- "assets/snippets/node1-setup.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·
<code>setup</code> · lines 314–335 · commit <code>db6d9b8</code>
</div>

**What it is.** `systemFatalTrap(name)` prints `[FATAL ERROR] …: <name>. Halted.`
and then loops forever on `vTaskDelay(pdMS_TO_TICKS(1000))`.

**Why halt instead of continuing.** Its two call sites are mutex allocation
failure and task-creation failure. Both mean the node cannot perform its function
correctly: without its mutexes it would race on shared state; without its UART
task it would be invisible; without its sensor task it would report nothing. A
node that limps on with a half-initialised task set produces *plausible but
wrong* telemetry, which is worse than an obviously dead node in a monitoring
system. Halting loudly is the defensible choice.

**Why `vTaskDelay` and not `while (1);`** — the deliberate detail. A bare
`while (1);` on a dual-core system with nothing pinned is a busy loop that pins
whatever core it lands on and heats the part, and it can starve the idle task so
that the watchdog — had one been enabled — would behave unpredictably. Sleeping
one second per iteration keeps the scheduler and the idle task alive, keeps the
node responsive to the USB stack, and keeps power dissipation low. The loop is
still non-recoverable: no external recovery path exists.

**What it does not do.** It does not blink an LED, light a screen, record
anything to NVS, or send an alert. On Nodes 1, 2 and 3 the *only* evidence is one
line on the debug UART — and Nodes 1–3 have no display. In the field, a halted
node presents as a silent, unresponsive unit. See
[Troubleshooting](../field-service/troubleshooting.md)).

## The SMTP variant

The SMTP variant is a **fork**, not an extension: it shares the GPIO map and the
sensor list with Node 4 and re-implements everything else. That is the single
most important thing to understand about it, and it explains every divergence in
the table on [Node 4 SMTP](../nodes/node4-smtp.md)).

**The network and time bring-up is deliberately blocking and time-boxed:**

```cpp
--8<-- "assets/snippets/node4-smtp-init-network.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·
<code>initNetworkAndTime</code> · lines 107–136 · commit <code>db6d9b8</code>
</div>

Thirty association attempts at 500 ms each gives a 15-second budget before the
node gives up and continues without a network; the NTP wait is capped at 15
retries of 1 s and guarded by the epoch floor `1700000000`, which is a cheap
"has the clock been set" test. `configTime(3600, 0, …)` hard-codes **Tunis,
UTC+1 with no daylight saving** — an explicit site decision, and a portability
constraint if a unit is deployed elsewhere.

**Mail is sent through a small, single-purpose helper:**

```cpp
--8<-- "assets/snippets/node4-smtp-send-mail.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·
<code>sendMailMessage</code> · lines 138–171 · commit <code>db6d9b8</code>
</div>

It refuses to send when Wi-Fi is not associated, opens an SSL session on port
465, sends HTML base64-encoded at high priority as `WattLab Node 4`, and closes
the session whether or not the send succeeded. Both outcomes are printed, so the
serial monitor is a usable delivery log.

**Alerting is rate-limited and persisted, which is the part done well:**

```cpp
--8<-- "assets/snippets/node4-smtp-alert-logic.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·
heartbeat and fault rate limiting · lines 301–350 · commit <code>db6d9b8</code>
</div>

The design is: a heartbeat every 86400 s and a fault alert no more often than
every 43200 s, with **both timestamps persisted** in the NVS namespace
`email_state` and only advanced **after a successful send**. Persisting them
means a power cycle cannot be used to defeat the cooldown — a naive
implementation would reset the counters on reboot and send an alert storm. A
fault e-mail itemises each failed sensor in an HTML `<ul>`, so the recipient
knows which probe to go and look at. This is the most operationally mature
behaviour in the firmware.

**Where the variant is weaker.** Its task stack is 5120 bytes for the combined
e-mail and UART task, against 4096 for the UART task in plain `Node4` — the
extra 1 KiB is there because TLS and HTTP buffers live on that task. It has **no
serial calibration console**, so its pH and conductivity constants can only be
changed by editing and reflashing. Its ADC path uses `analogRead` with a 3.3 V
reference and no attenuation configuration, it uses single reads with no
averaging, and it converts turbidity through an intermediate `turbVolt5V =
turbVolt * (5.0f / 3.3f)` — which reintroduces, in a different form, the
5 V-referenced assumption that `Node4`'s comments explicitly reject. And because
it shares GPIO 12, 13 and 14 with the Wi-Fi radio's ADC2 channels, its analogue
readings are taken while the radio is active.

See [Known Limitations](../validation/known-limitations.md) for the full list.

## Related

* [Source Map](source-map.md)) — every symbol with a line range and a permalink.
* [Configuration](configuration.md)) — the constants referenced above.
* [RTOS Tasks](../rtos/tasks.md)) — periods, cores, priorities and stacks.
* [Message Format](../communication/message-format.md)) — the frames being built
  here.
* [Node 4 SMTP](../nodes/node4-smtp.md)) — the variant divergence table.
* [Legacy Firmware](../historical/legacy-firmware.md)) — what "preserved from
  legacy" means in practice.
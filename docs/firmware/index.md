---
title: Firmware
description: Overview of the CIRQUA ESP32 firmware — repository, pinned commit, FreeRTOS execution model and how the documentation consumes the source.
---

# Firmware

The CIRQUA monitoring cluster runs on five Arduino-ESP32 sketches — four node
firmwares plus one Node 4 variant — hosted in a single Git repository. This
section documents that firmware as *source code*: what each file does, how it
is built, how it is flashed, how it is configured in the field, and how it maps
onto the pages of this documentation set.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Repository</span>
    <span class="cirqua-identity__value"><a href="https://github.com/lestealthy/Cirqua">github.com/lestealthy/Cirqua</a></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Branch</span>
    <span class="cirqua-identity__value"><code>main</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Documented revision</span>
    <span class="cirqua-identity__value"><code>db6d9b8</code><br>full SHA <code>db6d9b896341a9c7d8fd01913e854b663c110d55</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Consumed as</span>
    <span class="cirqua-identity__value">Git submodule at <code>_external/Cirqua-firmware</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Framework</span>
    <span class="cirqua-identity__value">Arduino-ESP32 <code>.ino</code> sketches, FreeRTOS tasks</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Units</span>
    <span class="cirqua-identity__value">4 nodes + 1 variant = <strong>5 sketches</strong>, each flashed to its own ESP32</span>
  </div>
</div>

## What this firmware is

Every node is an independent ESP32 board running a FreeRTOS task set. There is
no shared binary, no bootloader image, no configuration file and no remote
update mechanism in the repository. Each `.ino` file is:

* a **complete, standalone sketch** — it declares its own pins, its own sensor
  objects, its own task set and its own `setup()`;
* flashed to **one physical ESP32**;
* configured almost entirely by **compile-time constants** in that sketch;
* the only exception being Node 4, which has a small non-volatile (NVS) store
  for pH and conductivity calibration.

The telemetry protocol between nodes is plain ASCII over UART at 9600 baud. It
is described in [Message Format](../communication/message-format.md)) and
[Serial Links](../communication/serial-links.md)); this section describes the
*code*, not the wire format.

## Execution model — `setup()`/`loop()` are not the runtime

This is the single most important structural fact about the firmware. Each
sketch defines `setup()` and `loop()`, but the Arduino execution model is
discarded almost immediately:

* `setup()` opens `Serial` at 115200 baud, creates mutexes, and calls
  `xTaskCreatePinnedToCore()` for every task.
* `loop()` contains exactly one statement — `vTaskDelete(NULL)` — which deletes
  the Arduino loop task and reclaims its stack.

All real work therefore happens in FreeRTOS tasks pinned to the ESP32's two
cores. Any description of node behaviour that is written in terms of `loop()`
is wrong. Task tables are on [RTOS Tasks](../rtos/tasks.md)); core pinning and
scheduling are on [Scheduling](../rtos/scheduling.md)).

## Repository layout: CURRENT versus HISTORICAL

The repository contains two source trees, and **only one of them is the current
architecture**.

| Directory | Status | Meaning |
|---|---|---|
| `FreeRTOS_Implementation/` | <span class="cirqua-badge cirqua-badge--current">current</span> | The five authoritative sketches described by this documentation |
| `_OLD/` | <span class="cirqua-badge cirqua-badge--historical">historical</span> | Legacy single-file sketches kept for reference; **never the current architecture** |

`_OLD/` contains `cirqua/cirqua.ino`, per-node predecessors
(`Node1/Node1.ino`, `node2_fixed/node2_fixed.ino`, `node3_fixed/node3_fixed.ino`,
`Node4/Node4.ino`) and a concatenated `all_code_cluster.txt` dump. Those files
use blocking `loop()`-driven designs and a different or absent task structure.
They are **not** to be mixed into descriptions of current behaviour, and no
page in this documentation set describes them as though they were running on a
node. Where a legacy behaviour was deliberately kept in the current code, the
page says so explicitly — see
[Code Reference](code-reference.md#the-calibration-model) and
[Revision History](revision-history.md)).

Historical material is confined to [Legacy Firmware](../historical/legacy-firmware.md)).

## The five current sketches

| Sketch | Lines | Node role | Display | Link role |
|---|---|---|---|---|
| [`FreeRTOS_Implementation/Node1/Node1.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino) | 339 | Cluster head — Collection Tank A (`TAV`) level | 16×4 I²C LCD with a `STATUS:` line | **Originates** the frame; receives Node 2's echo |
| [`FreeRTOS_Implementation/Node2/Node2.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino) | 399 | Water temperature, dissolved oxygen, Feeding Tank B (`TBV`), ambient telemetry | none | Consumes Node 1, adds its own fields, echoes them back, forwards to Node 3 |
| [`FreeRTOS_Implementation/Node3/Node3.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino) | 174 | Inline flow metering (`FLM`) | none | Pass-through plus `FLM`; emits a fallback frame on upstream silence |
| [`FreeRTOS_Implementation/Node4/Node4.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino) | 1346 | Cluster tail — effluent volume, pH, turbidity, conductivity | 16×4 I²C LCD | Cleans and extends the upstream packet; **has the serial calibration console** |
| [`FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino) | 452 | Node 4 plus Wi-Fi, NTP and SMTP e-mail alerting | 16×4 I²C LCD | Same tail role; **different** downstream field set; no calibration console |

!!! warning "Node 4 and Node 4 SMTP are not interchangeable"
    The two variants share a GPIO map but differ in calibration defaults,
    downstream field names, the presence of a serial calibration console, the
    treatment of ambient `AT:`/`AH:` fields, and the conductivity unit reported.
    See [Node 4 SMTP](../nodes/node4-smtp.md)).

## How this documentation consumes the firmware

The documentation repository does **not** copy the firmware. It references it as
a **Git submodule**:

```text
Cirqua-documentation/
├── _external/Cirqua-firmware      <- Git submodule, pinned to db6d9b8
├── docs/
├── scripts/
└── sources/firmware-source.yml   <- machine-readable pin record
```

* The submodule is declared in `.gitmodules` with
  `url = https://github.com/lestealthy/Cirqua.git` at path
  `_external/Cirqua-firmware`.
* The exact commit consumed is recorded in `sources/firmware-source.yml` and
  repeated in `mkdocs.yml` under `extra.cirqua.firmware_commit`, so every page
  can render the same pin consistently.
* Every code excerpt in this documentation set is **mechanically extracted**
  from that submodule by `scripts/extract_code_snippets.py` into
  `docs/assets/snippets/`. Nothing is hand-typed. Each extracted file carries its
  originating path, symbol, line range and commit in
  [`docs/assets/snippets/snippet-index.yml`](../assets/snippets/snippet-index.yml).

That is why every code block in this section is followed by a provenance block
naming the file, the symbol, the line range and the commit. See
[Repository](repository.md)) for how to move the pin forward.

## Pages in this section

| Page | What it answers |
|---|---|
| [Repository](repository.md)) | Where the code lives, how the submodule is pinned, what every file contains, how to check the local tree matches the documented commit |
| [Source Map](source-map.md)) | **Reverse index**: documentation topic → node → file → function/symbol → link at commit `db6d9b8` |
| [Build](build.md)) | How to compile each sketch, which libraries are needed, and what is *not* in the repository |
| [Flashing](flashing.md)) | Per-node flashing procedure, UART and boot-mode cautions, expected first-boot serial output |
| [Calibration Console](configuration.md)) | The Node 4 serial configuration surface and every compile-time constant |
| [Code Reference](code-reference.md)) | A guided tour by engineering concern, with the rationale for each shape |
| [Revision History](revision-history.md)) | The real Git history — which is, today, a single commit — and what that means for provenance |

## How to read claims on these pages

Every statement in this section is one of four kinds, and the pages say which:

* **Firmware implementation** — read directly from the pinned commit.
* **Manufacturer specification** — only used where a datasheet is cited; see
  [Datasheets](../references/datasheets.md).
* **Engineering interpretation** — explicitly labelled, e.g. why a piece of
  code is probably shaped the way it is.
* **Recommendation** — explicitly labelled, e.g. the proposed test strategy in
  [Test Strategy](../validation/test-strategy.md)).

Nothing in this section asserts that a node has been deployed, measured or
certified. See
[Firmware Validation](../validation/firmware-validation.md) for what has and
has not been checked, and
[Known Limitations](../validation/known-limitations.md) for the honest list
of weaknesses.
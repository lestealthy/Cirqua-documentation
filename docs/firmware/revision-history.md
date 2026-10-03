---
title: Firmware Revision History
description: The real Git history of the CIRQUA firmware repository — a single commit — and what that means for provenance and for the legacy behaviour kept on purpose.
---

# Firmware Revision History

This page is built from the actual `git log` of
[lestealthy/Cirqua](https://github.com/lestealthy/Cirqua) at the documented
revision. It is short, because the repository's history is short.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Commits on <code>main</code></span>
    <span class="cirqua-identity__value"><strong>1</strong></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Tags / releases</span>
    <span class="cirqua-identity__value">0 — <span class="cirqua-badge cirqua-badge--unknown">none</span></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Branches observed</span>
    <span class="cirqua-identity__value"><code>main</code> only</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Earliest commit</span>
    <span class="cirqua-identity__value">2026-10-03</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Change log file</span>
    <span class="cirqua-identity__value">None in the repository</span>
  </div>
</div>

## The complete history

```text
commit db6d9b896341a9c7d8fd01913e854b663c110d55
Author: Amine <amine@wattlab.dev>
Date:   2026-10-03 14:30:02 +0100

    Initial commit: Cirqua firmware with FreeRTOS implementation

 FreeRTOS_Implementation/Node1/Node1.ino           |  339 ++++
 FreeRTOS_Implementation/Node2/Node2.ino           |  399 ++++
 FreeRTOS_Implementation/Node3/Node3.ino           |  174 ++
 FreeRTOS_Implementation/Node4/Node4.ino           | 1346 ++++++++++
 FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino |  452 ++++
 _OLD/Node1/Node1.ino                              |  856 ++++++++
 _OLD/Node4/Node4.ino                              |  288 ++
 _OLD/all_code_cluster.txt                         | 1987 +++++++++++++++++
 _OLD/cirqua/cirqua.ino                            |  269 ++++
 _OLD/node2_fixed/node2_fixed.ino                 |  753 ++++++++
 _OLD/node3_fixed/node3_fixed.ino                  |   90 +
 11 files changed, 6953 insertions(+)
```

**There is exactly one commit.** The entire current architecture, and the entire
legacy tree, arrived in a single commit on 2026-10-03. There is no earlier
commit, no branch, no tag, no release and no changelog file in the repository.

| Commit | Date | Summary | Files | Architecture impact |
|---|---|---|---|---|
| [`db6d9b8`](https://github.com/lestealthy/Cirqua/commit/db6d9b896341a9c7d8fd01913e854b663c110d55) | 2026-10-03 14:30:02 +0100 | *Initial commit: Cirqua firmware with FreeRTOS implementation* — Amine `&lt;amine@wattlab.dev&gt;` | 11 added, 6953 insertions | **Establishes the entire architecture.** Introduces `FreeRTOS_Implementation/` (Nodes 1–4 plus the `Node4_SMTP` variant) as the current design, and simultaneously adds `_OLD/` as the historical predecessor set. No change to compare against — this commit *is* the baseline. |
| *(documentation repository)* | 2026-10-03 onwards | This documentation set: `lestealthy/Cirqua-documentation`, consuming `db6d9b8` as a submodule at `_external/Cirqua-firmware` | Markdown, extracted snippets, `sources/firmware-source.yml` | **No firmware impact.** Documentation-only. The pin is recorded in `sources/firmware-source.yml` and `mkdocs.yml`; moving it re-baselines every line number in [Source Map](source-map.md)) and [Code Reference](code-reference.md)). |

## What one commit does and does not tell us

Stated plainly, because this is the kind of page that usually gets padded with
invented history.

**What it establishes.**

* The architecture as documented — five FreeRTOS sketches, dual-core task
  pinning, the ASCII frame protocol, the NVS calibration store, the SMTP
  variant — was complete at the moment of the commit. There is no
  "work-in-progress" state in the recorded history.
* The legacy code and the current code were committed **together**. The
  FreeRTOS implementation was not created *from* a tracked `main` history; it was
  committed beside the sketches it replaced.
* Every line number, constant and format claim in this documentation set is
  anchored to a single, immutable SHA. Nothing can silently change underneath
  the pages.

**What it does not establish.**

* **When each behaviour was introduced.** There is no way to tell from Git
  whether, for example, the Node 1 volume doubling predates or postdates the
  FreeRTOS port.
* **Which legacy behaviour was ported deliberately and which was simply left
  behind.** The repository records no such decision. Where the current code
  *comments* that something was preserved — the pH model, the EC K-factor, the
  `FLM` key name, the packet cleaner — that comment is the only evidence.
  Everywhere else this documentation labels its reasoning as
  **Engineering interpretation**.
* **Whether the deployed nodes run this commit.** No board reports a version or a
  commit identifier, on the wire or on the display. Field-to-repository
  traceability is currently manual bookkeeping.
* **Why any choice was made.** There is no commit message beyond the single
  initial one, no design notes and no pull-request discussion preserved in the
  repository.

!!! warning "A richer history is not yet available"
    There is no second commit to document. Any future page describing an
    "evolution" of this firmware would be fabrication. When commits are added,
    this page should be extended with the same columns, and the
    `FreeRTOS_Implementation/` versus `_OLD/` split should be revisited — if the
    legacy tree is deleted or promoted, the status labels here change.

## The `FreeRTOS_Implementation/` versus `_OLD/` split, as observed

The single commit contains both trees. Reading them together is the only
provenance evidence available.

| Aspect | `FreeRTOS_Implementation/` | `_OLD/` |
|---|---|---|
| Status | <span class="cirqua-badge cirqua-badge--current">current</span> | <span class="cirqua-badge cirqua-badge--historical">historical</span> |
| Program model | FreeRTOS tasks pinned with `xTaskCreatePinnedToCore`; `loop()` deletes itself | Blocking, `loop()`-driven sketches |
| Nodes | 4 nodes + 1 variant | 4 sketches + a cluster sketch + a concatenated dump |
| Sizes | 339 / 399 / 174 / 1346 / 452 lines | 7389 / 16852 / 17161 / 2710 / 7559 bytes, plus a 46269-byte dump |
| Concurrency | Mutex-protected shared structs, one ISR with a critical section | Not visible from the tree |
| Calibration | NVS-backed, console-adjustable on Node 4 | Constants in source |
| Diagnostics | Structured `[NODE 4 PACKET TRANSACTION]` block; LCD status strings | Not visible from the tree |
| Referenced by this documentation | Yes, exclusively | Only to explain provenance, always labelled |

The most likely reading — **Engineering interpretation** — is that the legacy
sketches were the working prototype on a single board, and the FreeRTOS
implementation was a multi-node rewrite that was committed as a new tree while
the originals were retained verbatim under `_OLD/` for reference. The directory
name `_OLD` is itself the author's statement that these files are superseded.
Note that `_OLD/all_code_cluster.txt` is a concatenated dump, which suggests it
was produced to make the legacy code easy to read or share as a single document
rather than to be compiled.

## Behaviour deliberately preserved from legacy

The current code carries exactly one architectural decision that a comment
records as inherited. It is the packet cleaner.

```cpp
--8<-- "assets/snippets/node4-packet-cleaner.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>cleanUpstreamPacket</code> · lines 936–990 · commit <code>db6d9b8</code>
</div>

**Why this one matters for provenance.** Every other piece of current code can be
read as new work in the FreeRTOS implementation. The packet cleaner cannot: its
effect is defined by an **external contract**, not by the node's own behaviour.
It removes the upstream `AT:` and `AH:` tokens so that the downstream controller
receives exactly one ambient temperature/humidity pair, taken from Node 4's own
DHT11. Two related comments in the current tree make the same point from the
other direction: the pH block's *"Existing calibration model preserved"* and the
EC block's *"Existing K-factor behavior preserved"*.

So the current firmware explicitly preserves three things from the legacy
system:

| Preserved behaviour | Where it is recorded | External contract it protects |
|---|---|---|
| One ambient `AT:`/`AH:` pair downstream | `cleanUpstreamPacket`, `Node4.ino` 936–990 | The controller's parser expects exactly one of each field |
| pH as `slope × V + offset` with the existing temperature compensation | `Task_Sensors_Node4`, `Node4.ino` 458–509, comment *"Existing calibration model preserved"* | Calibration already performed against this probe and recorded as slope/offset |
| Conductivity as `V × K` normalised to 25 °C | `Task_Sensors_Node4`, `Node4.ino` 584–635, comment *"Existing K-factor behavior preserved"* | The same K-factor, expressed in a different unit, was in use in the field |

and one naming decision that was standardised for interoperability rather than
inherited:

| Standardised name | Where | Why it is recorded |
|---|---|---|
| `FLM` for flow | `Task_UART_Node3`, `Node3.ino` 127–128 — *"Standardized key name FLM for downstream controller compatibility"* | The controller expects `FLM`; renaming it inside the node was required, and the field name is therefore fixed by an external consumer |

**What this implies for maintainers.** These five points are the ones where a
"clean-up" would break something outside the node. Before renaming a field,
changing a calibration model or re-adding an ambient pair, check what the
downstream controller expects. That contract is external to this repository, so
it cannot be verified here — > **Not verified from the current source.** The
controller's parsing code is not part of this repository, and no controller
firmware is included in it.

The one place where this standardisation was *not* propagated is a divergence,
not an oversight: Node 2's reverse-telemetry parser still looks for `|FR:` while
Node 3 emits `|FLM:`. See [Code Reference](code-reference.md#the-frame-parser).

## Divergences introduced inside the current tree

Both were introduced within the single commit — that is, the divergence exists in
the baseline and has no prior state to compare against.

| Divergence | Where | Effect |
|---|---|---|
| `Node4` vs `Node4_SMTP` downstream fields and calibration defaults | `Node4.ino` 1139–1162 versus `Node4_SMTP.ino` 376–383; defaults at `Node4.ino` 137–144 versus `Node4_SMTP.ino` 101–103 | Two units with the same GPIO map report different field names, different units and different calibration defaults |
| `Node4` cleans the upstream packet; `Node4_SMTP` does not | `Node4.ino` 1082–1085 versus the absent call in `Node4_SMTP.ino` | The controller receives one ambient pair from a `Node4` and Node 2's pair from an SMTP unit |
| `Node4_SMTP` has no calibration console | `Node4.ino` 717–931 only | Calibration on the SMTP variant requires a reflash |

## Related

* [Repository](repository.md)) — the pin, the inventories, and how to move it.
* [Source Map](source-map.md)) — line ranges that change when the pin moves.
* [Code Reference](code-reference.md)) — the preserved legacy behaviour in
  context.
* [Legacy Firmware](../historical/legacy-firmware.md)) — the `_OLD/` tree.
* [Firmware Validation](../validation/firmware-validation.md) — how the pin was
  verified.
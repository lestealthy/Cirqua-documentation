---
title: Historical index
description: Index of archived CIRQUA sketches retained for provenance, with an explicit statement that they are not the current firmware architecture.
---

# Historical

This section covers firmware that is retained in the repository for provenance
but is **not** part of the current CIRQUA architecture.

| Page | Contents |
|---|---|
| [Legacy firmware](legacy-firmware.md) | The `_OLD/` sketches, the legacy Arduino Mega controller, and two legacy Node 3 defects that the current code fixed |

!!! danger "Historical / Legacy — not the current firmware architecture"
    Do not use `_OLD/` GPIO assignments, serial protocols, task structures,
    sensor conversions or calibration constants when servicing hardware or
    interpreting live telemetry.

!!! info "Why legacy code is kept"
    Removing it would destroy the record of how constants such as the turbidity
    polynomial, the pH slope/offset model and the `FLM` key name were arrived at,
    and of which defects were deliberately fixed.

## Current versus historical

| | Current | Historical |
|---|---|---|
| Repository path | `FreeRTOS_Implementation/` | `_OLD/` |
| Documented as | The system architecture | Design history only |
| Documentation rule | Audited line by line | Never merged into current pages |
| FreeRTOS | Dual-core pinned tasks | Single-threaded `setup()` / `loop()` |

To work on the current firmware, start at
[Source map](../firmware/source-map.md).
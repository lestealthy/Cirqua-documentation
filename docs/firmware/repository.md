---
title: Firmware Repository
description: Layout, submodule pinning and file inventory of the CIRQUA firmware repository, and how to verify a local tree against the documented commit.
---

# Firmware Repository

Everything in this section is *firmware implementation*, read from one pinned
commit of one repository. This page explains where the code lives, how this
documentation binds to it, how to move the pin to a newer commit, and how to
prove that a working tree in front of you is the one these pages describe.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Repository</span>
    <span class="cirqua-identity__value"><a href="https://github.com/lestealthy/Cirqua">github.com/lestealthy/Cirqua</a></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Default branch</span>
    <span class="cirqua-identity__value"><code>main</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Pinned commit</span>
    <span class="cirqua-identity__value"><code>db6d9b896341a9c7d8fd01913e854b663c110d55</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Commit count</span>
    <span class="cirqua-identity__value">1 (<span class="cirqua-badge cirqua-badge--unknown">limited history</span>)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Documented by</span>
    <span class="cirqua-identity__value">Git submodule at <code>_external/Cirqua-firmware</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Build system</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--unknown">none</span> — no <code>platformio.ini</code>, no <code>CMakeLists.txt</code></span>
  </div>
</div>

## Repository layout

```text
Cirqua/                                   branch: main
├── FreeRTOS_Implementation/              CURRENT ARCHITECTURE
│   ├── Node1/Node1.ino                   339 lines
│   ├── Node2/Node2.ino                   399 lines
│   ├── Node3/Node3.ino                   174 lines
│   ├── Node4/Node4.ino                  1346 lines
│   └── Node4_SMTP/Node4_SMTP.ino         452 lines
└── _OLD/                                 HISTORICAL / LEGACY
    ├── cirqua/cirqua.ino                 7389 bytes
    ├── Node1/Node1.ino                  16852 bytes
    ├── node2_fixed/node2_fixed.ino      17161 bytes
    ├── node3_fixed/node3_fixed.ino       2710 bytes
    ├── Node4/Node4.ino                   7559 bytes
    └── all_code_cluster.txt             46269 bytes
```

That is the entire repository: **11 files, no README, no licence file, no build
files, no schematics, no CI configuration, no tests.**

!!! warning "The two directories are not two versions of the same program"
    `FreeRTOS_Implementation/` is a multi-task, multi-node, RTOS design.
    `_OLD/` is a set of earlier blocking sketches plus a concatenated dump.
    The `_OLD/` tree is **never** the current architecture. Where this
    documentation refers to `_OLD/`, it does so only to explain provenance — see
    [Legacy Firmware](../historical/legacy-firmware.md)) and
    [Revision History](revision-history.md)).

## Current firmware units

| Unit | File | Lines | Role |
|---|---|---|---|
| Node 1 | `FreeRTOS_Implementation/Node1/Node1.ino` | 339 | Collection Tank A (`TAV`) ultrasonic level; cluster head; LCD |
| Node 2 | `FreeRTOS_Implementation/Node2/Node2.ino` | 399 | Water temperature, dissolved oxygen, Feeding Tank B (`TBV`), ambient telemetry; no display |
| Node 3 | `FreeRTOS_Implementation/Node3/Node3.ino` | 174 | Flow pulse counting (`FLM`); pass-through forwarding; no display |
| Node 4 | `FreeRTOS_Implementation/Node4/Node4.ino` | 1346 | Effluent volume, pH, turbidity, conductivity, submerged and ambient temperature; cluster tail; LCD; NVS calibration console |
| Node 4 SMTP | `FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino` | 452 | Node 4 sensor set plus Wi-Fi, NTP and SMTP alerting; variant |

Line counts are the values at commit `db6d9b8` and are reproduced in the
manifest at `sources/firmware-source.yml`.

## Historical units

| Unit | Path | Size |
|---|---|---|
| Legacy cluster sketch | `_OLD/cirqua/cirqua.ino` | 7389 bytes |
| Legacy Node 1 | `_OLD/Node1/Node1.ino` | 16852 bytes |
| Legacy Node 2 | `_OLD/node2_fixed/node2_fixed.ino` | 17161 bytes |
| Legacy Node 3 | `_OLD/node3_fixed/node3_fixed.ino` | 2710 bytes |
| Legacy Node 4 | `_OLD/Node4/Node4.ino` | 7559 bytes |
| Concatenated dump | `_OLD/all_code_cluster.txt` | 46269 bytes |

Only one fragment of this tree is extracted into the documentation — the
`legacy-node3-ping` snippet, used on the legacy page to show a predecessor
design. It is labelled
<span class="cirqua-badge cirqua-badge--historical">historical</span> everywhere
it appears.

## The submodule relationship

The documentation repository references the firmware repository rather than
forking or copying it:

| Aspect | Value |
|---|---|
| Submodule path | `_external/Cirqua-firmware` |
| Submodule URL | `https://github.com/lestealthy/Cirqua.git` |
| Declared in | `.gitmodules` in the documentation repository |
| Pinned by | the submodule gitlink in the documentation repository tree |
| Recorded for tooling in | `sources/firmware-source.yml` and `mkdocs.yml` (`extra.cirqua`) |

The consequences of using a submodule rather than a copy are worth stating
plainly:

* The documentation cannot drift from a fork, because there is no fork.
* Snippet extraction reads the checked-out tree. If the submodule is not
  initialised, extraction fails loudly rather than producing empty code blocks.
* Nothing in the firmware repository is modified by the documentation tooling.
  The extractor is read-only with respect to `_external/`.

## How the pin is recorded

`sources/firmware-source.yml` is the machine-readable record of *which* firmware
the published pages describe. It carries the repository, branch, full and short
commit, submodule path, the current and historical directory names, and a unit
per sketch with its file path, role and status:

```yaml
repository: https://github.com/lestealthy/Cirqua
repository_slug: lestealthy/Cirqua
branch: main
commit: db6d9b896341a9c7d8fd01913e854b663c110d55
commit_short: db6d9b8
path: _external/Cirqua-firmware

current_source_dir: FreeRTOS_Implementation
historical_source_dir: _OLD
```

The same commit appears twice more: in `mkdocs.yml` as
`extra.cirqua.firmware_commit` (so page templates can render it) and in the
header of every generated snippet file, so a reader can always trace an embedded
block back to a commit without leaving the page.

## Developer setup

!!! info "Developer-only"
    The following commands assume a checkout of the documentation repository and
    a recent Git. They are for maintainers of the documentation, not for field
    technicians. Paths are relative to the repository root; adjust `%CD%` or
    `$PWD` to suit your shell rather than hard-coding a machine-specific path.

Initialise the pinned firmware tree:

```bash
git submodule update --init --recursive
```

Confirm what you actually have:

```bash
git submodule status
# ->  _external/Cirqua-firmware db6d9b896341a9c7d8fd01913e854b663c110d55 (heads/main)
```

Confirm the commit recorded for the documentation build:

```bash
git -C _external/Cirqua-firmware rev-parse HEAD
```

## Verifying that a local tree matches the documented commit

Use this four-step check whenever you are asked "is this the code your
documentation describes?".

| Step | Command | Expected result at `db6d9b8` |
|---|---|---|
| 1. HEAD commit | `git -C _external/Cirqua-firmware rev-parse HEAD` | `db6d9b896341a9c7d8fd01913e854b663c110d55` |
| 2. Clean tree | `git -C _external/Cirqua-firmware status --porcelain` | no output |
| 3. Submodule pin | `git submodule status` | line beginning ` _external/Cirqua-firmware db6d9b8…` with **no** `-` or `+` prefix |
| 4. Snippets not stale | `python scripts/extract_code_snippets.py --check` | exit code 0, no snippet reported as changed |

The `+` prefix in step 3 means the checked-out submodule commit differs from the
one recorded in the documentation repository index; `-` means the submodule is
not initialised. Both mean **do not trust the rendered code** until resolved.

Step 4 is the strongest single check: it re-derives all 41 snippets from the
firmware tree and compares them byte-for-byte against
`docs/assets/snippets/`. If the firmware has changed in a way that affects an
extracted region, the check fails and names the file.

## Updating to a newer firmware commit

!!! warning "A pin move is a documentation change, not a bookkeeping change"
    Moving the commit re-baselines every line number, every snippet and every
    claim on these pages. Budget for re-reading the diff, not just for running
    a command.

The supported sequence:

1. Fetch the newer firmware inside the submodule:

    ```bash
    git -C _external/Cirqua-firmware fetch origin main
    ```

2. Check out the target commit and commit the gitlink:

    ```bash
    git -C _external/Cirqua-firmware checkout <new-commit-sha>
    git add _external/Cirqua-firmware
    git commit -m "Pin firmware to <new-commit-short>"
    ```

3. Update `sources/firmware-source.yml`: `commit`, `commit_short`, and any
    changed `file` path, `role` or `status` entries. If a file was added,
    removed or renamed, update `current_units` / `historical_units` to match.
4. Update `mkdocs.yml` under `extra.cirqua`: `firmware_commit` and
    `firmware_commit_short`.
5. Regenerate the extracted snippets and the snippet index:

    ```bash
    python scripts/extract_code_snippets.py
    ```

6. Read the diff of the firmware and update the affected pages. At minimum
   re-check: the [Source Map](source-map.md)) line ranges, the GPIO map in
   [GPIO Map](../hardware/gpio-map.md)), the task table in
   [RTOS Tasks](../rtos/tasks.md)), the frame formats in
   [Message Format](../communication/message-format.md)), the constants table
   in [Calibration Console](configuration.md)), and the limitations register in
   [Known Limitations](../validation/known-limitations.md).
7. Record the move in [Revision History](revision-history.md)) — the Commit,
   Date, Summary, Files and Architecture impact columns.
8. Build strictly before publishing:

    ```bash
    mkdocs build --strict
    ```

Never hand-edit `sources/firmware-source.yml`'s `commit` field without actually
moving the submodule. A pin that describes a commit nobody has read produces
documentation that is confidently wrong.

## What is not in the repository

Stated plainly, because absence is easy to gloss over:

| Absent | Consequence |
|---|---|
| `README` | No upstream prose exists; this documentation set is the only description |
| Build system (`platformio.ini`, `CMakeLists.txt`, Makefile) | No reproducible, version-pinned build is defined anywhere |
| Pinned Arduino-ESP32 core version | > **Not verified from the current source.** |
| Library version pins or `library.properties` references | Library versions used for any build are the IDE's choice |
| Schematics, PCB files, wiring diagrams | Circuit documentation does not exist |
| Photographs | There is nothing to show |
| Tests, test harness, CI | Validation is manual; see [Validation](../validation/index.md)) |
| Licence file | > **Not verified from the current source.** |
| Hardware BOM, part numbers for DO / flow / pH / EC sensors | Those sensors are unnamed in source; see [Datasheets](../references/datasheets.md) |
| Changelog, tags, releases | History is one commit; see [Revision History](revision-history.md)) |

## Related

* [Source Map](source-map.md)) — every function mapped to a documentation topic.
* [Build](build.md)) — compiling each sketch without a build system.
* [Code Reference](code-reference.md)) — the code by engineering concern.
* [Revision History](revision-history.md)) — the real commit history.
* [Firmware Validation](../validation/firmware-validation.md) — what was
  verified at this pin.
---
title: Validation
description: How the CIRQUA firmware and documentation are validated today — what is actually checked, what is manual, and what the project still needs.
---

# Validation

This section is about assurance. It states, without hedging, what has been
checked, what has not, and how validation of this project could be made
stronger.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Firmware unit tests</span>
    <span class="cirqua-identity__value">0 — <span class="cirqua-badge cirqua-badge--unknown">none</span> no test files, no harness, no framework</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Firmware CI</span>
    <span class="cirqua-identity__value">0 workflows — <span class="cirqua-badge cirqua-badge--unknown">none</span></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Documentation checks</span>
    <span class="cirqua-identity__value">Snippet extraction, staleness check, pinned manifest</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Hardware validation</span>
    <span class="cirqua-identity__value"><strong>Manual and observational</strong> — LCD, debug UART, `STATUS`, frames</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Conformance claims</span>
    <span class="cirqua-identity__value">None — no standard is claimed or tested</span>
  </div>
</div>

## The honest position

!!! warning "The firmware repository has no automated tests, no test harness and no CI"
    A complete search of the pinned commit finds **no test files, no test
    framework, no assertion macros, no mocks, no fixture data, no CI workflow and
    no build automation of any kind**. There is nothing to run, and nothing that
    runs automatically.

    Everything the firmware is checked against today is checked by a **human
    looking at it**: an LCD, a serial monitor, or a captured UART frame.

That is not presented here as a criticism so much as a description of the
current state, because a reader deciding whether to trust a number on an LCD
needs to know that no automated check stands behind it.

## What *is* validated

Some things in this project genuinely are verified, mechanically:

| What | How it is checked | Tooling |
|---|---|---|
| The documentation describes the intended firmware revision | The submodule is pinned and the commit recorded | `sources/firmware-source.yml`, `.gitmodules`, `mkdocs.yml` |
| Every embedded code block is real, unaltered firmware | Snippets are **extracted**, never hand-written; a staleness check fails the build if they diverge | `scripts/extract_code_snippets.py --check` |
| Every snippet carries its file, symbol, line range and commit | Machine-readable index generated alongside the snippets | `docs/assets/snippets/snippet-index.yml` |
| Credentials cannot leak into the documentation | The extractor redacts `WIFI_PASSWORD` and `AUTHOR_PASSWORD` | `scripts/extract_code_snippets.py` |
| The documentation builds and internal links resolve | Strict build | `mkdocs build --strict` |
| GPIO maps, task tables and frame formats are internally consistent | Audited directly against the pinned source, and cross-checked between pages | Manual audit of this documentation build |

**Engineering interpretation.** The extraction pipeline is the strongest
assurance available here, and it is worth being precise about what it does and
does not give you: it guarantees the *code shown* is real code from the pinned
commit, and that documentation cannot drift away from the firmware text. It does
**not** guarantee the code is correct, that the surrounding prose is right, or
that the deployed nodes run this commit.

## What is not validated

| Not validated | Consequence |
|---|---|
| Sensor accuracy, drift or repeatability | No figure on any sensor page is field-verified |
| The correctness of any conversion formula | Only checkable by bench comparison; see [Test Strategy](test-strategy.md)) |
| Timing behaviour under load | No measurement, no trace, no assertion |
| Concurrency correctness beyond code review | No stress test, no ThreadSanitizer equivalent |
| Protocol robustness | No fuzzing, no malformed-frame injection |
| Field deployment of any node | > **Not verified from the current source.** |
| That deployed nodes run commit `db6d9b8` | No version or commit identifier is reported anywhere |
| Any standards conformance | None is claimed; see [Standards](../references/standards.md)) |

## Pages in this section

| Page | What it contains |
|---|---|
| [Test Strategy](test-strategy.md)) | A proposed layered scheme — clearly labelled **Recommendation** — with a test matrix |
| [Hardware Validation](hardware-validation.md)) | Per-node bring-up procedures written only in terms of observable firmware behaviour, with expected-observation tables |
| [Firmware Validation](firmware-validation.md) | What was actually verified for this documentation build, and the evidence for each claim |
| [Known Limitations](known-limitations.md) | The limitations register: what the design cannot do, with severity and mitigations |

## How to read the evidence labels

| Label | Meaning |
|---|---|
| <span class="cirqua-badge cirqua-badge--verified">verified</span> | Checked against the pinned commit for this documentation build; the evidence is named |
| <span class="cirqua-badge cirqua-badge--current">current</span> | Describes the firmware as it exists at `db6d9b8` |
| <span class="cirqua-badge cirqua-badge--variant">variant</span> | True of one variant only (`Node4` or `Node4_SMTP`) |
| <span class="cirqua-badge cirqua-badge--historical">historical</span> | Describes `_OLD/`, which is never the current architecture |
| <span class="cirqua-badge cirqua-badge--unknown">unknown</span> | Not established; written as "Not verified from the current source." |
| <span class="cirqua-badge cirqua-badge--planned">planned</span> | Proposed work that does not exist yet |

## Related

* [Firmware Source Map](../firmware/source-map.md)) — the basis for every
  verifiable claim.
* [Repository](../firmware/repository.md)) — how the pin is checked.
* [Official Project Sources](../references/official-project-sources.md)) — the
  primary sources for project-level claims, as distinct from code claims.
* [Test Strategy](test-strategy.md)) — the recommended way to close the gaps
  listed above.
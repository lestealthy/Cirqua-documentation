---
title: Standards
description: Standards relevant to the CIRQUA project's subject matter and to its documentation tooling — with an explicit statement that none is claimed or tested.
---

# Standards

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Conformance claimed by the firmware</span>
    <span class="cirqua-identity__value"><strong>None</strong> — <span class="cirqua-badge cirqua-badge--unknown">not claimed</span></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Conformance tested</span>
    <span class="cirqua-identity__value"><strong>None</strong> — no test exists</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Standards-conformance logic in the source</span>
    <span class="cirqua-identity__value">None. No standard is referenced, implemented or encoded anywhere</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Certification claimed</span>
    <span class="cirqua-identity__value">None — no certification is claimed anywhere in this project</span>
 </div>
</div>

!!! danger "No standard compliance is claimed, implemented or tested"
    The firmware contains **no standards-conformance logic of any kind**. There is
    no conformance test, no certification claim, no declaration of conformity, and
    no reference to any standard anywhere in the source at commit `db6d9b8`.

    The standards below are listed because they are **relevant to the subject
    matter** of the project or **referenced by the documentation tooling**. Their
    presence in this section is not a claim that the firmware complies with them,
    and it must not be read as one.

## How to read this page

| Category | Meaning | Conformance claimed? |
|---|---|---|
| **Relevant to the subject matter** | The standard governs the kind of system or output the project works with. Its existence contextualises the project; it says nothing about the firmware | **No** |
| **Referenced by the tooling** | The standard is used by the documentation build, not by the firmware | **No** |
| **Commonly applicable** | A standard a deployment in this domain would often need to consider. Listed for orientation only | **No** |
| **Explicitly not claimed** | Named in full and then expressly disclaimed, to prevent a reader inferring a claim from an omission | **No** |

## Relevant to the subject matter

These standards govern water reuse, irrigation control and water policy — the
domain the project's constructed wetlands and treated-water reuse sit in. **The
CIRQUA firmware does not implement, test or reference any of them.**

| Standard | Scope | Relationship to this documentation set |
|---|---|---|
| **ISO 24512** — *Water reuse — Guidelines for treated water usage* | Guidelines covering reuse of treated water for irrigation and other purposes | Contextualises the *purpose* of the effluent-quality measurements the cluster reports. It is a guidelines document, and this monitoring system is an input to a reuse decision, not an implementation of the standard |
| **ISO 16061** — *Irrigation management — Controllers with electrical control interfaces* | Requirements and test methods for irrigation controllers with electrical control interfaces | Potentially relevant to the **downstream controller** that Node 4 forwards frames to. Whether that controller falls within the standard's scope is **Not verified from the current source** — its firmware is not in this repository |
| **EU Water Framework Directive 2000/60/EC** | The EU's overarching water-policy framework, covering the status of water bodies, monitoring programmes and water-use efficiency | Policy context for a European water-reuse and efficiency initiative. The firmware performs no reporting to any authority and produces no regulatory output |

!!! note "Why these are listed at all"
    A reader evaluating whether this monitoring data is fit for a water-reuse
    decision needs to know that the system produces *measurements*, not
    *compliance evidence*. Listing the standards makes that boundary explicit:
    the cluster can supply the readings a reuse assessment would use, and cannot
    itself establish conformance with any of these documents.

## Commonly applicable

Listed for orientation. **None is claimed, referenced or implemented.** Whether
any of them applies to a particular CIRQUA installation is a question for the
project's own quality and regulatory obligations, not for this documentation.

| Standard | Scope | Note |
|---|---|---|
| **ISO 9001** — *Quality management systems — Requirements* | Quality-management-system requirements for organisations | **Explicitly not claimed.** No quality-management system, certification, audit or conformity claim exists for this firmware or for this documentation set. Listed here only because a reader may otherwise wonder whether it applies, and the answer is: it is not asserted |
| **ISO/IEC 17025** — *General requirements for the competence of testing and calibration laboratories* | Competence of laboratories carrying out testing and calibration | Relevant to where calibration of this equipment *should* be performed. No calibration in this project has been performed by an accredited laboratory |
| **ISO 17025 / measurement traceability practice for water chemistry** — *(general practice, not a single standard)* | Traceability of analytical measurements | Any dissolved-oxygen, pH or conductivity value produced by this cluster is an **uncalibrated field estimate** unless validated against traceable reference solutions. See [Validation](../validation/index.md) |

## Referenced by the documentation tooling

These are **not** engineering standards and have no bearing on the firmware. They
are listed because the documentation build genuinely uses them.

| Item | Use |
|---|---|
| **CommonMark** | Markdown syntax used by MkDocs, with the documented Python-Markdown and pymdownx extensions layered on top |
| **RFC 2119 / BCP 14** — *Key words for use in RFCs to Indicate Requirement Levels* | **Not applied to this documentation set.** Where this project needs to distinguish requirement from suggestion, it uses the explicit labels *Recommendation*, *Engineering interpretation* and *Not verified from the current source*, rather than RFC 2119 keywords |

## What would be required to claim conformance

**Recommendation, not a description.** For any of the standards above to be
claimed, all of the following would be needed. None exists today.

| Step | What it involves |
|---|---|
| 1 | Decide which standard is actually being claimed, and for which part of the system. The firmware, the downstream controller and the deployment as a whole are different subjects |
| 2 | Identify the specific clauses and state what "compliance" would mean for a monitoring node — a monitoring device usually cannot "comply" with a water-quality standard; it can only be shown to measure what a compliance assessment needs |
| 3 | Validate each reported quantity against traceable reference standards, with the uncertainty budget stated. No such validation exists for any channel |
| 4 | Write and run conformance tests, then record the results. The repository has no test harness |
| 5 | Record the calibration status, the calibration intervals and the traceability chain for each node |
| 6 | Obtain the hardware documentation that would let the electrical and environmental conditions be assessed at all — see [Datasheets](datasheets.md)) |

## Language this project does not use

These words do not appear in any claim made by this documentation set, and
should not be added to it without the evidence listed above:

* *industrial-grade*, *laboratory-grade*, *certified*, *qualified*, *approved*,
  *production-ready*
* *waterproof*, *IP-rated*, *weatherproof*, *ruggedised*
* *accurate*, *precise*, *calibrated* — where no calibration record exists
* *compliant*, *conforming*, *certified to*, *in accordance with*
* *guaranteed*, *fail-safe*, *safety-rated*

The project's own vocabulary is deliberately narrower: *measured*,
*calculated*, *estimated*, *reported as invalid*, *not verified from the current
source*.

## Related

* [Validation index](../validation/index.md) — what is actually checked.
* [Known Limitations](../validation/known-limitations.md) — the gaps that would
  have to be closed first.
* [Scientific Literature](scientific-literature.md) — the measurement principles
  behind the reported quantities.
* [Official Project Sources](official-project-sources.md) — the project's own
  policy context.
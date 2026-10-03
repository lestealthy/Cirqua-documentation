---
title: Official Project Sources
description: Primary project sources for CIRQUA and African Biotechnology Company, with full attribution, extracted facts and re-verification notes.
---

# Official Project Sources

Every **project-level** claim in this documentation set — funding, duration,
consortium, scope, partner identity — comes from the organisations' own
websites. No third-party summary, press release or conference material is used
for any of them.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Project</span>
    <span class="cirqua-identity__value">CIRQUA — Horizon Europe funded</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Pages consulted</span>
    <span class="cirqua-identity__value">5 CIRQUA pages · 1 ABC page</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Date accessed</span>
    <span class="cirqua-identity__value"><strong>2026-10-03</strong> by all six</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Authority</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--verified">primary</span> — the organisations' own sites</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Re-verification</span>
    <span class="cirqua-identity__value">Required before publication — project facts change</span>
  </div>
</div>

!!! warning "Project facts change. Re-verify before publication."
    Duration, funding and consortium composition are time-varying facts. The
    values on this page were taken from the official sites on **2026-10-03** and
    should be re-checked against those sites before this documentation set is
    published, re-issued or relied on for anything external. Do not extend these
    claims beyond what the pages state.

## Source register

| # | Title | Publisher | URL | Accessed | Authority |
|---|---|---|---|---|---|
| P1 | CIRQUA — home | CIRQUA project | <https://cirqua-water.eu/> | 2026-10-03 | Primary |
| P2 | The Project | CIRQUA project | <https://cirqua-water.eu/the-project/> | 2026-10-03 | Primary |
| P3 | Team | CIRQUA project | <https://cirqua-water.eu/team-2/> | 2026-10-03 | Primary |
| P4 | Work Programme | CIRQUA project | <https://cirqua-water.eu/work-program/> | 2026-10-03 | Primary |
| P5 | African Biotechnology Company — home | African Biotechnology Company | <https://www.african-biotech.com/> | 2026-10-03 | Primary |

## CIRQUA

### Identity

| Field | Value | Source |
|---|---|---|
| Acronym | CIRQUA | P1 |
| Full name | *"Integrated Approaches at Local Scale for Enhancing Water Reuse Efficiency and Sustainable Soil Fertilization from Wastewater's Recovered Nutrients"* | P1, P2 |
| Funding programme | Horizon Europe | P1 |
| Funding amount | **4.09 million EUR** | P1 |
| Duration | **36 months** | P1, P2 |
| Timeline | **April 2024 kick-off → March 2027** | P1, P2 |
| Consortium | **13 partners, 10 countries, 3 continents** | P3 |
| Documented as | The funded research project; owner of all project-level claims | — |

### What the project is about

From P1 and P2:

* Constructed wetlands as **nature-based solutions** for wastewater treatment
  and water recovery, targeted at **rural** areas.
* A **Mediterranean regional focus**.
* Innovative **nanostructured filters** and **photocatalytic modules**.
* **N₂-fixing legume cultivation** for sustainable fertilisation.
* **Sensors and automation** in support of treatment and irrigation.
* **Precision irrigation** and AI tooling.

Stated outcomes (P1, P2):

* Improved effluent quality.
* Treated water **and** constructed-wetland biomass usable for irrigation and
  fertilisation.
* Circular-economy outcomes at local scale.

### Work programme (P4)

The work-programme page describes the project's structure by work package. It is
the source for the claim that **sensors and automation** are one of the project's
technical themes alongside precision irrigation and AI tooling — which is the
thematic justification for a distributed ESP32 monitoring cluster of this kind.

!!! note "The relationship to this documentation set"
    This project documentation describes **the monitoring hardware and firmware
    that WattLab authored and maintains**. It does not claim that the firmware
    is a CIRQUA deliverable, that CIRQUA specified it, or that any node has been
    deployed for the project. See
    [Validation](../validation/index.md) for the honest position on field
    status.

### What is **not** claimed about CIRQUA

* No claim is made about the project's current status, milestones reached or
  deliverables completed.
* No claim is made that this firmware is used by, commissioned by or endorsed
  by the CIRQUA consortium.
* No claim is made about which partner built which node.
* No claim is made about data ownership, retention or the handling of
  measurements collected by the cluster.

## African Biotechnology Company (ABC)

| Field | Value | Source |
|---|---|---|
| Name | African Biotechnology Company | P5 |
| Founded | **2017** | P5 |
| Based in | **Tunis, Tunisia** | P5 |
| Type of organisation | Consulting firm | P5 |
| Services listed | Scientific-project consulting; wastewater treatment plant maintenance; 3D printing and product development; molecular biology services including DNA sequencing, NGS and oligo synthesis | P5 |
| Stated specialisation | Smart irrigation, wastewater reuse and sustainable agricultural technologies | P5 |
| Relationship to CIRQUA | Lists CIRQUA publicly among its projects | P5 |

### What is **not** claimed about ABC

* No specific role in CIRQUA is attributed beyond what the site states. The site
  lists the project; this documentation set does not assign ABC a work package,
  a task or a deliverable.
* No claim is made about ABC's staffing, facilities, certifications or legal
  registration beyond founding year and location.
* No commercial relationship between ABC and WattLab is asserted.

## Roles and attribution

| Organisation | Role in this context |
|---|---|
| **CIRQUA** | The funded research project; owner of project-level claims on its own official site |
| **African Biotechnology Company** | CIRQUA partner; the engineering and custom-equipment context for the site |
| **WattLab** | Authored and maintains this documentation and the firmware |
| **This documentation set** | A technical description of firmware, hardware interfaces and validation practice. It is **not** an official CIRQUA publication, and it makes no claim on CIRQUA's behalf |

## Re-verification procedure

**Recommendation.** Before publishing or re-issuing this documentation set:

1. Re-open P1 to P5 and confirm each URL still resolves.
2. Re-check the funding amount, the 36-month duration, the April 2024 → March 2027
   timeline, and the 13-partner / 10-country / 3-continent consortium figure.
3. Re-check the full project title for wording changes.
4. Re-check ABC's founding year and location.
5. Update the *Accessed* date in [Source Registry](source-registry.md) and in
   the table above.
6. If any value has changed, update [Project Overview](../project/overview.md)
   and [System Context](../project/system-context.md) in the same change, and
   note it in the documentation revision history.

!!! warning "Do not extrapolate"
    Nothing on this page may be extended beyond the sources listed. In
    particular, do not state a consortium size, a duration or a work-package
    structure that is not on P1–P4, and do not attribute a CIRQUA role to any
    organisation beyond what its own site states.

## Related

* [Project Overview](../project/overview.md) — how these facts are used in the
  narrative pages.
* [System Context](../project/system-context.md) — the project's setting and
  where the monitoring cluster sits in it.
* [Terminology](../project/terminology.md) — the project's own vocabulary.
* [Source Registry](source-registry.md) — machine-readable form.
* [Validation](../validation/index.md) — what is verified, and what is not.
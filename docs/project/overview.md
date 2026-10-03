---
title: Project Overview
description: CIRQUA in brief — Horizon Europe project name, 4.09M EUR budget, 36-month duration from April 2024, 13 partners, and where the monitoring platform fits.
---

# Project Overview

## What CIRQUA is

**CIRQUA** — *"Integrated Approaches at Local Scale for Enhancing Water Reuse
Efficiency and Sustainable Soil Fertilization from Wastewater's Recovered
Nutrients"* — is a **Horizon Europe funded research project**, branded under
the theme **"Waterwise Futures"**.

> **Project fact.** The figures and scope statements below are reproduced from
> the official project site, `https://cirqua-water.eu/`, consulted 2026-10-03.
> They are attributed to the CIRQUA project, not to this documentation set. See
> <a href="../references/official-project-sources.html">Official Project
> Sources</a>.

| Attribute | Value | Source |
|---|---|---|
| Full name | Integrated Approaches at Local Scale for Enhancing Water Reuse Efficiency and Sustainable Soil Fertilization from Wastewater's Recovered Nutrients | `cirqua-water.eu` |
| Branding | Waterwise Futures | `cirqua-water.eu` |
| Programme | Horizon Europe | `cirqua-water.eu` |
| Funding | 4.09 million EUR | `cirqua-water.eu` |
| Duration | 36 months, April 2024 kick-off → March 2027 | `cirqua-water.eu` |
| Consortium | 13 partners, 10 countries, 3 continents | `cirqua-water.eu` |
| Thematic focus | Constructed wetlands (CW) as nature-based solutions for wastewater treatment and water recovery in rural areas; Mediterranean region | `cirqua-water.eu` |

## Project scope as stated by the official site

The official description names the following technical strands:

* Constructed wetlands as **nature-based solutions** for wastewater treatment
  and water recovery, with emphasis on **rural** areas and the **Mediterranean**
  region.
* Innovative **nanostructured filters** and **photocatalytic modules**.
* **N2-fixing legume cultivation**.
* **Sensors and automation**.
* **Precision irrigation**.
* **AI tooling**.

Stated project outcomes are improved effluent quality; treated water and
constructed-wetland biomass usable for irrigation and fertilisation; and
circularity at local scale.

## Where the monitoring platform fits

The firmware documented on this site implements **sensors and automation** — one
of the strands named in the official project description. It is an ESP32 node
cluster that measures tank volumes, flow, dissolved oxygen, temperature,
humidity, pH, turbidity and electrical conductivity, and passes the readings
along a serial chain to a downstream controller.

> **Engineering interpretation.** The platform's role is *measurement and
> reporting*: it produces a parameter set describing water quantity and water
> quality in the treatment train. It does not itself treat water, drive a pump,
> dose a nutrient or close a control loop — no actuator output is present in the
> audited firmware.

> **Not verified from the current source.** The firmware repository contains no
> statement of which CIRQUA work package, partner site or pilot installation this
> code belongs to, and no evidence that any node is physically deployed in the
> field. Any mapping between this platform and a specific project work package
> or site must come from the project, not from this repository.

## Relationship between the project and the engineering work

CIRQUA is the funded project and owns project-level claims. **African
Biotechnology Company** is a CIRQUA partner. **WattLab** authored and maintains
this documentation and the firmware. These are separate roles; no organisation
owns another's marks. Full detail is on the <a href="index.html">homepage</a>.

## Where to go next

* What the project is trying to achieve — <a href="objectives.html">Objectives</a>
* Where this hardware sits in the wider system — <a href="system-context.html">System Context</a>
* What the abbreviations mean — <a href="terminology.html">Terminology</a>

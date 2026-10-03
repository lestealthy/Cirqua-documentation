---
title: Project Objectives
description: The stated central objective of the CIRQUA project and the nutrient-valorisation, precision-use and circular-economy strands it is built from.
---

# Project Objectives

All content on this page is a **project fact** reproduced from the official
project site `https://cirqua-water.eu/`, consulted 2026-10-03. It is attributed
to the CIRQUA project. See
<a href="../references/official-project-sources.html">Official Project
Sources</a>.

## The central objective

The central objective of CIRQUA is to **upgrade existing non-conventional,
decentralised wastewater treatment technologies, with a focus on constructed
wetlands as nature-based solutions (NBS)**, so that water reuse and the recovery
of nutrients from treated wastewater both become practical at local scale.

Two elements of that sentence matter for the engineering work:

* **Upgrade existing** — the project builds on decentralised, non-conventional
  treatment already in place rather than on a new centralised plant. Any
  instrumentation therefore has to work inside an existing rural installation.
* **Constructed wetlands as NBS** — the treatment technology is biological and
  surface-based, so the measurements of interest are water depth/quantity,
  water quality and flow, in outdoor conditions.

## Nutrient valorisation for precision use

A named strand of the project is the **use of the nutrients recovered from
wastewater for precision irrigation and fertilisation**. In practice this is
what gives rise to a need to measure:

* **Water quantity** — how much water is available, per tank and per unit time.
* **Water quality** — pH, electrical conductivity and turbidity, which together
  indicate salinity, nutrient loading and solids.
* **Process state** — dissolved oxygen and temperature in the treatment
  medium, and ambient temperature and humidity as environmental context.

> **Engineering interpretation.** These are the parameters a nutrient-reuse
> decision depends on, and they correspond to the measurement set implemented by
> the ESP32 node cluster: tank volumes, flow rate, dissolved oxygen, temperature,
> humidity, pH, turbidity and conductivity. The correspondence is an author's
> reading; the firmware repository does not state which project deliverable it
> supports.

## Circular economy at local scale

The stated outcome is a **circular economy at local scale**: water is treated
and reused locally, and the recovered nutrients — including constructed-wetland
biomass — are returned to the soil as fertiliser. This is why reuse and
fertilisation appear together in the project name.

## Precision irrigation

The project names **precision irrigation** and **AI tooling** among its strands.
The monitoring platform's contribution to that strand is limited to supplying
measurements; no irrigation scheduling, control or decision logic exists in the
audited firmware.

> **Not verified from the current source.** No AI, machine-learning, irrigation
> control, dosing or actuator code exists in the firmware repository at commit
> `db6d9b8`. Any claim that this platform performs irrigation control would be
> unsupported.

## How the project objective relates to this documentation

This documentation set covers **only** the monitoring hardware and firmware.
Project strategy, deliverables, reporting and the scientific case are outside
its scope and are owned by the project. What the engineering pages must preserve
is the measurement contract — what is measured, how, in what unit, and with what
uncertainty — because that contract is the only thing this platform contributes
to the project objectives described above.

Next: <a href="system-context.html">System Context</a> places the cluster in the
wider system, including the boundaries the firmware does not cross.

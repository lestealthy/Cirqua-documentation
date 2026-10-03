---
title: Scientific Literature
description: Scientific references behind the measurement principles CIRQUA uses, with identifiers that must be verified before publication.
---

# Scientific Literature

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Purpose of this page</span>
    <span class="cirqua-identity__value">Background framing only — never a source of a value quoted on a sensor page</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">References listed</span>
    <span class="cirqua-identity__value">A small number of well-established works</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">DOIs, volumes, pages given</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--unknown">deliberately omitted</span> where not certain</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Bibliographic check performed</span>
    <span class="cirqua-identity__value">No catalogue lookup — see the warning below</span>
  </div>
</div>

!!! danger "Read this before citing anything from this page"
    These references are given from **established knowledge of the field**, not
    from a catalogue lookup performed during this documentation build. Authors,
    titles, venues and years are given because they are long-standing and
    well-known. **Exact DOIs, volume numbers, issue numbers and page ranges are
    deliberately not given, because inventing or misremembering an identifier is
    worse than omitting it.**

    > Every identifier on this page — and every citation taken from it — **must
    > be verified against the publisher's record before publication.** Where a
    > DOI is given as a *pattern* rather than a number, treat it as a search
    > instruction, not as a citation.

    A short list of real, well-known works is more useful than a long list of
    plausible-looking ones. This page deliberately contains only the former.

## What this page is for, and is not for

| Use | Appropriate? |
|---|---|
| Explaining *why* temperature compensation matters for dissolved oxygen | Yes |
| Explaining *why* constructed wetlands are the project's treatment technology | Yes |
| Supporting the existence of an N₂-fixing legume approach in the project | Yes |
| Justifying a numeric value quoted on a sensor page | **No** — those come from the firmware, or they are marked unverified |
| Justifying a sensor accuracy or range figure | **No** — see [Datasheets](datasheets.md)) |
| Justifying a calibration coefficient in the source | **No** — the firmware's constants are used as they are, not defended |

## Constructed wetlands

### Kadlec and Wallace — treatment wetlands

* **Authors:** R. Kadlec and W. Wallace
* **Nature of the work:** the foundational treatment of *treatment wetlands* —
  systems in which microbial and plant processes in a wetland are used
  deliberately to remove contaminants from water, distinguishing them from
  conventional treatment works
* **What it is used for here:** the conceptual basis for the project's choice of
  constructed wetlands as a nature-based treatment technology. The work explains
  the mechanism that makes wetlands a treatment device, which is the reason the
  project's interest in them is technical and not merely ecological
* **Citation to verify:** Kadlec, R. and Wallace, W., work on treatment wetlands.
  Locate the specific publication through the publisher's catalogue or a
  bibliographic database before citing. No DOI, volume or page range is asserted
  here

### Vymazal — constructed wetlands reviews

* **Author:** Jan Vymazal
* **Nature of the work:** extensive review literature on horizontal-flow and
  vertical-flow constructed wetlands, including performance data for organic
  load removal and for the operation of treatment wetlands at pilot and
  full scale
* **What it is used for here:** the performance context in which the measured
  quantities make sense — that effluent quality from such a system varies with
  loading and season, and that monitoring a *range* of parameters (organic load,
  nutrients, suspended solids, pH) is a normal requirement rather than an excess
* **Citation to verify:** Vymazal, J., review papers on constructed wetlands for
  wastewater treatment. Identify the specific review intended through a
  bibliographic database. No DOI, volume or page range is asserted here

!!! note "Deliberate omission"
    No performance figure from any of this literature is quoted on any CIRQUA
    sensor, node or calibration page. The relationship between published wetland
    performance and this specific installation has not been established, and
    quoting a literature range here would invite a reader to treat it as a
    specification for this system.

## Dissolved oxygen and temperature

* **Nature of the work:** the solubility of oxygen in water falls with
  temperature, and the fall is well characterised; equally, the response of an
  oxygen-sensing probe is temperature dependent. Both facts are why dissolved
  oxygen has to be compensated for temperature before it means anything
* **What it is used for here:** it justifies the *existence* of the firmware's
  compensation term `compFactor = 1.0 + (T − 25.0) × (−0.02)` in `Node2.ino`, and
  of the temperature compensation in Node 4's pH and conductivity conversions
* **What it does not justify:** the specific coefficient `−0.02` per °C, the
  saturation value `8.26 mg/L` at 25 °C, or the two-point voltage constant. Those
  are **firmware constants**, taken from the source, and none of them is
  validated against a reference. The sensitivity of dissolved oxygen to
  temperature is *why* the constant exists, not evidence that the constant is
  right

## Nitrogen fixation

* **Context:** biological nitrogen fixation by symbiotic and free-living
  nitrogen-fixing organisms — including crop legumes — is the basis of
  legume-based approaches to reducing synthetic fertiliser input, and
  N₂-fixing legume cultivation is named as one of the CIRQUA project's themes on
  the project's own site
* **What it is used for here:** to note that the project describes an
  N₂-fixing legume strand, and that this monitoring cluster measures the water
  side of the system — nutrients, pH, conductivity, dissolved oxygen — and
  **not** the nitrogen or biomass side
* **Citation status:** the project-level claim is sourced to the CIRQUA site, not
  to literature. See [Official Project Sources](official-project-sources.md).
  No literature citation is offered here, because the project does not specify
  which biological nitrogen-fixing system it intends, and citing one would imply
  a specificity the source does not support

!!! warning "An important boundary"
    **This firmware measures nothing about nitrogen fixation.** There is no
    nitrogen sensor, no nitrate channel, no biomass measurement and no phenology
    input anywhere in the cluster. Any reader connecting this monitoring system to
    the project's legume theme should understand that the connection is at the
    level of shared site and irrigation water, not at the level of a shared
    measurement.

## Electrical conductivity as a water-quality quantity

* **Nature of the work:** bulk electrical conductivity in water is a standard
  surrogate for the concentration of dissolved ions, is strongly temperature
  dependent, and is reported in µS/cm or mS/cm with the reference temperature
  stated
* **What it is used for here:** it justifies normalising conductivity to a
  reference temperature — which is what Node 4's `ecCoefficient = 1 + 0.0185 ×
  (T − 25)` does — and it justifies stating the unit on every reported value
* **What it does not justify:** the K-factor `9.997`, which has no documented
  provenance in the firmware or anywhere else, and which converts the probe's
  analogue output to µS/cm. That number is a **field calibration constant** and
  must be established per probe, per installation

## pH measurement

* **Nature of the work:** the glass electrode potential follows the Nernst
  equation, giving a near-linear voltage–pH relation with a slope that itself
  depends on temperature
* **What it is used for here:** it explains why temperature compensation exists
  in the firmware, and why a two-point affine calibration is the normal practical
  approach for a field probe
* **What it does not justify:** the firmware's actual model, which is a plain
  `slope × voltage + offset` and **not** a Nernst implementation. That choice is
  recorded as deliberate in the source — *"Existing calibration model preserved"* —
  and is documented as a limitation, not defended here. See
  [pH](../sensors/ph.md) and
  [Known Limitations](../validation/known-limitations.md)

## Ultrasonic level measurement

* **Nature of the work:** time-of-flight distance measurement assumes a known
  speed of sound, which depends on air temperature, and converting a height to a
  volume assumes a known vessel geometry
* **What it is used for here:** it identifies the two systematic biases the
  firmware does not correct — an uncompensated speed-of-sound constant, and a
  zero assumed sensor offset — and it explains why a tank modelled as a right
  circular cylinder will mis-report a tank that is not one
* **What it does not justify:** any accuracy figure for this system. None is
  quoted anywhere in this documentation set

## Turbidity

* **Nature of the work:** turbidity sensing modules are vendor-calibrated: a
  specific sensor's analogue output maps to a nephelometric turbidity unit scale
  through a characteristic relationship, usually a piecewise fit rather than a
  physical law, and the relationship is specific to the module and often to its
  supply voltage
* **What it is used for here:** it explains why the firmware's turbidity
  conversion is a fixed quadratic with explicit breakpoints rather than a
  derived formula, and why a different module would need a different curve
* **What it does not justify:** that the curve in the firmware matches the module
  actually installed. The source names `SEN0189 / DFRobot` in a comment; the
  fitted module is **Not verified from the current source**

## Citations to add when the gap is closed

**Recommendation.** The following would let this page carry proper identifiers:

1. A bibliographic-database lookup for each work named above, recording DOI,
   volume, issue and pages, or the publisher's stable URL and ISBN.
2. Access dates recorded in [Source Registry](source-registry.md).
3. Manufacturer datasheets for the parts named in the firmware, so that device
   specifications can be cited from the manufacturer rather than from review
   literature. See [Datasheets](datasheets.md)).
4. Traceable reference methods for the dissolved-oxygen, pH and conductivity
   channels, so that "compared against" can replace "compared by eye".
5. A decision on whether literature is needed at all for the sensor pages — an
   argument for keeping values out of the literature and in the firmware
   constants is a legitimate one.

## Related

* [Sensors index](../sensors/index.md) — the pages this page frames.
* [Calibration index](../calibration/index.md) — what has to be calibrated, and
  against what.
* [Datasheets](datasheets.md) — where device specifications would come from.
* [Official Project Sources](official-project-sources.md) — the source for the
  project's own themes.
* [Standards](standards.md) — and why none is claimed.
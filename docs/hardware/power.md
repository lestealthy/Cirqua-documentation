---
title: Power
description: What the CIRQUA firmware implies about power — 3.3 V logic, ADC input range limits, LCD backlight draw — and the supply data still undocumented.
---

# Power

!!! warning "Read this first"

    **Supply rails, currents, regulators, battery capacity and solar topology
    are not present anywhere in the firmware repository.** There are no
    schematics, no BOM and no hardware documentation in the source tree. This
    page records only what the code *implies*, and is explicit about the
    remainder.

## Firmware implementation — what is actually stated in the source

| Statement | Where it comes from |
|---|---|
| The ESP32 logic domain is **3.3 V** | Implied by the ESP32 platform and by the millivolt-based ADC code on Node 4, which relies on a 3.3 V-class full-scale input |
| Node 2 comment: *"sensor boards may be powered from 5 V but their analog output must remain within the ESP32 ADC input range"* | `Node2.ino`, dissolved oxygen section |
| Node 4 uses `ADC_11db` attenuation, giving a usable input range well above 3.3 V | `configureADC()` |
| Node 4 validity gates reject any analogue input above **3.30 V** | pH, turbidity and EC validity rules |
| Node 2 dissolved oxygen conversion assumes a **5000.0 mV** reference (`VREF`) scaled across the full 4095-count 12-bit range | `VREF 5000.0f`, `ADC_RESOLUTION 4095.0f` |
| Node 4 turbidity engineering note: the legacy code wrongly assumed a 5.0 V ADC reference; the current code uses the **real voltage at the ESP32 pin** | `Node4.ino` turbidity section |
| LCD backlight is driven, but the firmware sets no PWM duty and no current limit | `lcdN4` / Node 1 LCD initialisation |

## The 3.3 V / 5 V boundary — the one real constraint the code states

**Firmware implementation.** The Node 2 comment is the clearest statement in
the whole firmware about the power situation, and it describes a mixed-domain
system:

* Sensor boards **may** be supplied from 5 V.
* Their **analogue outputs must** remain inside the ESP32 ADC input range.

That is a genuine hazard and it is the reason the following appears in
<a href="gpio-map.html">GPIO Map</a> and <a href="wiring.html">Wiring</a>:

| Signal | Native level | ESP32 pin tolerance |
|---|---|---|
| Node 4 pH / turbidity / EC analogue | Typically 0–5 V sensor boards | Firmware rejects anything `> 3.30 V` |
| Node 2 DO analogue | Board may be 5 V powered | Firmware assumes a 5000 mV full-scale reference |
| HC-SR04 ECHO | **5 V logic level** | 3.3 V GPIO — **real overvoltage risk** |

**Engineering interpretation.** The firmware's use of `ADC_11db` attenuation on
Node 4 suggests the designers intended the analogue inputs to be tolerant of
signals up to roughly 5 V, with the 3.30 V validity ceiling then acting as a
*data-quality* gate rather than a hardware gate. That is a reading of intent,
not a documented electrical specification.

**Recommendation.** Do not rely on `ADC_11db` as a protection device. Fit
properly scaled dividers or a level shifter on every 5 V signal entering a
3.3 V GPIO, and verify with a meter before first power-up.

## Practical consequences for field power budgeting

**Engineering interpretation.** Even without a current budget in the
repository, the firmware is enough to reason about load shape:

| Load | Where | Notes |
|---|---|---|
| ESP32 core plus Wi-Fi (SMTP variant only) | Node 4 SMTP | Wi-Fi TX bursts dominate; the variant calls `WiFi.begin()` and keeps the radio associated |
| ESP32 core, no Wi-Fi | Nodes 1, 2, 3, 4 | Sensors and LCD only |
| 16×4 LCD backlight | Nodes 1, 4 | Driven constantly; no PWM, no auto-dim |
| HC-SR04 modules | Nodes 1, 2, 4 | Driven from 5 V in practice; see the note above |
| Dissolved oxygen, pH, turbidity, EC probe boards | Node 2, Node 4 | Typically the largest continuous draw on the node |

**Recommendation.** Because the firmware gives no duty-cycle control — the LCD
backlight is never dimmed, the ultrasonic modules are triggered on a fixed
schedule, and there is no deep-sleep path anywhere in the cluster — the power
budget for each node should be built around **continuous average draw**, not
peak draw. Any battery or solar sizing must be derived from a measured average
current on the assembled node, not from component datasheet maxima.

**Recommendation.** If field autonomy is important, note that no node enters
light sleep or deep sleep in the current firmware. Any low-power redesign is a
firmware change and would invalidate the timing model in
<a href="../rtos/scheduling.html">RTOS Scheduling</a>.

## What must still be documented

None of the following is present in the repository. Each needs a hardware
design record or a measured value before the platform can be installed and
serviced reliably.

| Item | Status |
|---|---|
| Supply voltage per node (battery bus voltage, rail voltage at the board) | **Not verified from the current source.** |
| Regulator part numbers, topology and efficiency | **Not verified from the current source.** |
| Current budget per node, average and peak | **Not verified from the current source.** |
| Wi-Fi peak current for the SMTP variant | **Not verified from the current source.** |
| LCD backlight current and whether it is switched at all in hardware | **Not verified from the current source.** |
| Battery chemistry, capacity, self-discharge, usable depth of discharge | **Not verified from the current source.** |
| Solar panel size, charge controller type and set points | **Not verified from the current source.** |
| Charge and load protection scheme, fuses, reverse-polarity protection | **Not verified from the current source.** |
| Power-down / power-loss behaviour of the nodes and of any downstream controller | **Not verified from the current source.** |
| Cable gauges and voltage drop over inter-node runs | **Not verified from the current source.** |
| Earthing, bonding and lightning/surge protection strategy | **Not verified from the current source.** |

## Related pages

* <a href="wiring.html">Wiring</a> — where the 3.3 V and 5 V domains meet.
* <a href="controllers.html">Controllers</a> — ADC configuration and the ADC2
  conflict on the SMTP variant.
* <a href="gpio-map.html">GPIO Map</a> — which pin each signal uses.
* <a href="enclosures.html">Enclosures</a> — enclosure thermal monitoring that a
  power budget must account for.

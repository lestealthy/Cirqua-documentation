---
title: Known Limitations
description: Limitations register for the CIRQUA firmware - protocol, sensor, electrical and operational gaps, with severity, impact and mitigations.
---

# Known Limitations

This is the honest list. It records what the firmware **cannot** do, what it
does imperfectly, and where a field technician should expect to be surprised.
Nothing here is speculative: every entry is traceable to the source at commit
[`db6d9b8`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55).

!!! warning "Severity is engineering judgement, not a measurement"
    The severity column is the documentation author's assessment of how much a
    limitation affects the usefulness of the monitoring data. It is **not** a
    formal risk rating, a probability estimate or a safety classification, and
    no such classification is claimed anywhere in this project.

Severity scale used below:

| Level | Meaning |
|---|---|
| **High** | Produces data that can be silently wrong, or a failure that is invisible |
| **Medium** | Degrades accuracy or diagnosability; a technician can usually work around it |
| **Low** | Cosmetic, minor inconvenience, or a documented-and-accepted behaviour |

## Register

| # | Limitation | Severity | Impact | Affected node(s) | Mitigation | Status |
|---|---|---|---|---|---|---|
| L01 | **No checksum, CRC, sequence number, acknowledgement or retry** in the protocol. The only integrity check is key presence in `validateUpstreamFrame` | High | A corrupted frame is forwarded, and a lost frame is never recovered. Because receivers reset their buffer index on overflow, a truncated frame can be silently discarded and the next one mis-parsed | All | None in firmware. Accept or add a CRC and a sequence number; treat gaps in the record as expected. On the SMTP variant, Node 3's fallback frame at least marks `node1:0`/`node2:0` so a total upstream loss is visible | Accepted, not mitigated |
| L02 | **Invalid sensor values are transmitted as `0.00`**, so zero is ambiguous | High | A disconnected probe and a genuine zero reading are indistinguishable on the wire. The only disambiguator is a per-node health flag, not per-quantity | 1, 2, 3, 4, 4 SMTP | Read the `nodeN:` flag alongside the value. A field log that stores values without the flags cannot distinguish the two cases retrospectively | Accepted, not mitigated |
| L03 | **No store-and-forward anywhere in the chain** | High | A broken link or an unpowered node loses data permanently. Node 4 absent means the controller receives nothing at all | All | External buffering at the controller, or the SMTP variant's e-mail as an independent path | Accepted, not mitigated |
| L04 | **No node addressing on the wire** — frames carry a health flag but no identity | High | Physically swapping two similar nodes is undetectable. Two Node 4 units swapped produce valid-looking frames from the wrong tank | All | Physical labelling and QR identification; see [Node Identification](../field-service/node-identification.md). Adding a node-id field would be a protocol change | Accepted, not mitigated |
| L05 | **Node 1's unexplained `2.0f` volume factor** (`(int)(volumeLiters * 2.0f)`) | High | `TAV` is not a geometric result. Reported volume is roughly double the cylinder calculation, and the maximum the display can show (≈19758 L) is roughly double what the geometry can hold (≈9879 L) | 1 | Characterise against a physical measurement and either justify or remove the factor. Until then do not compare `TAV` with a dip stick or tank data sheet | **Open — undocumented in source** |
| L06 | **No runtime calibration for dissolved oxygen, turbidity or flow** — compile-time constants only | Medium | Recalibrating dissolved oxygen or flow requires editing and reflashing the sketch, which is a bench task, not a field task | 2, 3 | Edit `SATURATION_DO_25C` / `FLOW_CAL_FACTOR` and reflash, per [Configuration](../firmware/configuration.md). The Node 4 console pattern could be extended to these quantities | Open |
| L07 | **pH uses a legacy linear slope/offset model, not a Nernst law** | Medium | Accuracy is limited to the calibrated range; extrapolation outside it is not physically meaningful. Two-point calibration cannot follow the true pH–voltage curve | 4 | Keep operation inside the calibrated range and re-calibrate if the probe or buffer range changes. The source comment records this as deliberate: *"Existing calibration model preserved"* | Accepted by design |
| L08 | **Turbidity has no runtime calibration and is not temperature compensated** | Medium | The quadratic is a fixed fit for the named sensor module. Optical scattering is temperature dependent, so a warm sample reads differently from a cold one at identical turbidity | 4, 4 SMTP | Accept the drift, or record temperature alongside turbidity so it can be modelled downstream. Note `Node4_SMTP` additionally routes the conversion through an intermediate 5 V-referred voltage | Open |
| L09 | **Ultrasonic measurement assumes a zero sensor offset** — the source comment reads *"True 0-offset ultrasonic calculation"* | Medium | A transducer mounted below the configured tank height biases every reading by a constant amount, and nothing in the firmware can detect or correct it | 1, 2, 4 | Record the actual transducer height above the maximum water line and adjust `TANK_HEIGHT` accordingly | Accepted by design |
| L10 | **Node 1's HC-SR04 uses a 30 ms echo timeout, giving a maximum range of about 5.1 m** | Medium | A full or badly aimed tank can produce a late or missing echo. Node 1 is the only node whose timeout is long enough to be noticeable, and its tank is the largest | 1 | Keep the transducer aimed and unobstructed; treat a sudden `0` reading as suspect rather than as an empty tank. Nodes 2 and 4 use shorter timeouts (20 ms / 25 ms) and reject implausible distances | Accepted |
| L11 | **DHT11 is a low-accuracy, slow sensor** | Medium | Absolute temperature and humidity values carry meaningful error, and the part's own accuracy is modest. Its 1 Hz-class conversion is the reason for the 2000 ms pacing gate | 2, 4, 4 SMTP | Treat ambient values as indicative — they drive status strings and fault thresholds, not water-quality reporting. Do not calibrate against them | Accepted |
| L12 | **Node 4's ADC2 channels are shared with the Wi-Fi radio** (GPIO 12, 13, 14) | High on the SMTP variant | On `Node4_SMTP`, `analogRead` competes with the Wi-Fi driver for ADC2. Readings taken while the radio is active can be biased or unavailable. Plain `Node4` has no radio, so its ADC2 use is uncontended | 4 SMTP | Prefer a board/channel plan that moves pH, turbidity and EC to ADC1 (GPIO 32–39 range). GPIO 12 is also a strapping pin, which is an independent risk | **Open** |
| L13 | **HC-SR04 echo is a 5 V logic signal into a 3.3 V GPIO, with no documented level shifting** | High | On paper this exceeds the ESP32 input range. Whether it is a real fault depends on the fitted module's actual output swing, which is not established anywhere in the repository | 1, 2, 4 | > **Not verified from the current source.** Confirm the module's echo amplitude, or fit a divider or level shifter. Do not assume the inputs are 5 V tolerant | **Open — no documentation exists** |
| L14 | **`systemFatalTrap` halts the node permanently on allocation failure** | Medium | If a mutex or task cannot be created the node stops: no display, no telemetry, no self-recovery. On Nodes 1–3 the only evidence is one line on the debug UART | All | Treat a silent node as a possible fatal trap and read its serial output. If halting proves to be the wrong trade in a given deployment, retry with backoff instead | Accepted by design |
| L15 | **No brownout or watchdog strategy is visible in the firmware** | High | Nothing in these sketches configures a brownout detector or a task watchdog. A brownout or a starved task therefore manifests as a silent node or as a node reporting stale values, depending on where it fails | All | > **Not verified from the current source** — the repository contains no brownout or watchdog configuration. Consider enabling the hardware brownout detector and a task watchdog as a firmware improvement | **Open** |
| L16 | **No unit tests, no test harness and no CI in the firmware repository** | Medium | A regression in a constant or a format string is not caught automatically. Documentation fidelity is checked; firmware behaviour is not | All | Adopt [Test Strategy](test-strategy.md)), starting with the documentation checks and the pure conversion functions | **Open** |
| L17 | **Credentials in `Node4_SMTP.ino` are placeholders** | High if mishandled | The committed values are `YOUR_WIFI_SSID`, `YOUR_WIFI_PASSWORD` and example mailbox addresses. A node built from the committed file has no working network. **Conversely**, if real credentials are ever committed, the SSID, the Wi-Fi passphrase and the mailbox app password are exposed in version control history | 4 SMTP | Never commit real values. Supply them at build time from an untracked source. The documentation extractor redacts the two password macros automatically. If real credentials are ever found in a commit, treat it as an incident and rotate | Accepted with a hard rule |
| L18 | **The 45 °C and 80 % thresholds are attributed in comments to the Node 2 enclosure, but are applied on Node 1** | Medium | Node 1's `OVERTEMP` / `HI HUMID` / `HOT+HUM` status strings are driven by Node 2's DHT11 while the source comment labels them as enclosure limits. The intent is ambiguous: a Node 1 tank overheat would not trip them | 1 (measuring Node 2's DHT11) | Confirm the intended location with the firmware author. If Node 1's own enclosure can overheat, the thresholds belong on the node that measures that enclosure | **Open — ambiguous in source** |
| L19 | **Node 3 marks every flow sample valid, so a disconnected flow sensor is indistinguishable from no flow** | Medium | `FLM:0.00` with `node3:1` occurs both when nothing is flowing and when the sensor is unplugged. A dry line and a failed sensor look the same | 3 | Monitor `FLM` for plausibility outside the firmware. Adding a "no pulse for N seconds" validity rule would close it, at the cost of mis-flagging genuinely still water | **Open** |
| L20 | **Node 2's reverse-telemetry parser is dead code** — it looks for `\|FR:` while Node 3 emits `\|FLM:`, and the struct it populates is never read | Low today, Medium as a trap | Nothing is currently broken, because nothing consumes the data. But the code implies a capability that does not exist, and the key rename was never propagated | 2, 3 | Either update the parser to `\|FLM:` and use the data, or delete the parser and the struct. Leaving both is the worst option | **Open — divergence, silent** |
| L21 | **`Node4_SMTP` does not clean the upstream packet** | Medium | The controller receives Node 2's ambient `AT:`/`AH:` from an SMTP unit instead of a single pair measured at the water-quality enclosure. Two units with the same GPIO map behave differently on the wire | 4 SMTP | Port `cleanUpstreamPacket` to the variant, or document the divergence in the controller's expectations. Verify which behaviour the controller requires before deploying either variant | **Open — divergence** |
| L22 | **`Node4` and `Node4_SMTP` differ in downstream fields, calibration defaults and available features** | Medium | The two are not interchangeable. Different field names (`TCV` vs `EV`/`ST`), different conductivity units (µS/cm integer vs mS/cm one decimal), different default calibration, and only `Node4` has the console | 4, 4 SMTP | Track which variant each physical unit carries — nothing reports it at runtime. See [Node 4 SMTP](../nodes/node4-smtp.md) | Accepted, documented |
| L23 | **Node 4's LCD prints stored values with no invalid-value substitution and has no status line** | Medium | An invalid pH appears as `pH:0.0` and an invalid turbidity reading as `TU:0`. The validity information exists only on the debug UART | 4, 4 SMTP | Read the `[LOCAL SENSORS]` block in the transaction output, not the LCD, when assessing validity | Accepted by design |
| L24 | **Unused ADC work on every Node 4 cycle** — `phRaw`, `turbRaw` and `ecRaw` are averaged but never used, and `adcToVoltage` has no call site | Low | Roughly doubles the ADC time spent per cycle for no benefit, and dead code invites confusion when reading the conversion path | 4 | Remove the unused reads, or use them for the diagnostics they were evidently intended for | **Open — cleanup** |
| L25 | **`Serial.readStringUntil('\n')` blocks Node 4's UART task** | Medium | An unterminated console command stalls telemetry forwarding for as long as the operator waits to press Enter. Frames arriving in the interval are lost, with no replay | 4 | Type complete lines and press Enter promptly; avoid leaving the console connected during normal operation | Accepted |
| L26 | **Node 4's debug transaction block can saturate the 115200 baud channel** | Low to Medium | While the chain is healthy, the printed block is emitted per received frame at the routing task's cadence. Output can interleave with itself and consume most of the debug channel | 4 | Treat the debug UART as a diagnostic aid, not a data channel. Detach it once bring-up is complete | Accepted |
| L27 | **No filtering on any ultrasonic measurement** | Medium | One reading per cycle is used directly, with no median, no moving average and no outlier rejection. A single spurious echo passes straight through on Nodes 1 and 2 | 1, 2 | Repeat measurements and average outboard, or add a median filter in firmware | Open |
| L28 | **Nodes 1 and 2 perform no plausibility check on the distance** | Medium | A short or spurious echo becomes a *valid* near-full-tank reading rather than an invalid one. Only Node 4 rejects distances above `TANK_HEIGHT + 20` | 1, 2 | Treat an implausibly high level reading as suspect. Port Node 4's rejection rule to Nodes 1 and 2 | **Open** |
| L29 | **Node 2's dissolved-oxygen conversion assumes a 5 V ADC full scale (`VREF 5000.0f`) on a 3.3 V ESP32** | Medium | The comment describes it as *"ADC Reference Voltage (mV) on 3.3V ESP32"*, but the value implies a 5 V span. If the true span is 3.3 V, every `DO` reading is scaled too high by roughly the ratio of the two | 2 | > **Engineering interpretation.** Compare `DO` against a calibrated reference before trusting the absolute value. Correcting the reference is a one-line change plus a re-calibration | **Open — needs bench verification** |
| L30 | **No pulse-count overflow detection on the flow counter** | Low | `g_pulseCount` is a free-running `uint32_t`. A reset partway through a second, or an extremely long accumulation, could yield a wrong rate | 3 | Resetting the counter every second already bounds accumulation to one second of pulses; overflow is not a practical concern at plausible flow rates | Accepted, low risk |
| L31 | **The chain is serial and fragile by construction** | High | Node 1 *originates* the frame and no node regenerates upstream fields. A break anywhere upstream of Node N means Node N sees no frame at all | All | Segment monitoring at the controller, or independent alerting on the SMTP variant. Architectural change would be needed to remove this | Accepted by design |
| L32 | **No firmware version or commit identifier is reported** | Medium | There is no way to tell from a node, its LCD, its debug output or the wire which firmware it is running. Field-to-repository traceability is manual bookkeeping | All | Record the commit at flashing time, per node. Adding a version field to the frame and a boot line to each sketch would close it | **Open** |
| L33 | **The ultrasonic, DO and flow conversions are not validated against any reference** | Medium | The documentation set contains no measurement comparing these outputs to a traceable standard. Formulas are verified as *implemented*; they are not verified as *correct* | 1, 2, 3 | Perform the calibration procedures on [Calibration](../calibration/index.md) against reference solutions and volumes, and record the results | **Open** |
| L34 | **DS18B20 failure degrades to uncompensated readings rather than invalid ones** | Low to Medium | When the submerged probe is invalid, pH and EC fall back to 25 °C compensation and still report valid. A pH reading can therefore be *valid but wrong* with no flag on the wire | 4 | Treat a `node4:0` flag as also casting doubt on the compensated values, and check `[DS18B20] Devices found:` after any probe change | Accepted by design |
| L35 | **Flow rate is reported, never totalised** | Low | `FLM` is a rate in L/min. Total volume must be integrated downstream, and inherits any rate error for the whole period | 3, and the controller | Integrate at the controller if totalised volume is needed | Accepted by design |
| L36 | **No input filtering or debouncing on the flow sensor** | Low | `pulseIn`-style timing assumes a clean signal. A bouncing or noisy sensor output would over-count | 3 | Fit a suitable sensor or add hardware filtering. A software debounce inside an ISR would cost pulses | Open |

## Grouped reading

If you read only one section, read these.

**Can produce silently wrong data (High)**

* L01 no integrity mechanism · L02 zero ambiguity · L03 no store-and-forward ·
  L04 no node addressing · L05 the Node 1 volume factor · L12 ADC2 versus Wi-Fi
  · L13 unverified 5 V echo input · L15 no brownout or watchdog · L17 credentials ·
  L31 serial chain fragility.

**Degrades accuracy or diagnosability (Medium)**

* L06 no runtime calibration outside pH and EC · L07 linear pH model ·
  L08 turbidity uncompensated · L09 zero sensor offset · L10 Node 1 timeout ·
  L11 DHT11 accuracy · L14 permanent halt on trap · L16 no tests or CI ·
  L18 threshold attribution · L19 flow validity · L20 dead reverse parser ·
  L21 un-cleaned SMTP packet · L22 variant divergence · L23 LCD validity
  display · L25 blocking console · L27 no ultrasonic filtering · L28 no plausibility
  check on Nodes 1 and 2 · L29 DO ADC reference · L32 no version reporting ·
  L33 unvalidated conversions · L34 graceful degradation.

**Cosmetic or low-risk (Low)**

* L24 unused ADC work · L26 debug-channel saturation · L30 counter overflow ·
  L35 rate-only reporting · L36 no flow debounce.

## What this register does not cover

| Not covered | Why |
|---|---|
| Physical installation quality | No schematic, wiring diagram, enclosure specification or photograph exists in the repository |
| Regulatory or standards compliance | None is claimed and none is tested; see [Standards](../references/standards.md)) |
| Security beyond credentials | No authentication, encryption or update security exists in the protocol; the chain is a bare UART and is assumed to be physically enclosed |
| Field deployment status | > **Not verified from the current source.** No node is confirmed to be deployed |
| Long-term component life | No derating, ageing or maintenance-interval data exists in the repository; see [Maintenance](../field-service/maintenance.md) |

## Related

* [Test Strategy](test-strategy.md)) — which of these a test could actually close.
* [Hardware Validation](hardware-validation.md) — procedures that expose many of
  these in the field.
* [Firmware Validation](firmware-validation.md) — the evidence behind every row
  above.
* [Code Reference](../firmware/code-reference.md) — the code each row points at.
* [Standards](../references/standards.md)) — and why none is claimed.
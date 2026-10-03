---
title: Hardware Validation
description: Per-node bring-up validation for CIRQUA, written only in terms of observable firmware behaviour: LCD, debug UART, STATUS console and frames.
---

# Hardware Validation

These procedures validate a node or a cluster using **only what the firmware
shows you**: the LCD, the debug UART, the Node 4 `STATUS` console and the frames
on the inter-node links. Nothing here depends on a schematic, a bench supply
listing or a part number, because none of those exist in the repository.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Observation channels</span>
    <span class="cirqua-identity__value">LCD · debug UART (115200) · Node 4 <code>STATUS</code> · captured UART frames (9600)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Displays in the cluster</span>
    <span class="cirqua-identity__value">Node 1 and Node 4 only</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Silent nodes</span>
    <span class="cirqua-identity__value">Node 2 and Node 3 — validated <strong>indirectly</strong> through the frames they contribute</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Verification status</span>
    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--planned">procedures defined, results not recorded</span></span>
  </div>
</div>

!!! warning "These are procedures, not recorded results"
    No execution record for any node exists in the firmware repository or in this
    documentation set. What follows is what *should* be observed, derived from
    the source at commit `db6d9b8`. A field report that differs from these tables
    is a finding, not a nuisance.

## Before you start

| Preparation | Why |
|---|---|
| Capture the firmware commit each board is running | Nothing on the wire or the display reports it. Record it manually |
| Note each node's physical position in the chain | There is no node address on the wire; identity is physical |
| Have a serial terminal able to capture 115200 8N1 | Node 4's `STATUS` and Node 4's transaction block |
| Have a way to capture one inter-node link at 9600 8N1 | Nodes 2 and 3 have no other output |
| Photograph or note the LCD contents of Nodes 1 and 4 before and after | The only display-based evidence |

## Cluster-level validation

Do this once after all four nodes are flashed. It answers "is the chain alive?"
before you investigate any individual node.

| Step | Action | Observe | Pass criterion |
|---|---|---|---|
| C1 | Power the whole cluster | Node 1 LCD backlight on | Backlight lit |
| C2 | — | Node 1 line 1 shows `C<number>L F<number>L` | `TAV` populated; `F…L` becomes `----` then a number |
| C3 | — | Node 1 line 4 initially shows `STATUS: WAITING` | `WAITING` for the first few seconds is expected |
| C4 | Wait 10 s | Node 1 line 4 changes from `WAITING` | Reaches `NORMAL`, or a documented specific state |
| C5 | — | Node 1 lines 2 and 3 populate | `DO`, `T`, `AT`, `H` values present |
| C6 | Capture the Node 1 ↔ Node 2 link for 30 s | Repeating frames | Node 1's `\|TAV:…\|node1:…;` and Node 2's echo both visible |
| C7 | Capture the Node 2 ↔ Node 3 link | Repeating frames | Consolidated frame with `TAV`, `DO`, `Temp`, `TBV`, `AT`, `AH`, `node2` |
| C8 | Capture the Node 3 ↔ Node 4 link | Repeating frames | Same fields plus `FLM` and `node3` |
| C9 | Capture the Node 4 → controller link | Repeating frames | Upstream fields **minus** `AT:`/`AH:`, plus `pH`, `Turb`, `EC`, `TCV`, `node4:1` |
| C10 | — | Node 4 LCD shows four rows | `EV:`, `TU:`, `EC:`, `ST:`/`AT:`, `AH:` all populated |

!!! warning "C9 is the check that distinguishes a `Node4` from a `Node4_SMTP`"
    A `Node4` sends `EC` in µS/cm with an integer format and a `TCV:` field. A
    `Node4_SMTP` sends `EC` in mS/cm with one decimal, and sends `EV:` and `ST:`
    instead of `TCV:`, and leaves Node 2's `AT:`/`AH:` in the frame. If the
    captured frame does not match the expected variant, the wrong sketch is
    flashed on that node.

## Node 1 — Collection Tank A and cluster head

| Step | Action | Expected observation |
|---|---|---|
| N1-1 | Power the node with no sensors and no link connected | LCD backlight on, four rows rendered |
| N1-2 | — | Line 4 reads `STATUS: WAITING` and stays there (no frame has ever been received) |
| N1-3 | — | Line 1 shows `C0L F----L` — `TAV` zero, `TBV` unavailable |
| N1-4 | — | Lines 2 and 3 show `DO--mg/l T--C` and `AT--C H--%` |
| N1-5 | Connect Node 2's link | Within ≈3 s (`RX_TIMEOUT_MS`) line 4 leaves `WAITING` |
| N1-6 | — | Line 1 `F…L` fills in; lines 2 and 3 populate |
| N1-7 | Disconnect Node 2's link | Line 4 returns to `ERROR` after `RX_TIMEOUT_MS` |
| N1-8 | — | Lines 1–3 retain their last values (there is no blanking on link loss) |
| N1-9 | Cover or unplug the ultrasonic head | `TAV` falls to `0`, and `node1:0` appears in the frame |
| N1-10 | — | Line 4 shows `LOW TAV` when the link is otherwise healthy |
| N1-11 | Fill or drain the tank and compare | `TAV` **changes by roughly half** the geometric change — see below |
| N1-12 | Force a Node 2 sensor failure | `node2:0` in the echo frame, line 4 reads `FAULT` |

### Node 1 status-string expectations

The precedence is strict; the highest-priority condition wins. Verify in this
order, because a lower-priority condition can never be observed while a
higher-priority one is active.

| Order | Condition | Line 4 reads |
|---|---|---|
| 1 | No frame ever received | `STATUS: WAITING` |
| 2 | `millis() − lastRx > 3000` | `STATUS: ERROR` |
| 3 | ambient ≥ 45 °C **and** humidity ≥ 80 % | `STATUS: HOT+HUM` |
| 4 | ambient ≥ 45 °C | `STATUS: OVERTEMP` |
| 5 | humidity ≥ 80 % | `STATUS: HI HUMID` |
| 6 | `TAV < 5000` and `TBV < 500` | `STATUS: LOW C+F` |
| 7 | `TAV < 5000` | `STATUS: LOW TAV` |
| 8 | `TBV < 500` | `STATUS: LOW TBV` |
| 9 | `node2:0` | `STATUS: FAULT` |
| 10 | none of the above | `STATUS: NORMAL` |

!!! danger "N1-11 is the most important check on this page"
    Node 1's reported litres are **doubled** by a hard-coded `2.0f` factor. If a
    known volume change of ΔV produces roughly `2 × ΔV` on the display, the
    factor is present and the reading is not a geometric result. Do not treat
    Node 1's volume as calibrated until that factor has been characterised
    against a physical measurement. See
    [Ultrasonic Level](../sensors/ultrasonic.md#node-1-doubles-the-result-read-this-before-trusting-tav).

### LCD formatting expectations

| Row | Format | Substitution rule |
|---|---|---|
| 1 | `C<TAV>L F<TBV>L` | `----` when `TBV` is not yet available (`volume < 0`) |
| 2 | `DO<value>mg/l T<value>C` | `--` when `DO < 0` or water temperature ≤ −100; decimal point shown as a comma |
| 3 | `AT<value>C H<value>%` | `--` when the value is unavailable or below −100; humidity as an integer |
| 4 | `STATUS: <status>` | always populated |

## Node 2 — Water telemetry and router

Node 2 has **no display and no boot output**, so every check is made through the
frames it produces.

| Step | Action | Expected observation on the wire |
|---|---|---|
| N2-1 | Power the node, capture both links | Echo frame appears on the Node 1 link within 50 ms of boot: `\|DO:…\|Temp:…\|TBV:…\|AT:…\|AH:…\|node2:1;` |
| N2-2 | Capture the Node 2 → Node 3 link | Consolidated frame: `\|TAV:…\|node1:…\|DO:…\|Temp:…\|TBV:…\|AT:…\|AH:…\|node2:…;` |
| N2-3 | — | Both frames repeat at the UART task cadence |
| N2-4 | Disconnect the DS18B20 | `Temp:0.00` and `node2:0` |
| N2-5 | Reconnect the DS18B20 | `Temp` becomes a plausible water temperature, `node2:1` |
| N2-6 | Disconnect the DO probe | `DO:0.00`, `node2:0` |
| N2-7 | Disconnect the ultrasonic head | `TBV:0.00`, `node2:0` |
| N2-8 | Disconnect the DHT11 | `AT:0.00` and `AH:0.00`, `node2:0` |
| N2-9 | — | `node2:0` while **any** of the four is invalid — the flag is an AND, not a per-quantity flag |
| N2-10 | Observe `AT`/`AH` over 5 s | Values change at most once per 2 s — the DHT pacing gate |
| N2-11 | Cut the Node 1 link | `TAV:0.00` and `node1:0` in the downstream frame; Node 2 keeps transmitting |
| N2-12 | Heat or cool the water and watch `DO` | `DO` moves in the direction and rough proportion the −0.02/°C coefficient predicts |

!!! warning "N2-12 confirms compensation, not accuracy"
    The compensation factor is `1 + (T − 25) × (−0.02)`, so at 15 °C it is 1.2 and
    at 35 °C it is 0.8. A changing `DO` with a changing `Temp` shows the
    compensation is live. It says nothing about whether the absolute value is
    right — that needs comparison against a calibrated reference, which the
    firmware has no facility for. See
    [Dissolved Oxygen](../sensors/dissolved-oxygen.md)).

## Node 3 — Flow metering and forwarding

| Step | Action | Expected observation |
|---|---|---|
| N3-1 | Power the node | No serial output at all, by design |
| N3-2 | Capture the Node 3 → Node 4 link | Forwarded frame includes `\|FLM:<value>\|node3:1;` |
| N3-3 | Move water through the flow sensor | `FLM` changes; `node3:` stays `1` |
| N3-4 | — | With no flow, `FLM` reads `0.00` and `node3:` **still** reads `1` — the flow task marks every sample valid |
| N3-5 | Disconnect the flow sensor | Identical to N3-4: `FLM:0.00`, `node3:1`. A disconnected flow sensor is indistinguishable from no flow |
| N3-6 | Count pulses for exactly 60 s and compute | Reported rate ≈ `pulses / 5.5` L/min; confirms `FLOW_CAL_FACTOR` |
| N3-7 | Cut the Node 2 link | **One** fallback frame: `\|TAV:0.00\|node1:0\|DO:0.00\|node2:0\|FLM:…\|node3:…;` |
| N3-8 | Leave the link cut for 2 min | No further fallback frames — the alert is muted after the first |
| N3-9 | Restore the link | Forwarding resumes immediately, and no extra fallback is emitted |

!!! warning "N3-4 and N3-5 together are a real limitation"
    Node 3's health flag reports the *task*, not the *sensor*. There is no way,
    from the wire, to tell a working idle sensor from a disconnected one. If
    flow is a monitored quantity in your installation, that gap has to be covered
    outside the firmware. See
    [Known Limitations](known-limitations.md).

## Node 4 — Effluent analytics

Node 4 has both a display and a debug UART, so it offers the richest observation
set in the cluster.

| Step | Action | Expected observation |
|---|---|---|
| N4-1 | Power the node, open 115200 8N1 | Calibration banner, three `[ADC]` lines, DS18B20 count, `[DHT11] Initialized` |
| N4-2 | Compare the banner values | Defaults `3.500 / -1.750 / 9.997` on a fresh board; other values mean saved NVS |
| N4-3 | — | `[DS18B20] Devices found: 1` with the probe connected |
| N4-4 | Connect the upstream link | `[NODE 4 PACKET TRANSACTION]` blocks appear |
| N4-5 | Compare `[INCOMING]` and `[CLEANED]` | The cleaned line lacks `AT:` and `AH:`; every other field is identical and in the same order |
| N4-6 | Compare `[OUTGOING]` with `[CLEANED]` | Adds `pH:`, `Turb:`, `EC:`, `TCV:`, `node4:1;` |
| N4-7 | — | Node 4 LCD shows `EV:`, `TU:`, `EC:`, `ST:`/`AT:`, `AH:` with plausible values |
| N4-8 | Disconnect the DS18B20, reboot | `[DS18B20] Devices found: 0` plus the explicit warning line |
| N4-9 | — | `[LOCAL SENSORS]` reports the submerged temperature as invalid, and pH/EC switch to 25 °C compensation while still reporting `Valid: YES` |
| N4-10 | Send `STATUS` + newline | Raw ADC counts and volts for pH, EC and turbidity, plus saved constants |
| N4-11 | Send `HELP` + newline | The six-line command list |
| N4-12 | Send `SET:EC_K=0` | `[ERROR] Invalid value for EC K-Factor.` |
| N4-13 | Send `SET:EC_K=-1` | Same error |
| N4-14 | Send `SET:EC_K=8.412` | `[SUCCESS] EC K-Factor updated and saved to flash: 8.412` |
| N4-15 | Power-cycle | `STATUS` still reports `K: 8.412` — the value persisted |
| N4-16 | Send `SET:PH_S=3.480`, `SET:PH_O=-1.610` | Two `[SUCCESS]` lines; `STATUS` reflects both |
| N4-17 | Send `RESET` | Banner reprints with `3.500 / -1.750 / 9.997`, then `[SUCCESS] Calibration reset to defaults.` |
| N4-18 | Send `set:ec_k=8.412` (lowercase) | **No response.** The `SET:` keyword is matched case-sensitively |
| N4-19 | Short the EC probe, send `STATUS` | Raw count near the rail; `EC` becomes invalid in the next transaction block |
| N4-20 | — | Turbidity at either end of its range still reports `Valid: YES` — saturation is treated as valid |

### Node 4 LCD expectations

| Row | `Node4` format | `Node4_SMTP` format |
|---|---|---|
| 0 | `EV:<int>L pH:<1 dp>` | same |
| 1 | `TU:<int> EC:<int>uS` | `TU:<int> EC:<1 dp>mS` |
| 2 | `ST:<1 dp>C AT:<1 dp>C` | same |
| 3 | `AH:<0 dp>%` | same |

Note that Node 4's LCD prints the **stored** values with no invalid-value
substitution and no status line, so an invalid reading appears as a plausible
number. The validity information is on the debug UART, in `[LOCAL SENSORS]`.

## Node 4 SMTP variant

| Step | Action | Expected observation |
|---|---|---|
| NS-1 | Power the node with no network in range | `Connecting to Wi-Fi: <ssid>` then 30 dots, then `[ERROR] Wi-Fi Connection Failed!` |
| NS-2 | — | The node continues normally afterwards; telemetry is unaffected |
| NS-3 | Power within range of the configured AP | `[INFO] Wi-Fi Connected!`, then `[INFO] Synchronizing NTP time for Tunis...` |
| NS-4 | — | `[INFO] Current Epoch Time: <value>` with a value above `1700000000` |
| NS-5 | With valid credentials | One startup e-mail per boot; `[SMTP SUCCESS] Email sent successfully!` |
| NS-6 | With invalid credentials | `[SMTP ERROR] Connect failed: <library reason>` |
| NS-7 | Connect the upstream link | Frames appear on the Node 4 → controller link |
| NS-8 | Compare against the `Node4` expectations | **Different field set:** `EC` with one decimal in mS/cm, `EV:` instead of `TCV:`, `ST:` present, and Node 2's `AT:`/`AH:` **not** removed |
| NS-9 | Send `HELP` | No response — this variant has no calibration console |
| NS-10 | — | No `[ADC]`, `[DS18B20]` or `[DHT11]` boot lines — those prints exist only in `Node4` |

## Regression checks to run after any firmware change

| Check | Why |
|---|---|
| Snippet staleness, then `mkdocs build --strict` | The documentation pin moved with the code |
| This page's cluster-level section C1–C10 | Catches a broken chain immediately |
| The node's own status/precedence table | Status strings are the primary field-visible behaviour |
| `STATUS` before and after any calibration change | Confirms what actually persisted |

## Recording results

| Field | Content |
|---|---|
| Date and operator | |
| Firmware commit on each node | Recorded manually — nothing reports it |
| Board identity for each node | QR code and physical position |
| Link wiring as found | Which GPIO goes to which neighbour's GPIO |
| Observations against each table above | Including anything that did **not** match |
| Calibration values found in NVS | From the Node 4 `STATUS` output |
| Anything that could not be verified | Record it as unverified rather than inferring it |

## Related

* [Startup Checklist](../field-service/startup-checklist.md)) — the shorter,
  field-facing version.
* [Troubleshooting](../field-service/troubleshooting.md)) — what to do when an
  observation here fails.
* [Node 1](../nodes/node1.md)), [Node 2](../nodes/node2.md)),
  [Node 3](../nodes/node3.md)), [Node 4](../nodes/node4.md)),
  [Node 4 SMTP](../nodes/node4-smtp.md)) — per-node detail.
* [Message Format](../communication/message-format.md)) — the frames referenced
  throughout.
* [Known Limitations](known-limitations.md) — the failures these procedures
  cannot detect.
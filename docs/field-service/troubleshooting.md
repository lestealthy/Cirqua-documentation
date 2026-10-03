---

title: Troubleshooting

description: Symptom-to-cause tables for the CIRQUA nodes, serial console diagnostics, UART link faults and the evidence needed to escalate.

---

# Troubleshooting

This page is organised by what you can **observe**, not by what you think has failed. It

covers the real behaviours of the audited firmware, including several that look like

faults but are not.

Claim types used throughout: **Firmware implementation**, **Engineering

interpretation**, **Recommendation**.

!!! warning

    Isolate the power before opening any enclosure. There is no published schematic —

    see the safety admonition on the [Field service index](index.md#safety-first).

## The chain fails as a unit

**Firmware implementation.** Node 1 originates the upstream frame and sends it every

500 ms; each intermediate node appends its own fields and forwards; Node 4 terminates and

forwards to the controller.

**Engineering interpretation.** A break anywhere removes data from everything downstream.

Symptom patterns therefore localise the break:

| Where you see the fault | Likely break |

|---|---|

| Node 1 shows `ERROR` | Link 1↔2, or Node 2 is not running |

| Node 1 is fine but `DO`, `T`, `AT`, `H` never populate | Node 2 not running, or Node 2 is running but its sensors are all invalid (`node2:0`) |

| Node 4's `EV`, `TU`, `EC`, `pH` are fine but the controller sees nothing | Link 4↔controller |

| Controller frame contains `FLM:` but a stale pH/Turb/EC | Node 4 sensor task stalled |

Work from the **far end backwards** — controller first, then Node 4, then Node 3, then

Node 2. The node nearest the break still looks healthy.

## Node 1 status word

**Firmware implementation.** The fourth LCD row is a complete status machine. The

precedence below is exact and first-match-wins, so a low-volume condition can mask a

health flag.

```cpp

--8<-- "assets/snippets/node1-lcd-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>Task_LCD_Node1</code> ·

lines 220–310 · commit <code>db6d9b8</code>
</div>

| Status shown | Exact firmware condition | What it means | What to do |

|---|---|---|---|

| `STATUS: WAITING` | `g_lastNode2Rx == 0` — **no frame has ever been received** | Node 1 has never seen Node 2. Normal for the first second or two after boot | If it persists past a few seconds, the link or Node 2 is down. See [No data on the link](#no-data-on-the-link) |

| `STATUS: ERROR` | `millis() - lastRx > 3000` ms | A frame **was** received once, then the link went quiet for over 3 s | Link, wiring, or Node 2 has stopped. See [No data on the link](#no-data-on-the-link) |

| `STATUS: HOT+HUM` | Ambient `>= 45 °C` **and** humidity `>= 80 %` | Enclosure overheat plus condensation risk. Both must be true | Ventilation and enclosure sealing. **Not** a sensor-fault indication |

| `STATUS: OVERTEMP` | Ambient `>= 45 °C` (and not both) | Ambient temperature at or above the threshold | Same |

| `STATUS: HI HUMID` | Humidity `>= 80 %` (and not both) | Condensation threshold reached | Same |

| `STATUS: LOW C+F` | `TAV < 5000` **and** `TBV < 500` | Both tanks low | Refill. **Remember the Node 1 ×2 factor** — see the note below |

| `STATUS: LOW TAV` | `TAV < 5000` only | Collection Tank A low | Refill |

| `STATUS: LOW TBV` | `TBV < 500` only | Feeding Tank B low | Refill |

| `STATUS: FAULT` | Node 2's frame carried `node2:0` | **Node 2 reports that at least one of its local sensor validity flags is false** | Go to Node 2. This is Node 2 telling you about its own sensors, not Node 2 being dead |

| `STATUS: NORMAL` | All of the above false | — | — |

!!! warning

    **`FAULT` is the least specific message.** It means "Node 2 sent something with at

    least one invalid flag". Node 2 does not say *which* sensor. Node 2 has no display and

    no console, so you must go and inspect the water side: the dissolved-oxygen probe,

    the DS18B20, the DHT11 and the ultrasonic sensor on the Feeding Tank B.

!!! warning

    **`LOW TAV` fires at a real volume of about 2500 L, not 5000 L.** Node 1 doubles its

    computed volume before comparison, and the doubled figure is what the threshold is

    compared against. This is a real consequence of the empirical ×2 factor documented in

    [Ultrasonic calibration](../calibration/ultrasonic.md#the-node-1-2-factor-an-empirical-fudge-with-no-geometric-justification).

!!! note

    `LOW C+F` and `LOW TAV` are only evaluated when the corresponding measurement is

    valid: `lowTav` requires `localSnap.isValid`, and `lowTbv` requires a received volume

    `>= 0`. If the Node 1 ultrasonic is failing, `TAV` reads `0` and the low-volume

    alarms still fire — which masks the real fault behind `LOW TAV`.

## Node 1 placeholder fields

**Firmware implementation.** `Task_LCD_Node1` substitutes fixed strings when a field is

missing or invalid. The placeholders are the only "invalid" indication Node 1 gives.

| Display | Field | Placeholder shown when |

|---|---|---|

| `C<TAV>L F<TBV>L` | `TBV` | `----` — Node 2's frame carried no usable volume |

| `DO<mg/l> T<Temp>C` | `DO`, `Temp` | `--` — field absent or below the sentinel threshold |

| `AT<AT>C H<AH>%` | `AT`, `AH` | `--` — ambient temperature `<= -100`, humidity `< 0` |

**Engineering interpretation.**

- A persistent `----` in the `F` field with everything else populated means Node 2 is

  alive and reporting, but its ultrasonic is failing. **Node 2 does not set `node2:0`

  for this** — it publishes the frame with an invalid volume — so the status word may

  still read `NORMAL` while the tank level is missing entirely. Do not rely on the status

  word alone.

- A `--` for `DO` or `Temp` means the dissolved-oxygen raw ADC was exactly `0`, or the

  DS18B20 failed its validity check.

- Note the sentinel asymmetry: `Temp` is suppressed below `-100`, while `DO` and `AH` are

  suppressed at `>= 0` failing. A legitimately negative humidity reading would still be

  displayed.

## Node 1 `C…L` volume is `0` or implausible

| Observation | Firmware cause | Check |

|---|---|---|

| `C0L` and `STATUS: WAITING` or `ERROR` | No frame from Node 2 yet | Link first; the level is local and independent |

| `C0L` on an empty tank | Ultrasonic returning a distance `>= 260 cm`, so height clamps to 0 | Sensor mounting, condensation inside the housing, cable |

| `C0L` with the ultrasonic removed | `pulseIn` returned 0 → `isValid = false`, stored value reset to 0 | Wiring on GPIO 2 / 17 |

| Reading roughly **double** the true volume | The hard-coded `2.0f` factor | Expected behaviour — see [Ultrasonic calibration](../calibration/ultrasonic.md) |

| Reading offset by a roughly constant number of litres | Sensor mounted below the tank rim; no offset compensation exists | Re-verify geometry |

| Reading drifts slowly and never settles | No filtering, averaging or hysteresis on the level value in the firmware | Not fixable by calibration; clean the transducer face |

!!! note

    `isValid` being false does **not** clear the level — the task writes a zeroed

    `LocalSensorData` on each failed cycle, so the displayed volume drops to `0` rather

    than freezing at the last good value. A `0` is therefore ambiguous between "empty" and

    "no echo".

## Dissolved oxygen unavailable

| Symptom | Firmware behaviour |

|---|---|

| `DO--` on the Node 1 LCD | `rawDO == 0` on GPIO 34 — the analogue channel is reading hard zero, i.e. the module is unpowered, disconnected, or its output is at 0 V |

| `DO` present but absurdly high | Remember the `VREF` of 5000 mV is applied to a 3.3 V ADC; see [Dissolved oxygen calibration](../calibration/dissolved-oxygen.md#the-vref-question-read-this-carefully) |

| `DO` value changes with water temperature while the water chemistry is constant | Expected: the −0.02/°C compensation term |

## Flow value missing or stuck

**Firmware implementation.** Node 3 always sets `isValid = true`:

```cpp

--8<-- "assets/snippets/node3-flow-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>Task_Flow</code> ·

lines 43–69 · commit <code>db6d9b8</code>
</div>

**Engineering interpretation.** Because `isValid` is unconditional:

- **`FLM:0` is never a fault indication.** It means zero pulses were counted in that

  1000 ms window. That is indistinguishable from a failed sensor at the telemetry layer.

- **No pulse-count overflow detection exists.** `g_pulseCount` is a free-running

  `volatile uint32_t` reset each second; the firmware does not check for wrap.

- The 50 % duty assumption of a typical hall-effect flow sensor means fewer than one

  pulse per second is indistinguishable from no flow by this firmware alone. Verify by

  observing flow physically.

- The ISR triggers on **FALLING** with `INPUT_PULLUP`. A hall sensor wired active-low is

  required.

## Node 4 display reads zero

**Firmware implementation.** Node 4's LCD task prints the stored numeric fields

**unconditionally**. It does not test the validity flags.

```cpp

--8<-- "assets/snippets/node4-lcd-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_LCD_Node4</code> ·

lines 1187–1259 · commit <code>db6d9b8</code>
</div>

**Engineering interpretation.** On Node 4 the display is *not* a validity indicator.

`EC:0`, `TU:0` or `pH:0.0` may mean a valid measurement **or** an invalid channel. This

is the opposite of Node 1, which does substitute placeholders.

| Display | Valid only if | If not valid |

|---|---|---|

| `EC:<v>uS` | `0.0 <= V <= 3.30` | Value stays at its previous value; `node4:0` is set in the downstream frame |

| `TU:<n>` | `0.0 <= V <= 3.30` | As above. Note that `TU:0` is also the correct output when `V >= 3.20` — a genuinely clear sample also reads `0` |

| `pH:<v>` | `0.02 <= V <= 3.30` **and** `0.0 <= pH <= 14.0` | As above |

| `EV:<n>L` | Echo returned and `distance <= TANK_HEIGHT + 20` | `tcValid` false; the stored value is not updated |

**Recommendation.** Never conclude a Node 4 channel is healthy from the LCD. Use the

`node4:` health flag in the downstream frame, and `STATUS` on the serial console.

**Important:** the Node 4 LCD **does** distinguish variants. Row 1 ends `EC:<n>uS` on

`Node4` and `EC:<v>mS` on `Node4_SMTP`. If your unit says `uS` where you expect `mS`,

either the wrong firmware is flashed or the LCD expectation is wrong.

## pH out of range

| Observation | Firmware behaviour | Interpretation |

|---|---|---|

| pH never displayed as invalid — instead reads `0.0` or `14.0` | The task stores the value only when both gates pass; on failure the flag is cleared and the stored number is left as-is | A persistent `0.0` is the zero-initialised value, i.e. the channel has never been valid |

| pH reads a plausible value at 25 °C but drifts badly colder or hotter | The compensation divides by `1 + 0.02*(T-25)` | Expected — see [pH calibration](../calibration/ph.md#honest-limitations-of-this-model) |

| pH changed drastically after a `SET:` command | `SET:PH_S=` and `SET:PH_O=` have **no validation at all** | A typo was accepted and persisted. `RESET` restores the variant defaults |

| pH reads differently before and after a firmware variant change | `Node4` defaults `phOffset` to `-1.75f`; `Node4_SMTP` defaults it to `0.0f`, but **both read the same NVS key** | Flashing a variant does not reset calibration. See [pH calibration](../calibration/ph.md#the-default-divergence-is-real-and-must-not-be-smoothed-over) |

## Serial console diagnostics

**Firmware implementation.** Node 4 only, 115200 baud, newline-terminated commands.

`HELP`, `STATUS` and `RESET` are case-insensitive; `SET:` prefixes are case-sensitive.

| Command | Use |

|---|---|

| `HELP` | Confirm the console is alive and that this is a `Node4` build |

| `STATUS` | The primary diagnostic — see below |

| `RESET` | **Destructive to calibration.** Clears `node4_cal` |

`STATUS` output format:

```text

--- Live Raw Sensor Diagnostics ---

pH   -> Raw ADC: 1462 | Voltage: 1.176V

EC   -> Raw ADC:  803 | Voltage: 0.647V | K: 9.997

Turb -> Raw ADC:  312 | Voltage: 0.251V

Saved Constants -> pH Slope: 3.500 | pH Offset: -1.750 | EC K: 9.997

```

### Reading raw ADC counts

`readSensorVoltage()` averages 16 `analogReadMilliVolts()` samples per channel per cycle

after discarding one post-channel-switch sample. Raw counts come from `readADCFiltered()`.

Practical guidance:

| Raw count | Approximate voltage | Reading |

|---|---|---|

| `0` | 0 V | Channel dead, disconnected or unpowered |

| `~10` | < 0.01 V | Below the pH validity gate (`0.02 V`) |

| `~40` | ~0.03 V | Near the bottom of the valid window |

| `~1367` | ~1.1 V | Middle of the pH window |

| `~4095` | ~3.3 V | **Above every validity gate** (`3.30 V`) — channel saturated or shorted |

**Engineering interpretation.** The validity gates are all expressed in volts around a

3.3 V full scale, so any channel reading near 3.3 V is rejected by pH, EC *and* turbidity

simultaneously. A single saturated channel produces "invalid" on that channel only; all

three at once points at the supply or the ADC configuration, not at three sensors.

**Recommendation.** Take `STATUS` readings **before** changing any calibration constant.

It distinguishes an electrical fault (raw counts at the rails) from a calibration error

(raw counts plausible but the computed value wrong). Changing a K-factor to compensate

for a disconnected sensor destroys a previously good calibration.

### A useful asymmetry

| Observation | Most likely cause |

|---|---|

| All three channels read 0 V | Common supply or common ground fault |

| One channel reads 0 V, others normal | That module's wiring, or the module itself |

| One channel near 3.3 V, others normal | That module saturated, shorted, or its VCC to the wrong rail |

| `EC -> ... K:` shows a value you do not expect | NVS holds a value from a previous calibration or a previous firmware variant |

| Console silent, LCD updating normally | USB/serial connection or baud rate — the sensor tasks do not depend on `Serial` |

## No data on the link

**Firmware implementation.** Every link runs at `INTERNODE_BAUD 9600`, `SERIAL_8N1`. Node 1

has one link; Nodes 2, 3 and 4 each have two (`UART1` upstream, `UART2` downstream). There

is **no checksum, no CRC, no sequence number, no acknowledgement and no retry**;

validation is structural only.

### The five things to check, in order

1. **TX/RX crossover.** This is the most common wiring fault. Each link needs

   **TX → RX and RX → TX**, never TX → TX.

2. **Common ground.** Every node on a link must share a ground reference with its

   neighbours. Without it, UART levels are undefined and the symptom is intermittent or

   complete silence.

3. **Baud mismatch.** Both ends must be 9600 8N1. A node running a re-flashed build with

   a different baud will be silently unintelligible.

4. **Swapped GPIO pairing.** Using **25/26** where the link expects **32/33** is a

   realistic field error, because Nodes 2, 3 and 4 all use 25/26 for the upstream link

   and 32/33 for the downstream link. Wiring both links to the same pair makes the node

   listen to itself and talk to nothing. Verify against the GPIO table for the *specific*

   node you are holding — numbers do not carry across nodes.

5. **Cable.** Open, shorted, or a data cable that is actually a charge-only cable.

### UART pin assignments

| Node | Upstream (RX / TX) | Downstream (RX / TX) |

|---|---|---|

| Node 1 | — | 32 / 33 (Node 2) |

| Node 2 | 25 / 26 (Node 1) | 32 / 33 (Node 3) |

| Node 3 | 25 / 26 (Node 2) | 32 / 33 (Node 4) |

| Node 4, SMTP | 25 / 26 (Node 3) | 32 / 33 (controller) |

**Recommendation.** Prove a link with a terminal at 9600 baud on the *downstream* node's

upstream RX before suspecting the firmware. A healthy link produces a frame roughly every

500 ms.

### Frames to expect on each link

| Link | Frame shape |

|---|---|

| Node 1 → Node 2 | `|TAV:<int>|node1:<0 or 1>;` every 500 ms |

| Node 2 → Node 1 | `|DO:<f>|Temp:<f>|TBV:<f>|AT:<f>|AH:<f>|node2:<0 or 1>;` |

| Node 2 → Node 3 | Upstream frame plus Node 2's own fields |

| Node 3 → Node 4 | Upstream frame plus `|FLM:<f>|node3:<0 or 1>;` |

| Node 3 → Node 4 on silence | `|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:<f>|node3:<0 or 1>;` — **emitted once, then muted** |

| Node 4 → controller (`Node4`) | Cleaned upstream plus `|pH:<f>|Turb:<i>|EC:<i>|TCV:<i>|node4:1;` |

| Node 4 → controller (`Node4_SMTP`) | Cleaned upstream plus `|pH:<f>|Turb:<i>|EC:<f>|EV:<i>|ST:<f>|node4:1;` |

!!! warning

    **`TAV:0.00` on the Node 3 fallback frame is not a real tank level.** It is the

    timeout substitute emitted when Node 3 stops hearing from Node 2, and it is sent **once**

    and then muted. If you see it once and then no frames at all, Node 3 has gone quiet

    rather than recovering.

**Engineering interpretation.** The health flag is a single bit per node meaning "all of

my local sensor validity flags are true". It cannot tell you *which* sensor failed, and

`node1:0` appears on the Node 3 fallback even when Node 1 is perfectly healthy.

### Buffer overflow

**Firmware implementation.** Node 1 uses a 256-byte `String` and resets at 250; Node 2

uses `char[128]` per link; Node 3 `char[256]`; Node 4 `char[384]` with a 512-byte

assembled packet. On overflow the receiver **resets its index and drops the frame**.

**Engineering interpretation.** A dropped frame is silent — there is no error indication

anywhere. With correct baud rates the frames are far below these limits, so overflow

implies a baud mismatch, noise, or a stuck/framing error.

## Node 4 SMTP specific symptoms

| Symptom | Firmware behaviour |

|---|---|

| No e-mail at all | `initNetworkAndTime()` retries Wi-Fi 30 × 500 ms, then NTP 15 retries. On failure it logs an error and **carries on** — the node still runs |

| `EC` value 1000× smaller than expected | You are looking at the SMTP variant, which reports **mS/cm**, not µS/cm |

| `EC` value does not change with water temperature | Expected on the SMTP variant — it has **no temperature compensation** |

| pH value differs from a `Node4` at the same temperature | The SMTP variant applies **no pH temperature compensation** |

| Repeated pH/EC/Turbidity values identical to three decimals | Expected: it uses raw `analogRead()` against a fixed 3.3 V, not `analogReadMilliVolts()` |

| Nothing printed on serial | `Node4_SMTP` has **no calibration console** — `HELP` and `STATUS` do not exist in that build |

!!! danger

    The committed SMTP build contains **placeholder credentials**. They are not working

    values and must never be published or reused. See

    [Node 4 SMTP](../nodes/node4-smtp.md).

## Nothing works at all

| Symptom | Check |

|---|---|

| Blank LCD on Node 1 or Node 4, no serial output | `[FATAL ERROR]` on 115200 baud — task or mutex creation failed, and the node is halted |

| LCD lit but completely static, serial silent | Same: the fatal trap idles in `vTaskDelay`, so it prints once and stops |

| LCD lit, serial silent, values frozen | Task stalled, or `setup()` did not complete |

| All nodes dead at once | Common supply. The chain shares no power regulation as far as the source shows, but a single upstream supply fault explains this |

## Escalation

Before escalating, capture the following. Without these, an escalation cannot be acted on.

**Recommendation.**

- [ ] **Photographs** — of the enclosure interior with wiring visible, of every cable

      termination, of each sensor at its mounting point, and of any QR or identity label.

- [ ] **Serial log at 115200 baud**, from power-on, captured as text. Include the complete

      boot output and any `[FATAL ERROR]` line.

- [ ] **`STATUS` output** on Node 4, captured verbatim, for all three channels. Note the

      time and the water temperature.

- [ ] **`HELP` output**, confirming the console and therefore the firmware variant.

- [ ] **Node 1 LCD photographs** of all four rows at the time of the fault. The status

      word is the fastest triage signal.

- [ ] **Node 4 LCD photographs** of all four rows, noting whether the EC suffix reads

      `uS` or `mS`.

- [ ] **Frame captures** at 9600 baud on each link, showing what is actually on the wire —

      or silence.

- [ ] **Measured supply voltage** at the 3.3 V rail at the ESP32, and at the sensor

      modules, taken while the node is running. Note the time of measurement.

- [ ] **The exact node and firmware variant** — and if it is Node 4, the pH slope, pH

      offset and EC K-factor from `STATUS`.

- [ ] **Commit `db6d9b8`.** State that the firmware in question is build

      `db6d9b896341a9c7d8fd01913e854b663c110d55` from

      `lestealthy/Cirqua`, branch `main`, or state the actual commit if it differs. A

      report against the wrong build cannot be reproduced.

- [ ] **What you have already ruled out**, so the escalation does not repeat your work.

Do **not** include Wi-Fi credentials, SMTP passwords, tokens or any other secret in an

escalation.

### What an escalation cannot resolve from the repository

Be explicit about these in the report so expectations are clear:

- No schematics, circuit diagrams, wiring records or hardware photographs exist.

- No part numbers are published for the DO, flow, pH or EC modules — only HC-SR04,

  DS18B20 and DHT11 are named in the source.

- No maintenance schedule or calibration interval is documented.

- No hardware validation record exists.

## Related pages

- [Field service index](index.md)

- [Startup checklist](startup-checklist.md)

- [Sensor replacement](sensor-replacement.md)

- [Node 1](../nodes/node1.md) · [Node 2](../nodes/node2.md) ·

  [Node 3](../nodes/node3.md) · [Node 4](../nodes/node4.md) ·

  [Node 4 SMTP](../nodes/node4-smtp.md)

- [Communication: fault handling](../communication/fault-handling.md)

- [Validation: known limitations](../validation/known-limitations.md)
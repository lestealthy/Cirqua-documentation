---

title: Node 4 SMTP (Analytics Tail with E-mail Reporting)

description: Field-service manual for CIRQUA Node 4 SMTP — same water-quality sensors as Node 4 plus Wi-Fi, NTP and fault e-mail reporting.

---

# Node 4 SMTP (Analytics Tail with E-mail Reporting)

## Identity card

--8<-- "assets/generated/node-cards/node4-smtp.html"


<div class="cirqua-photo-slot">
  <span class="cirqua-photo-slot__label">Photo required</span>
  <p class="cirqua-photo-slot__title">Node 4 (SMTP) — analytics with e-mail reporting — no photograph on record</p>
  <p class="cirqua-photo-slot__note">
    Photograph the node, the probe positions, and any antenna fitted for the Wi-Fi variant.
    No photograph of CIRQUA hardware was found in the firmware repository or
    the local workspace, so this slot is intentionally empty. A stock or
    generated image is not used, because that would misrepresent the hardware.
  </p>
</div>

## Responsibilities

The SMTP variant does everything `Node4` does for measurement and forwarding, and

adds network reporting:

1. **Measures** pH, turbidity, EC, submerged temperature, ambient temperature and

   humidity, and effluent tank volume at 1 Hz — using the same sensors on the

   same GPIO map.

2. **Forwards** the upstream frame to the downstream controller with its own

   fields appended. The field **names and units differ** from `Node4`; see the

   variant-differences admonition below.

3. **Associates with Wi-Fi** at boot and synchronises NTP time (Tunis, UTC+1).

4. **Sends e-mail**:

   * a **startup / reset notice** on every boot;

   * a **heartbeat** every 86400 s (24 h) while healthy;

   * a **fault alert** whenever any sensor is invalid, ambient temperature exceeds

     45 °C or ambient humidity exceeds 90 %, rate-limited by a 43200 s (12 h)

     cooldown.

5. **Renders the local 16×4 I²C LCD** at 500 ms.

Node 4 SMTP does **not** provide the serial calibration console, so its

calibration constants can only be changed by editing and reflashing.

## Inputs

| Input | Device | Signal | Notes |

|---|---|---|---|

| pH | [Analogue pH probe](../sensors/ph.md) | ADC2, GPIO 13 | Linear slope/offset model |

| Turbidity | [SEN0189 / DFRobot analogue](../sensors/turbidity.md) | ADC2, GPIO 14 | Quadratic, 5 V-rescaled in this variant |

| Electrical conductivity | [Analogue EC probe](../sensors/conductivity.md) | ADC2, GPIO 12 | **No temperature compensation** in this variant |

| Submerged water temperature | [DS18B20](../sensors/temperature.md) | 1-Wire, GPIO 27 | 10-bit |

| Ambient temperature / humidity | [DHT11](../sensors/humidity.md) | GPIO 5 | `!isnan()` gating only |

| Effluent tank level (EV) | [HC-SR04 ultrasonic](../sensors/ultrasonic.md) | TRIG GPIO 4, ECHO GPIO 2 | 20 ms timeout |

| Upstream frame | [UART](../communication/serial-links.md) | GPIO 25 RX (UART1) | From Node 3 |

| Downstream link | [UART](../communication/serial-links.md) | GPIO 32 RX / 33 TX (UART2) | GPIO 33 TX to the controller |

| Wi-Fi | — | ESP32 radio | Association attempted at boot |

| NTP | — | ESP32 radio | `pool.ntp.org`, `time.nist.gov` |

## Outputs

| Output | Field | Format | Notes |

|---|---|---|---|

| Downstream to controller | entire upstream frame | verbatim | **Not cleaned** — see below |

| Downstream to controller | `pH` | `%.1f` | 0.0 when invalid |

| Downstream to controller | `Turb` | `%d` | integer NTU, 0 when invalid |

| Downstream to controller | `EC` | `%.1f` | **mS/cm** in this variant |

| Downstream to controller | `EV` | `%d` | integer litres (the `Node4` name is `TCV`) |

| Downstream to controller | `ST` | `%.1f` | submerged temperature (absent in `Node4`) |

| Downstream to controller | `node4` | hard-coded `1` | Always 1 |

| E-mail | startup / reset | subject `[WattLab Node 4] SYSTEM RESET / STARTUP` | Sent from `Task_Email_And_UART_Node4` before the main loop |

| E-mail | heartbeat | subject `[WattLab Node 4] Daily Heartbeat OK` | Every 86400 s, only if the send succeeded |

| E-mail | fault | subject `[WattLab Node 4] FAULT ALERT` | Itemised per-sensor HTML `<ul>`; 43200 s cooldown |

| E-mail sender | name `WattLab Node 4` | recipient `Operator` | HTML body, base64 transfer encoding, SSL transport, high priority |

| Local display | 16×4 I²C LCD, address `0x27` | — | Refreshed every 500 ms |

| Debug UART | `Serial`, 115200 baud | text | Wi-Fi and SMTP status lines only |

Downstream frame structure:

```text

<upstream verbatim>|pH:%.1f|Turb:%d|EC:%.1f|EV:%d|ST:%.1f|node4:1;

```

!!! important "The upstream frame is NOT cleaned in this variant"

    `Node4` runs `cleanUpstreamPacket()` to strip `AT:` and `AH:` so the

    controller receives one ambient pair. `Node4_SMTP` **does not call that

    function** — it forwards the upstream tokens unchanged. A controller attached

    to a Node 4 SMTP board therefore still receives Node 2's `AT`/`AH` fields,

    and this variant never appends its own ambient pair under those names. Do

    not port a `Node4` parser assumption about a single ambient pair onto this

    firmware without checking.

## Controller

| Property | Value |

|---|---|

| MCU | ESP32 |

| Framework | Arduino ESP32 (`.ino` sketch) |

| RTOS | FreeRTOS, `xTaskCreatePinnedToCore` |

| Debug UART | `Serial.begin(115200)` |

| Libraries | `WiFi.h`, `ESP_Mail_Client.h`, `Preferences.h` |

| NVS namespaces | `node4_cal` (calibration), `email_state` (e-mail epochs) |

| Board variant | > **Not verified from the current source.** |

!!! warning "Wi-Fi and ADC2 conflict — unresolved in the committed source"

    All three analogue sensor inputs (GPIO 12, 13, 14) are on **ADC2**. On the

    ESP32 the Wi-Fi driver uses ADC2 for its own internal measurements, and

    those channels are **not usable while Wi-Fi is active**. This variant runs

    `WiFi.begin()` at boot and keeps the radio associated while reading those

    three channels every second.

    **Engineering interpretation:** the pH, turbidity and EC readings on this

    variant should be treated as suspect whenever Wi-Fi is associated. This is a

    real limitation of the committed source; it is not a wiring fault and it

    cannot be diagnosed from the LCD alone. Verify the three analogue readings

    against the debug output before trusting them.

## GPIO Map

Identical pin map to `Node4`:

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| Effluent ultrasonic | TRIG | 4 | out | 2 µs low, 10 µs high |

| Effluent ultrasonic | ECHO | 2 | in | `pulseIn(..., HIGH, 20000)` — **20 ms timeout here**, 25 ms in `Node4` |

| pH probe | analogue out | 13 | in (ADC2) | Conflicted by Wi-Fi — see above |

| Turbidity probe | analogue out | 14 | in (ADC2) | Conflicted by Wi-Fi |

| EC probe | analogue out | 12 | in (ADC2) | Conflicted by Wi-Fi |

| Submerged DS18B20 | 1-Wire data | 27 | 1-Wire | 10-bit resolution |

| DHT11 | data | 5 | in | `DHTTYPE DHT11` |

| UART1 | RX (from N3) | 25 | in | 9600 8N1 |

| UART1 | TX | 26 | out | Declared |

| UART2 | RX (from controller) | 32 | in | Commented `// To Controller (Mega)` |

| UART2 | TX (to controller) | 33 | out | Cluster packet to the Mega |

| LCD (I²C) | SDA | 21 | — | `Wire.begin(21, 22)` |

| LCD (I²C) | SCL | 22 | — | `LiquidCrystal_I2C lcdN4(0x27, 16, 4)` |

!!! danger "GPIO 4 and GPIO 2 are the ultrasonic pair here"

    On this node **TRIG is GPIO 4 and ECHO is GPIO 2** — the opposite sense from

    [Node 1](node1.md), where TRIG is 2 and ECHO is 17. On

    [Node 2](node2.md) TRIG is 16 and ECHO 17. Never reuse another node's

    pinout.

## Power

> **Supply voltage and current draw are NOT verified from the current source.**

> There is no regulator, rail, current budget, antenna or enclosure supply

> documentation in the repository, and no schematic exists.

What the source implies:

* `ESP32_VREF 3.3f` — the analogue channels are referenced to a **3.3 V** logic

  domain, and the DHT11, DS18B20, HC-SR04, LCD and UARTs are 3.3 V logic

  peripherals.

* The ESP32 radio draws substantially more current than the sensors, so the

  supply for this node must be sized for Wi-Fi operation. No figure is given in

  the source; measure before deploying.

* A 5 V supply rail is plausible for the probe boards, but the source does not

  state one. Do not assume it.

This is the highest-power node in the cluster, because it is the only one that

runs Wi-Fi. Supply design is covered in [Power](../hardware/power.md).

## Communication

### UART chain

| Aspect | Detail |

|---|---|

| Upstream | Node 3, UART1, GPIO 25 RX |

| Downstream | Controller (Arduino Mega), UART2, GPIO 33 TX; GPIO 32 RX is opened but not read |

| Reverse | **None** — this variant does not send anything upstream |

| Protocol | Delimiter-separated ASCII key/value |

| Baud | 9600, `SERIAL_8N1` (`INTERNODE_BAUD`) |

| Frame | upstream verbatim + `\|pH:%.1f\|Turb:%d\|EC:%.1f\|EV:%d\|ST:%.1f\|node4:1;` |

| Timing / cadence | UART and e-mail task 50 ms; sensor task 1000 ms; LCD task 500 ms; DHT11 paced to ≥ 2000 ms |

| Receive buffer | `char rxBuffer[384]`; assembled packet `static char fullPacket[512]` |

| Integrity | **No checksum, no CRC, no sequence number, no acknowledgement, no retry.** Any frame ending in `;` is accepted and appended to |

### Network

| Aspect | Detail |

|---|---|

| Wi-Fi | `WiFi.begin(SSID, PASSWORD)` in `setup()`, **before** the tasks are created |

| Association attempts | 30 attempts × 500 ms |

| NTP | `configTime(3600, 0, "pool.ntp.org", "time.nist.gov")` — **Tunis UTC+1**, daylight-saving offset 0 |

| Time validation | Waits until epoch > 1700000000, up to 15 retries of 1 s |

| Transport | `esp_mail_secure_transport_ssl` |

| SMTP host / port | `smtp.gmail.com`, port `465`, declared in the configuration block — these two are real service values, unlike the account placeholders beside them |

| Message | HTML body, `enc_base64`, `esp_mail_priority_high` |

| Sender name | `WattLab Node 4` |

| Session reuse | One `SMPSession smtp;` object, `smtp.closeSession()` after each message |

```cpp

--8<-- "assets/snippets/node4-smtp-network-config.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·

<code>network and SMTP configuration block</code> ·

lines 11–24 · commit <code>db6d9b8</code>
</div>

!!! note "The literal values are redacted in the published snippet"

    The documentation build replaces the `WIFI_PASSWORD` and `AUTHOR_PASSWORD`

    macro values with a redaction marker. The other placeholders (SSID, sender,

    recipient) are shown as-is because they are not secret in themselves — but

    they are still **placeholders**, not a working deployment.

### Timing / cadence for e-mail

| Event | Interval | Rate limiting |

|---|---|---|

| Startup / reset | once per boot | none — always attempted |

| Heartbeat | every 86400 s (24 h) | `lastHbEpoch` persisted; **only advanced if the send succeeds**, so a failure retries next cycle |

| Fault alert | while a fault condition holds | `lastErrEpoch` persisted; 43200 s (12 h) cooldown, **only advanced if the send succeeds** |

`lastHeartbeatEpoch` and `lastErrorEmailEpoch` are stored as `unsigned long` in

NVS namespace **`email_state`** under the keys `lastHbEpoch` and `lastErrEpoch`.

Both are read once when the task starts, before the main loop, so the cadence

survives a reboot.

!!! important "A failed send does not advance the timestamp"

    Because the epochs are only persisted on success, a node with no Wi-Fi or no

    reachable SMTP server will retry the heartbeat on **every** 50 ms cycle

    rather than every 24 h. The cooldown protects the mailbox, not the radio.

    Expect repeated `[SMTP ERROR] Connect failed` lines on the debug UART while

    the network is down.

### Failure behaviour

* **No Wi-Fi.** `initNetworkAndTime()` prints

  `[ERROR] Wi-Fi Connection Failed!` and continues; the node still samples

  sensors and still forwards the UART frame. `sendMailMessage()` returns `false`

  immediately when `WiFi.status() != WL_CONNECTED`.

* **No NTP.** If the epoch stays below the threshold, e-mail timestamps will be

  wrong or invalid; the firmware does not refuse to send.

* **No SMTP.** `[SMTP ERROR] Connect failed: <reason>` or

  `[SMTP ERROR] Send failed: <reason>` is printed; the UART forwarding is

  unaffected, because e-mail is handled in the same task but is not in the

  forwarding path's critical section.

* **Upstream silent.** Node 4 SMTP has no timeout fallback of its own; it simply

  has nothing to forward.

* **Buffer overflow.** RX index resets to 0 and the frame is dropped.

* **Mutex timeout.** 50 ms sensor commit, 20 ms for the e-mail/UART and LCD

  snapshots; a timeout means a stale snapshot.

## RTOS Architecture

| Task name | Function | Stack | Priority | Core | Period |

|---|---|---|---|---|---|

| `N4_Sensors` | `Task_Sensors_Node4` | 4096 | 2 | 1 | 1000 ms (`vTaskDelayUntil`) |

| `N4_EmailUART` | `Task_Email_And_UART_Node4` | **5120** | 3 | 0 | 50 ms (`vTaskDelayUntil`) |

| `N4_LCD` | `Task_LCD_Node4` | 3072 | 1 | 1 | 500 ms (`vTaskDelayUntil`) |

The email/UART task has the **largest stack in the cluster, 5120 words**, which

is consistent with a task that holds an HTML message buffer, an `ESP_Mail_Session`

and a `SMTP_Message` on its stack.

Mutex: **`xLocalN4Mutex`** protecting `g_localN4` (pH, NTU, EC, submerged

temperature, ambient temperature, ambient humidity, EV volume and their seven

validity flags).

```cpp

--8<-- "assets/snippets/node4-smtp-setup.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·

<code>setup</code> ·

lines 428–448 · commit <code>db6d9b8</code>
</div>

Note the ordering in `setup()`: `loadCalibration()` → `initNetworkAndTime()`

→ mutex → tasks. Because `initNetworkAndTime()` blocks for up to 15 s (association)

plus up to 15 s (NTP) **before any task exists**, no measurement or forwarding

happens until the network attempt completes.

## Firmware

### Network and time

```cpp

--8<-- "assets/snippets/node4-smtp-init-network.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·

<code>initNetworkAndTime</code> ·

lines 107–136 · commit <code>db6d9b8</code>
</div>

### Message dispatch

```cpp

--8<-- "assets/snippets/node4-smtp-send-mail.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·

<code>sendMailMessage</code> ·

lines 138–171 · commit <code>db6d9b8</code>
</div>

### Heartbeat and fault rate limiting

```cpp

--8<-- "assets/snippets/node4-smtp-alert-logic.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·

<code>heartbeat and fault-alert logic</code> ·

lines 301–350 · commit <code>db6d9b8</code>
</div>

The fault predicate:

```text

hasError = any validity flag false

        OR ambTemp > 45.0

        OR ambHum  > 90.0

```

The HTML body of a fault alert lists each failed sensor as an `<li>` item, e.g.

*pH Sensor Fault / Out of Range*, *Turbidity Sensor Fault*, *EC Sensor Fault*,

*Submerged DS18B20 Temp Sensor Disconnected/Fault*, *Ambient Temperature Fault or

Excessive (>45C)*, *Ambient Humidity Fault or Excessive (>90%)*, *Effluent

Ultrasonic Tank Sensor Fault*.

## Sensors

Same sensors as [Node 4](node4.md):

| Page | Sensor | Used by Node 4 SMTP |

|---|---|---|

| [pH](../sensors/ph.md) | Analogue pH probe, GPIO 13 | **Yes** |

| [Turbidity](../sensors/turbidity.md) | SEN0189 / DFRobot analogue, GPIO 14 | **Yes** |

| [Conductivity (EC)](../sensors/conductivity.md) | Analogue EC probe, GPIO 12 | **Yes** |

| [Water Temperature (DS18B20)](../sensors/temperature.md) | DS18B20 submerged, GPIO 27 | **Yes** |

| [Humidity / Ambient (DHT11)](../sensors/humidity.md) | DHT11, GPIO 5 | **Yes** |

| [Ultrasonic (HC-SR04)](../sensors/ultrasonic.md) | HC-SR04, GPIO 4 / 2 | **Yes** — effluent volume (EV) |

| [Dissolved Oxygen](../sensors/dissolved-oxygen.md) | — | No — Node 2 measures DO |

| [Flow](../sensors/flow.md) | — | No — Node 3 measures flow |

## Calibration

Calibration constants live in NVS namespace **`node4_cal`** — the **same

namespace** as `Node4` — with **different defaults**:

| Key | `Node4` default | `Node4_SMTP` default |

|---|---|---|

| `phSlope` | 3.5 | 3.5 |

| `phOffset` | **-1.75** | **0.0** |

| `ecKFactor` | **9.997** | **2.0** |

!!! danger "Differences from standard Node 4 — check this before you work on the node"

    * **Calibration defaults differ.** `phOffset` is `0.0` here (not `-1.75`) and

      `ecKFactor` is `2.0` (not `9.997`). With the defaults as shipped, pH is

      `3.5 × V + 0.0` and EC is `V × 2.0` — the numbers are **not comparable**

      with a calibrated `Node4`.

    * **Shared NVS namespace.** Both firmwares read and write `node4_cal`.

      Flashing one variant onto a board calibrated for the other silently

      applies the wrong constants. Erase the NVS partition or issue an explicit

      reset when you change variant.

    * **No temperature compensation on EC.** This variant computes

      `ec = V × ecKFactor` with no `(1 + 0.0185 × (T − 25))` divisor, so EC

      drifts with temperature.

    * **EC is reported in mS/cm, not µS/cm.** There is no `× 1000` conversion,

      and the LCD prints `EC:%.1fmS`. A value of `0.85` here corresponds to

      roughly `850 µS/cm` on a `Node4`.

    * **Different downstream field names.** This variant emits

      `pH`, `Turb`, `EC`, `EV`, `ST`; `Node4` emits `pH`, `Turb`, `EC`, `TCV`.

      `EV` is the effluent volume that `Node4` calls `TCV`, and `ST` (submerged

      temperature) has **no** counterpart in the `Node4` frame. A controller

      written against one variant will silently miss fields on the other.

    * **No upstream packet cleaning.** `cleanUpstreamPacket()` is absent, so

      `AT`/`AH` from Node 2 pass through unchanged.

    * **No calibration console.** `Node4`'s `HELP` / `STATUS` / `SET:EC_K=` /

      `SET:PH_S=` / `SET:PH_O=` / `RESET` commands **do not exist here**.

      Constants can only be changed by editing and reflashing.

    * **Turbidity voltage domain.** This variant rescales the pin voltage by

      `5.0 / 3.3` and thresholds at 4.2 V / 2.5 V, instead of using the ESP32

      pin voltage directly with 3.20 V / 0.50 V thresholds as `Node4` does. The

      resulting NTU values are therefore on a different scale between the two

      variants.

    * **ADC validity checks are raw-count based** (`> 10 && < 4080`) rather than

      voltage-range based, and the ambient DHT11 has **no** range gate here

      (Node 2-style `!isnan()` only).

    * **Ultrasonic timeout is 20000 µs** here, against 25000 µs on `Node4`.

!!! note "Why these divergences matter in the field"

    Two identical-looking water-quality enclosures can emit different units and

    different field names for the same physical measurement. Before comparing

    data from a Node 4 board with data from a Node 4 SMTP board, confirm which

    firmware each one runs — the LCD is the giveaway: **`EC:…uS` on `Node4`,

    `EC:…mS` on `Node4_SMTP`**.

### Field calibration

Because there is no console, calibration requires editing the source:

1. Read the current constants out of the sketch (`phSlope`, `phOffset`,

   `ecKFactor`) or out of NVS with an ESP32 preferences tool.

2. Establish the true values against buffer solutions and a conductivity

   standard.

3. Edit the `preferences.getFloat(...)` **default** values in `loadCalibration()`

   — this only helps on a board whose NVS has not been written. To force a known

   value onto an existing board, clear the `node4_cal` namespace first.

4. Reflash and verify against a reference meter.

Procedures: [pH Calibration](../calibration/ph.md) ·

[Turbidity Calibration](../calibration/turbidity.md) ·

[Conductivity Calibration](../calibration/conductivity.md).

## Display / UI

16×4 character LCD over I²C at address `0x27`, refreshed every 500 ms. Rows are

written by direct HD44780 DDRAM addressing, `lcdSetRow()` issuing `0x80 | addr`

with `addr` from `{0x00, 0x40, 0x10, 0x50}`.

| Row | DDRAM address | Format string | Shown as |

|---|---|---|---|

| 0 | `0x00` | `EV:%dL pH:%.1f` | effluent volume in litres, pH to one decimal |

| 1 | `0x10` | `TU:%d EC:%.1fmS` | turbidity in NTU, EC in **mS/cm** |

| 2 | `0x40` | `ST:%.1fC AT:%.1fC` | submerged temperature, ambient temperature |

| 3 | `0x50` | `AH:%.0f%%` | ambient humidity, no decimals |

* The row order and content match [Node 4](node4.md); only the EC unit and

  precision differ.

* As on `Node4`, there is **no status or error line**. Invalid channels print

  their last stored number, so a failed probe looks like a live reading.

* The `mS` suffix on row 1 is the fastest way to tell the two variants apart in

  the field.

## Troubleshooting

| Symptom | Likely cause | Check | Action |

|---|---|---|---|

| No e-mail at all, ever | Placeholder credentials are still in the sketch | Debug UART for the SSID printed at boot and for `[SMTP ERROR]` lines | Supply real credentials at build time (see the warning at the top of this page); use an SMTP app password |

| No Wi-Fi association | SSID/PSK wrong, or no coverage at the enclosure | Debug UART: 30 dots then `[ERROR] Wi-Fi Connection Failed!` | Move the node or add coverage; do not commit a working PSK to fix this |

| `[SMTP ERROR] Connect failed` repeating rapidly | Sends are retried every 50 ms because the epoch is only advanced on success | Count the error lines over a few seconds | Restore connectivity. Expect retries, not silence |

| E-mail timestamps are wrong or unset | NTP did not synchronise | Debug UART: `[INFO] Current Epoch Time: …` | Check the NTP servers and the network path; the time zone is hard-coded to Tunis UTC+1 |

| No startup e-mail after a power cycle | Network attempt happens in `setup()` before the tasks start and may fail within 15 s | Read the debug output from the boot itself | Ensure the network is reachable at boot, not just later |

| Fault e-mail every few minutes instead of every 12 h | `lastErrEpoch` not persisted (namespace not writable) or the send succeeded but the write failed | Check that `email_state` persists across a reboot | Re-flash; verify NVS is writable |

| No fault e-mail despite a broken sensor | The fault is not in the alert list — for example the ultrasonic head reading a plausible but wrong volume | Compare the LCD against the physical tank | Understand which conditions actually raise an alert |

| `pH`, `Turb` or `EC` readings unstable while Wi-Fi is associated | **ADC2 is unusable while Wi-Fi is active** — the committed source reads ADC2 pins anyway | Compare readings with Wi-Fi disconnected from the access point | Treat as a firmware limitation; verify against a reference meter. A source change (move to ADC1 pins, or read before Wi-Fi) is required to fix it |

| LCD shows `EC:0.9mS` where the other board shows `EC:900uS` | **Different units between the two variants** — this is expected | Check the suffix | Convert: µS/cm = mS/cm × 1000 |

| Controller cannot find a `TCV` field | This variant emits `EV`, not `TCV` | Inspect the downstream frame | Adjust the controller's parser |

| Controller receives two `AT`/`AH` pairs | This variant does not clean the upstream packet | Compare the incoming and outgoing frames | Expected; `Node4` strips them, this variant does not |

| `EC` drifts as the water temperature changes | **No temperature compensation** in this variant | Compare EC at two water temperatures | Expect the drift, or move the probe to a temperature-controlled point |

| `HELP` / `STATUS` / `SET:` produce no output | **This variant has no calibration console** | Try the commands and read nothing | Edit the source and reflash; see Calibration |

| Calibration constants look wrong after a variant swap | Both variants share the `node4_cal` namespace | Read the constants from the sketch's defaults | Clear the `node4_cal` namespace and re-apply the constants for the variant you are running |

| Ultrasonic reads invalid more often than on `Node4` | Timeout is 20000 µs here vs 25000 µs | Check TRIG GPIO 4 / ECHO GPIO 2 and clean the transducer face | Repair the head; a longer timeout would need a source change |

| Downstream frame never appears | TX 33 → controller RX, or the controller is not powered | Verify ground continuity and 9600 baud | Restore the link |

| Controller frame missing Node 3's `FLM` | No upstream frame has arrived | Check the Node 3 → Node 4 link | Fix upstream; this node has no fallback frame of its own |

| Fatal trap on the debug UART | Mutex or task creation failure | — | The node is dead by design; reflash |

## Validation

1. **Boot sequence on the debug UART at 115200 baud.** Confirm, in order:

   ```text

   Connecting to Wi-Fi: <SSID>

   ..................

   [INFO] Wi-Fi Connected!

   [INFO] Synchronizing NTP time for Tunis...

   [INFO] Current Epoch Time: <epoch>

   ```

   A missing `[INFO] Wi-Fi Connected!` means the node never had a network when

   the tasks were created — the measurement chain still runs, but no e-mail will

   ever be sent.

2. **Startup e-mail.** Power-cycle the node and confirm a message with the

   subject `[WattLab Node 4] SYSTEM RESET / STARTUP` arrives. If it does not,

   the fault is credentials, network or SMTP reachability — not the sensors.

3. **Heartbeat.** With everything healthy, the next message is

   `[WattLab Node 4] Daily Heartbeat OK`, 24 h later. To test the logic without

   waiting, note that the heartbeat epoch is stored in `email_state`; clearing

   that namespace makes the next cycle treat it as due.

4. **Fault alert.** Disconnect the pH probe and wait for the cooldown window (or

   clear `email_state`). Confirm a `[WattLab Node 4] FAULT ALERT` arrives whose

   HTML body itemises *pH Sensor Fault / Out of Range*. Then repeat for the

   DHT11 by heating or humidifying the enclosure beyond 45 °C / 90 %.

5. **Variant identification on the LCD.** Confirm row 1 ends in `mS`, not `uS`.

   This is the field test for which firmware is actually running.

6. **Field-name check on the wire.** Capture the downstream frame at 9600 baud

   and confirm it contains `EV:` and `ST:` and does **not** contain `TCV:`.

7. **ADC2 conflict check.** Record pH, turbidity and EC with the access point

   associated, then with Wi-Fi off. Any change beyond the usual noise confirms

   the interference.

8. **NVS persistence check.** Send a note of the three calibration constants,

   power-cycle, and confirm the same values are loaded at boot and on the LCD.

9. **UART continuity unaffected by e-mail.** While deliberately failing every

   e-mail send, confirm the downstream frame keeps flowing at the upstream rate.

   E-mail failure must not stall the measurement chain.

## Source

* Firmware file at the pinned commit:

  [`FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino)

* Directory listing:

  [`FreeRTOS_Implementation/Node4_SMTP`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP)

* Extracted snippets used on this page:

  [node4-smtp-network-config](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L11-L24),

  [node4-smtp-init-network](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L107-L136),

  [node4-smtp-send-mail](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L138-L171),

  [node4-smtp-alert-logic](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L301-L350),

  [node4-smtp-setup](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L428-L448)

* Commit: [`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/commit/db6d9b896341a9c7d8fd01913e854b663c110d55)

* Firmware Source Map: [../firmware/source-map.html](../firmware/source-map.md)

* Related: [Node 4](node4.md) ·

  [Nodes Index](index.md) ·

  [Conductivity](../sensors/conductivity.md) ·

  [pH](../sensors/ph.md) ·

  [Serial Links](../communication/serial-links.md) ·

  [RTOS Tasks](../rtos/tasks.md)
---
title: Firmware Configuration
description: The Node 4 serial calibration console, every compile-time constant in the five CIRQUA sketches, and how to change each one safely.
---

# Firmware Configuration

CIRQUA firmware is configured in two very different ways, and conflating them is
the most common source of field confusion:

| Surface | Where it lives | Applies to | Needs a reflash? |
|---|---|---|---|
| **Serial calibration console** | Node 4's debug UART at 115200 baud | Node 4 only: pH slope, pH offset, EC K-factor | No — persisted in NVS |
| **Compile-time constants** | `#define` / `const float` blocks inside each `.ino` | Whichever node the file belongs to | Yes |

There is **no** remote configuration, no configuration file, no web interface and
no OTA. If a setting is not in the table below, it is not configurable.

<div class="cirqua-identity">
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Console link</span>
    <span class="cirqua-identity__value">USB serial / <code>Serial</code>, <strong>115200 baud</strong></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Line discipline</span>
    <span class="cirqua-identity__value">newline-terminated, no flow control</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">NVS namespace</span>
    <span class="cirqua-identity__value"><code>node4_cal</code> (and <code>email_state</code> on the SMTP variant)</span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Persisted keys</span>
    <span class="cirqua-identity__value"><code>phSlope</code>, <code>phOffset</code>, <code>ecKFactor</code></span>
  </div>
  <div class="cirqua-identity__item">
    <span class="cirqua-identity__label">Available on</span>
    <span class="cirqua-identity__value"><strong>Node 4 only</strong> — <span class="cirqua-badge cirqua-badge--unknown">absent</span> on Nodes 1, 2, 3 and on the SMTP variant</span>
  </div>
</div>

## Part 1 — The Node 4 serial calibration console

### How to reach it

1. Connect the Node 4 board by USB.
2. Open a serial terminal at **115200 baud**, **newline** line ending, no flow
   control. The Arduino Serial Monitor's line-ending control must be set to
   *Newline* or *Both*.
3. Type a command and press Enter. **A command is not executed until the
   newline arrives** — see the blocking note below.

The console is served by `handleSerialCalibrationCommands()`, which is called
once per iteration of Node 4's UART task (a 50 ms period). Only **one** node in
the cluster can be talking to a PC this way at a time, and it is Node 4.

### Command reference

| Command | Behaviour | Validation | Persisted |
|---|---|---|---|
| `HELP` | Prints the command list | none | no |
| `STATUS` | Prints raw ADC counts and calibrated volts for pH, EC and turbidity, plus the saved constants | none | no |
| `SET:EC_K=<val>` | Sets and saves the conductivity K-factor | **Rejects values ≤ 0** with `[ERROR] Invalid value for EC K-Factor.` | yes → `ecKFactor` |
| `SET:PH_S=<val>` | Sets and saves the pH slope | none | yes → `phSlope` |
| `SET:PH_O=<val>` | Sets and saves the pH offset | none | yes → `phOffset` |
| `RESET` | Clears the whole `node4_cal` namespace and reloads the compiled defaults, printing the banner again | none | yes (destructive) |

!!! info "Case sensitivity — a real detail worth knowing"
    `HELP`, `STATUS` and `RESET` are matched with `equalsIgnoreCase()`, so
    `help`, `Status` and `reset` all work.

    The three `SET:` keywords are matched with `startsWith()`, which is
    **case-sensitive** in the current source. `SET:EC_K=…` works;
    `set:ec_k=…` does not, and is silently ignored — no error is printed and the
    node simply carries on.

    Values after the `=` are parsed with `toFloat()`, so whitespace around the
    number is tolerated and a non-numeric value yields `0.0`.

!!! warning "`SET:PH_S` and `SET:PH_O` have no range check"
    Only `SET:EC_K` validates its argument. A pH slope of `0`, a negative slope
    or a nonsense offset is accepted and written straight to flash. Check the
    values with `STATUS` after setting them, and set them from a calibration
    procedure rather than by trial.

### What persists, and what does not

Persisted in NVS (survives power cycles and reflashing, until erased or
`RESET` is sent):

| Namespace | Key | Type | Written by |
|---|---|---|---|
| `node4_cal` | `phSlope` | float | `SET:PH_S=`, `RESET` |
| `node4_cal` | `phOffset` | float | `SET:PH_O=`, `RESET` |
| `node4_cal` | `ecKFactor` | float | `SET:EC_K=`, `RESET` |
| `email_state` | `lastHbEpoch` | unsigned long | SMTP variant, after a successful heartbeat |
| `email_state` | `lastErrEpoch` | unsigned long | SMTP variant, after a successful fault e-mail |

Not persisted — reset to the compiled default on every boot:

* the `Node4` defaults (`phSlope 3.5`, `phOffset -1.75`, `ecKFactor 9.997`);
* `Node4_SMTP`'s different defaults (`phSlope 3.5`, `phOffset 0.0`,
  `ecKFactor 2.0`);
* the firmware build itself, if you flash over the top of saved calibration —
  flashing does **not** erase NVS, so a reflashed board keeps its saved
  constants.

!!! warning "`RESET` clears the namespace, not the flash"
    `RESET` empties `node4_cal` and immediately reloads the compiled defaults.
    It does not touch the firmware, does not erase the whole flash, and does not
    touch `email_state`.

### The source of both halves of the console

Calibration load, including the boot banner and the compiled defaults:

```cpp
--8<-- "assets/snippets/node4-load-calibration.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>loadCalibration</code> · lines 132–156 · commit <code>db6d9b8</code>
</div>

The command handler itself:

```cpp
--8<-- "assets/snippets/node4-calibration-console.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·
<code>handleSerialCalibrationCommands</code> · lines 717–931 · commit <code>db6d9b8</code>
</div>

### A complete session, copy-and-paste

The prompts and formats below are exactly those in the source. The **numeric
sensor values are illustrative** — a real `STATUS` depends on your probes and
buffers.

```text
$ picocom -b 115200 /dev/ttyUSB0     # any 115200 8N1 terminal works

--- Loaded Calibration Constants ---
pH Slope: 3.500 | pH Offset: -1.750 | EC K-Factor: 9.997
[ADC] Resolution: 12-bit
[ADC] Attenuation: 11 dB
[ADC] Multi-sample filtering enabled
[DS18B20] Devices found: 1
[DHT11] Initialized

> HELP

========== NODE 4 CALIBRATION DEBUG CONSOLE ==========
STATUS        - View current raw ADC and calculated values
SET:EC_K=<val>- Set and save EC K factor
SET:PH_S=<val>- Set and save pH slope
SET:PH_O=<val>- Set and save pH offset
RESET         - Reset calibration to factory defaults
=====================================================

> STATUS

--- Live Raw Sensor Diagnostics ---
pH   -> Raw ADC: 2043 | Voltage: 2.213V
EC   -> Raw ADC: 1372 | Voltage: 1.487V | K: 9.997
Turb -> Raw ADC:  410 | Voltage: 0.445V
Saved Constants -> pH Slope: 3.500 | pH Offset: -1.750 | EC K: 9.997

> SET:EC_K=0
[ERROR] Invalid value for EC K-Factor.

> SET:EC_K=-4.5
[ERROR] Invalid value for EC K-Factor.

> SET:EC_K=8.412
[SUCCESS] EC K-Factor updated and saved to flash: 8.412

> SET:PH_S=3.480
[SUCCESS] pH Slope updated and saved: 3.480

> SET:PH_O=-1.610
[SUCCESS] pH Offset updated and saved: -1.610

> STATUS

--- Live Raw Sensor Diagnostics ---
pH   -> Raw ADC: 2043 | Voltage: 2.213V
EC   -> Raw ADC: 1372 | Voltage: 1.487V | K: 8.412
Turb -> Raw ADC:  410 | Voltage: 0.445V
Saved Constants -> pH Slope: 3.480 | pH Offset: -1.610 | EC K: 8.412

> RESET
--- Loaded Calibration Constants ---
pH Slope: 3.500 | pH Offset: -1.750 | EC K-Factor: 9.997
[SUCCESS] Calibration reset to defaults.
```

Field-by-field reading of the `STATUS` output:

| Field | Meaning | Valid range checked by the firmware |
|---|---|---|
| `pH -> Raw ADC` | 12-bit averaged count on GPIO 13 | — |
| `pH -> Voltage` | `analogReadMilliVolts` average | valid if `0.02 ≤ V ≤ 3.30` |
| `EC -> Raw ADC` / `Voltage` | same pair on GPIO 12 | valid if `0.0 ≤ V ≤ 3.30` |
| `EC -> … \| K:` | the live K-factor, i.e. the last saved value | `> 0` |
| `Turb -> Raw ADC` / `Voltage` | same pair on GPIO 14 | valid if `0.0 ≤ V ≤ 3.30` |
| `Saved Constants -> …` | the three values that will survive a reboot | — |

!!! note "`STATUS` does not change stored values"
    It performs fresh ADC reads and prints them; it does not read or write the
    sensor task's snapshot. Use it to characterise a probe at the bench, not to
    read what the node is currently reporting on the wire.

!!! warning "The console briefly blocks the UART task"
    `handleSerialCalibrationCommands()` uses `Serial.readStringUntil('\n')`.
    Until a newline is received, that call does not return, so the Node 4 UART
    task stops forwarding telemetry for that interval. Type a complete line and
    press Enter; never leave a partial command open. While you are in the
    console, frames from Node 3 will be missed and will be re-requested only by
    the next valid frame — the protocol has no replay, so a gap appears in the
    data stream.

## Part 2 — Compile-time configuration

Changing anything below requires editing the sketch and reflashing that node.
Nothing else is configurable at runtime except the three Node 4 calibration
values above.

### Node 1 — `Node1.ino`

| Constant | Value | Effect | How to change |
|---|---|---|---|
| `INTERNODE_BAUD` | `9600` | UART1 link rate to Node 2 | Edit line 5; **must** match Node 2's `INTERNODE_BAUD` |
| `PIN_N1_TRIG` | `2` | Ultrasonic trigger pin | Edit line 10; also a strapping pin — see [Flashing](flashing.md)) |
| `PIN_N1_ECHO` | `17` | Ultrasonic echo pin | Edit line 11 |
| `PIN_N1_UART_RX` / `PIN_N1_UART_TX` | `32` / `33` | UART1 to Node 2 | Edit lines 14–15 |
| `PIN_LCD_SDA` / `PIN_LCD_SCL` | `21` / `22` | I²C to the LCD backpack | Edit lines 17–18 |
| `TANK_HEIGHT` | `260.0f` cm | Full height used for `waterHeight = TANK_HEIGHT − distance` and the low-volume check | Edit line 23 and re-measure the tank |
| `TANK_RADIUS` | `110.0f` cm | Cylinder radius in the volume formula | Edit line 24 |
| `TEMP_ALERT_TH` | `45.0f` °C | `OVERTEMP` / `HOT+HUM` threshold on Node 2's ambient temperature | Edit line 27 |
| `HUMID_ALERT_TH` | `80.0f` % RH | `HI HUMID` / `HOT+HUM` threshold on Node 2's humidity | Edit line 28 |
| `TAV_LOW_ALERT_TH` | `5000` L | `LOW TAV` status string | Edit line 31 |
| `TBV_LOW_ALERT_TH` | `500` L | `LOW TBV` status string | Edit line 32 |
| `RX_TIMEOUT_MS` | `3000` | `millis()` gap after which the LCD shows `ERROR` | Edit line 34 |
| `TX_INTERVAL_MS` | `500` | How often Node 1 emits its own `\|TAV:…\|node1:…;` frame | Edit line 35 |
| Volume factor `2.0f` | literal, in `Task_Sensors_Node1` | **Doubles** the computed litres; the value on the wire is doubled and truncated | Edit the literal on line 107 after empirically justifying it |

### Node 2 — `Node2.ino`

| Constant | Value | Effect | How to change |
|---|---|---|---|
| `INTERNODE_BAUD` | `9600` | Both UART1 and UART2 | Edit line 10 |
| `PIN_DS18B20` | `4` | 1-Wire water temperature | Edit line 12 |
| `PIN_DO_ANALOG` | `34` | Analog dissolved-oxygen input (ADC1) | Edit line 13 |
| `PIN_N2_TRIG` / `PIN_N2_ECHO` | `16` / `17` | Ultrasonic head over Feeding Tank B | Edit lines 14–15 |
| `PIN_DHT11` | `27` | Ambient temperature and humidity | Edit line 16 |
| `PIN_N1_UART_RX` / `TX` | `25` / `26` | UART1 to Node 1 | Edit lines 17–18 |
| `PIN_N3_UART_RX` / `TX` | `32` / `33` | UART2 to Node 3 | Edit lines 19–20 |
| `DHTTYPE` | `DHT11` | DHT sensor family | Edit line 22 |
| `VREF` | `5000.0f` mV | Assumed ADC full scale for the DO conversion | Edit line 25; see the caveat in [Known Limitations](../validation/known-limitations.md) |
| `ADC_RESOLUTION` | `4095.0f` | 12-bit full-scale count | Edit line 26 |
| `TWO_POINT_VOLTAGE` | `1000.0f` mV | The 1 V "two-point" reference used to scale the DO output | Edit line 27 |
| `SATURATION_DO_25C` | `8.26f` mg/L | Saturation concentration at 25 °C | Edit line 28; the single most sensitive DO constant |
| `TANK_HEIGHT` / `TANK_RADIUS` | `178.0f` / `59.5f` cm | Feeding Tank B geometry | Edit lines 31–32 |
| Temperature coefficient `−0.02f` | literal | DO compensation per °C away from 25 °C | Edit line 151 |
| DHT pacing `2000` ms | literal | Minimum interval between DHT reads | Edit line 194 |
| Echo timeout `20000` µs | literal | Ultrasonic wait on Node 2 | Edit line 171 |
| Valid-range gate `−55 … 125 °C` | literals | DS18B20 acceptance window | Edit line 135 |

### Node 3 — `Node3.ino`

| Constant | Value | Effect | How to change |
|---|---|---|---|
| `INTERNODE_BAUD` | `9600` | Both UARTs | Edit line 3 |
| `PIN_FLOW_SENSOR` | `23` | Flow pulse input, `INPUT_PULLUP`, ISR on **falling** edge | Edit line 6 |
| `PIN_UP_UART_RX` / `TX` | `25` / `26` | UART1 to Node 2 | Edit lines 7–8 |
| `PIN_DOWN_UART_RX` / `TX` | `32` / `33` | UART2 to Node 4 | Edit lines 9–10 |
| `FLOW_CAL_FACTOR` | `5.5f` | Pulses per litre; `flowRate = pulses / 5.5` L/min | Edit line 12; **the** flow calibration constant |
| `TIMEOUT_MS` | `2000` | Upstream silence after which the fallback frame is emitted once | Edit line 13 |
| Interrupt edge | `FALLING` | Which edge increments the counter | Edit line 46; also edit `INPUT_PULLUP` on line 45 together with it |

### Node 4 — `Node4.ino`

| Constant | Value | Effect | How to change |
|---|---|---|---|
| `INTERNODE_BAUD` | `9600` | Both UARTs | Edit line 10 |
| `PIN_EFFLUENT_TRIG` / `ECHO` | `4` / `2` | Effluent tank ultrasonic head | Edit lines 13–14 |
| `PIN_PH_ANALOG` | `13` | pH analogue input (ADC2) | Edit line 15 |
| `PIN_TURB_ANALOG` | `14` | Turbidity analogue input (ADC2) | Edit line 16 |
| `PIN_EC_ANALOG` | `12` | Conductivity analogue input (ADC2) — **also a strapping pin** | Edit line 17 |
| `PIN_SUB_DS18B20` | `27` | Submerged 1-Wire temperature | Edit line 18 |
| `PIN_N4_DHT11` | `5` | Ambient temperature and humidity (strapping pin) | Edit line 19 |
| `PIN_N4_UART_RX` / `TX` | `25` / `26` | UART1 from Node 3 | Edit lines 21–22 |
| `PIN_N5_UART_RX` / `TX` | `32` / `33` | UART2 to the controller (Mega) | Edit lines 23–24 |
| `PIN_N4_LCD_SDA` / `SCL` | `21` / `22` | I²C to the LCD | Edit lines 26–27 |
| `DHTTYPE` | `DHT11` | DHT family | Edit line 29 |
| `ADC_RESOLUTION` | `4095.0f` | 12-bit full-scale count | Edit line 37 |
| `ADC_SAMPLES` | `16` | Averaging depth in both `readADCFiltered` and `readSensorVoltage` | Edit line 48; raising it lengthens the sampling window |
| `SENSOR_ADC_ATTENUATION` | `ADC_11db` | Input range for pH, turbidity and EC | Edit line 52; lowering it raises resolution but clips the range |
| `TANK_HEIGHT` / `TANK_RADIUS` | `178.0f` / `59.5f` cm | Effluent geometry | Edit lines 40–41 |
| LCD address | `0x27` | I²C address of the HD44780 backpack | Edit line 77 |
| pH defaults | `3.5f`, `-1.75f` | Compiled fallback for `phSlope`, `phOffset` | Edit lines 138, 141; prefer the console |
| EC default | `9.997f` | Compiled fallback for `ecKFactor` | Edit line 144; prefer the console |
| pH temperature coefficient | `0.02f` | Compensation denominator per °C from 25 °C | Edit line 479 |
| EC temperature coefficient | `0.0185f` | Compensation divisor per °C from 25 °C | Edit line 605 |
| Turbidity polynomial | `−1120.4`, `5742.3`, `−4353.8` | NTU mapping; breakpoints at `3.20` V and `0.50` V; clamp `[0, 3000]` | Edit lines 534–564 |
| Valid windows | `0.02 ≤ V ≤ 3.30` (pH), `0.0 ≤ V ≤ 3.30` (turbidity, EC), `0 ≤ pH ≤ 14` | What counts as a valid reading | Edit lines 498–501, 573–574, 626–627 |
| DS18B20 resolution | `setResolution(10)` | 0.25 °C, ~187.5 ms blocking conversion | Edit line 276 |
| DHT pacing | `2000` ms | Minimum interval between DHT reads | Edit line 644 |
| Echo timeout | `25000` µs | Ultrasonic wait on Node 4 | Edit line 328 |
| Rejection window | `TANK_HEIGHT + 20` cm | Largest accepted distance | Edit line 340 |

### Node 4 SMTP variant — `Node4_SMTP.ino`

| Constant | Value | Effect | How to change |
|---|---|---|---|
| `WIFI_SSID` | `YOUR_WIFI_SSID` — **placeholder** | SSID passed to `WiFi.begin` | Supply at build time from an untracked source; never commit a real SSID |
| `WIFI_PASSWORD` | `YOUR_WIFI_PASSWORD` — **placeholder, redacted in this documentation** | Wi-Fi passphrase | As above |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server | Edit line 19 for another provider |
| `SMTP_PORT` | `465` | Implicit-TLS port | Edit line 20 |
| `AUTHOR_EMAIL` | `your_sender_email@gmail.com` — **placeholder** | Sender mailbox | Build time, untracked |
| `AUTHOR_PASSWORD` | `your_email_app_password` — **placeholder, redacted in this documentation** | Mailbox app password | Build time, untracked |
| `RECIPIENT_EMAIL` | `your_recipient_email@gmail.com` — **placeholder** | Operator mailbox | Build time, untracked |
| `ESP32_VREF` | `3.3f` | Assumed ADC full scale | Edit line 44 |
| `ADC_RESOLUTION` | `4095.0f` | 12-bit full-scale count | Edit line 45 |
| `TANK_HEIGHT` / `TANK_RADIUS` | `178.0f` / `59.5f` cm | Effluent geometry | Edit lines 48–49 |
| NTP offset | `3600`, DST `0` | **Tunis, UTC+1, no daylight saving** | Edit line 122 |
| NTP servers | `pool.ntp.org`, `time.nist.gov` | Time sources | Edit line 122 |
| Epoch threshold | `1700000000` | Time considered valid | Edit line 127 |
| Wi-Fi attempts | `30` × 500 ms | Association budget before giving up | Edit line 113 |
| Heartbeat interval | `86400` s (24 h) | "Operating normally" e-mail | Edit line 305 |
| Error cooldown | `43200` s (12 h) | Minimum gap between fault e-mails | Edit line 328 |
| Fault thresholds | `> 45.0f` °C, `> 90.0f` % | Ambient conditions that raise a fault | Edit line 326 |
| pH defaults | `3.5f`, `0.0f` | **Different from `Node4`** | Edit lines 101–102 |
| EC default | `2.0f` | **Different from `Node4`**, and reported in mS/cm | Edit line 103 |

The placeholder configuration block, as published:

```cpp
--8<-- "assets/snippets/node4-smtp-network-config.cpp"
```

<div class="cirqua-source">
<span class="cirqua-source__label">Source</span>
<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino">lestealthy/Cirqua</a> ·
<code>FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino</code> ·
Wi-Fi/SMTP macro block · lines 11–24 · commit <code>db6d9b8</code> ·
password macros redacted by the extractor
</div>

!!! danger "Credentials are the one thing this page will never publish"
    The values in the committed source are placeholders and must stay that way in
    version control. Real Wi-Fi credentials and a mailbox app password are
    supplied at build time from a source that is never committed. The extraction
    tooling redacts the two password macros automatically, so even the embedded
    snippet cannot leak a value. If you ever find a real SSID, password or
    mailbox address in a CIRQUA commit, treat it as an incident and rotate it.

## Configuration change safety notes

| Change | Risk to check before deploying |
|---|---|
| `TANK_HEIGHT` / `TANK_RADIUS` | The low-volume thresholds (`TAV_LOW_ALERT_TH`, `TBV_LOW_ALERT_TH`) are tuned to the old geometry and will mis-fire |
| Node 1's `2.0f` volume factor | Node 1's LCD status string and any downstream consumer of `TAV` change immediately |
| `SATURATION_DO_25C` | Dissolved oxygen is linear in this constant; an error scales every `DO` value |
| `FLOW_CAL_FACTOR` | `FLM` is a rate, so the whole downstream flow record rescales |
| `INTERNODE_BAUD` | Must be changed on **both** ends of a link; a mismatch produces a wall of garbage |
| `SENSOR_ADC_ATTENUATION` | Values above the attenuated range clip silently, producing a plausible but wrong reading |
| Turbidity polynomial | The breakpoints and the quadratic are coupled; changing one without the others leaves a discontinuity |
| NTP offset `3600` | Hard-coded for Tunis. A unit deployed outside that zone will timestamp e-mails wrongly |
| Any pin change | Re-verify against [GPIO Map](../hardware/gpio-map.md)), including the strapping pins |

## Related

* [Calibration](../calibration/index.md)) — the procedures that use these
  constants.
* [Flashing](flashing.md)) — putting a modified sketch on the board.
* [Code Reference](code-reference.md)) — the code behind each constant.
* [Known Limitations](../validation/known-limitations.md) — what the constants
  cannot compensate for.
* [Source Map](source-map.md)) — file, symbol and line for every constant.
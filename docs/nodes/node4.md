---

title: Node 4 (Water Quality Analytics Tail)

description: Field-service manual for CIRQUA Node 4 — pH, turbidity, EC, submerged and ambient temperature, effluent level, and the calibration console.

---

# Node 4 (Water Quality Analytics Tail)

## Identity card

--8<-- "assets/generated/node-cards/node4.html"


<div class="cirqua-photo-slot">
  <span class="cirqua-photo-slot__label">Photo required</span>
  <p class="cirqua-photo-slot__title">Node 4 — Effluent analytics — no photograph on record</p>
  <p class="cirqua-photo-slot__note">
    Photograph the node, the pH, turbidity and conductivity probe positions, the submerged temperature probe, and the LCD.
    No photograph of CIRQUA hardware was found in the firmware repository or
    the local workspace, so this slot is intentionally empty. A stock or
    generated image is not used, because that would misrepresent the hardware.
  </p>
</div>

## Responsibilities

Node 4 terminates the measurement chain and adds the water-quality dimension.

Its duties:

1. **Samples seven quantities at 1 Hz**: submerged DS18B20 temperature, pH,

   turbidity, electrical conductivity, ambient temperature and humidity

   (DHT11, paced to ≥ 2000 ms), and effluent tank volume (HC-SR04).

2. **Applies calibration**: pH via a linear slope/offset model plus temperature

   compensation; turbidity via a piecewise quadratic NTU conversion; EC via a

   K-factor plus temperature compensation and a ×1000 conversion to µS/cm. All

   three calibration constants are held in **NVS namespace `node4_cal`** and are

   editable at runtime from a serial console.

3. **Cleans and forwards** the upstream frame: `cleanUpstreamPacket()` strips the

   `AT:` and `AH:` tokens so the controller receives **one** ambient pair, from

   Node 4's own DHT11, not two.

4. **Appends its own fields** — `pH`, `Turb`, `EC`, `TCV`, `node4` — and sends

   the result to the downstream controller over UART2 (GPIO 32 RX / 33 TX; the

   pins are commented `// To Controller (Mega)`).

5. **Runs a PC serial calibration and diagnostics console** on the debug UART at

   115200 baud.

6. **Renders the local 16×4 I²C LCD** at 500 ms.

Node 4 originates nothing. It cannot forward anything it has not received.

## Inputs

| Input | Device | Signal | Notes |

|---|---|---|---|

| pH | [Analogue pH probe](../sensors/ph.md) | ADC2, GPIO 13 | `ADC_11db`, 12-bit |

| Turbidity | [SEN0189 / DFRobot analogue](../sensors/turbidity.md) | ADC2, GPIO 14 | Quadratic NTU model |

| Electrical conductivity | [Analogue EC probe](../sensors/conductivity.md) | ADC2, GPIO 12 | K-factor, µS/cm |

| Submerged water temperature | [DS18B20](../sensors/temperature.md) | 1-Wire, GPIO 27 | 10-bit, **blocking** by design |

| Ambient temperature / humidity | [DHT11](../sensors/humidity.md) | GPIO 5 | Range-gated on this node |

| Effluent tank level (TCV) | [HC-SR04 ultrasonic](../sensors/ultrasonic.md) | TRIG GPIO 4, ECHO GPIO 2 | 25 ms timeout, range rejection |

| Upstream frame | [UART](../communication/serial-links.md) | GPIO 25 RX (UART1) | From Node 3 |

| Debug UART | USB/serial | `Serial` | 115200 baud; calibration console |

## Outputs

| Output | Field | Format | Notes |

|---|---|---|---|

| Downstream to controller | entire cleaned upstream frame | verbatim | `AT:` and `AH:` tokens removed |

| Downstream to controller | `pH` | `%.1f` | 0.0 when invalid |

| Downstream to controller | `Turb` | `%d` | integer NTU, 0 when invalid |

| Downstream to controller | `EC` | `%.0f` | **µS/cm**, 0 when invalid |

| Downstream to controller | `TCV` | `%d` | integer litres, 0 when invalid |

| Downstream to controller | `node4` | hard-coded `1` | **Always 1**, regardless of local sensor validity |

| Local display | 16×4 I²C LCD, address `0x27` | — | Refreshed every 500 ms |

| Debug UART | `Serial`, 115200 baud | text | ADC status lines, boot banners, `[NODE 4 PACKET TRANSACTION]` dump, console responses |

| E-mail | **None** | — | E-mail exists only on [Node 4 SMTP](node4-smtp.md) |

!!! warning "`node4` is a constant"

    The downstream frame always ends `|node4:1;`. Unlike `node1`, `node2` and

    `node3`, which are computed from validity flags, **Node 4's health flag

    carries no information**. A downstream consumer cannot tell from `node4:1`

    that the pH probe has failed. Use the value fields (a zero or an implausible

    reading) and Node 4's LCD / debug output instead.

Downstream frame structure:

```text

<cleaned upstream>|pH:%.1f|Turb:%d|EC:%.0f|TCV:%d|node4:1;

```

### `cleanUpstreamPacket` — why the ambient fields are stripped

```cpp

--8<-- "assets/snippets/node4-packet-cleaner.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>cleanUpstreamPacket</code> ·

lines 936–990 · commit <code>db6d9b8</code>
</div>

It splits the incoming frame on `|`, drops any token that starts with `AT:` or

`AH:`, and rejoins the rest. The effect: Node 2's enclosure ambient pair is

removed so that the controller sees exactly one `AT`/`AH` — but note that the

**re-joined tokens are only the upstream fields**; Node 4's own ambient values

are **not** re-added under those names. The downstream frame therefore contains

pH, Turbidity, EC and TCV but no ambient temperature or humidity keys at all. Do

not expect `AT` or `AH` in the controller's frame; the controller gets Node 4's

ambient values only through the LCD or the debug UART.

## Controller

| Property | Value |

|---|---|

| MCU | ESP32 |

| Framework | Arduino ESP32 (`.ino` sketch) |

| RTOS | FreeRTOS, `xTaskCreatePinnedToCore` |

| Debug UART | `Serial.begin(115200)` |

| Non-volatile storage | `Preferences.h` (NVS), namespaces `node4_cal` |

| Board variant | > **Not verified from the current source.** |

`setup()` loads calibration, creates the mutex, creates the three tasks, and

prints the loaded constants. `loop()` calls `vTaskDelete(NULL)`.

## GPIO Map

| Peripheral | Signal | GPIO | Direction | Notes |

|---|---|---|---|---|

| Effluent ultrasonic | TRIG | 4 | out | 3 µs low, 10 µs high |

| Effluent ultrasonic | ECHO | 2 | in | `pulseIn(..., HIGH, 25000)` — 25 ms timeout |

| pH probe | analogue out | 13 | in (ADC2) | `ADC_11db` attenuation, 12-bit |

| Turbidity probe | analogue out | 14 | in (ADC2) | `ADC_11db`, 12-bit |

| EC probe | analogue out | 12 | in (ADC2) | `ADC_11db`, 12-bit |

| Submerged DS18B20 | 1-Wire data | 27 | 1-Wire | 10-bit resolution |

| DHT11 | data | 5 | in | `DHTTYPE DHT11` |

| UART1 | RX (from N3) | 25 | in | 9600 8N1 |

| UART1 | TX | 26 | out | Declared; the current source does not write upstream |

| UART2 | RX (from controller) | 32 | in | Commented `// To Controller (Mega)` |

| UART2 | TX (to controller) | 33 | out | Cluster packet to the Mega |

| LCD (I²C) | SDA | 21 | — | `Wire.begin(21, 22)` |

| LCD (I²C) | SCL | 22 | — | `LiquidCrystal_I2C lcdN4(0x27, 16, 4)` |

!!! danger "ADC2 pins are shared with Wi-Fi — but this variant has no Wi-Fi"

    All three analogue inputs (12, 13, 14) are on **ADC2**. On the ESP32, Wi-Fi

    operation makes ADC2 unusable. `Node4` has no Wi-Fi, so this is fine.

    `Node4_SMTP` **does** use Wi-Fi and still reads ADC2 pins for pH, turbidity

    and EC — an unresolved conflict in the committed source. See

    [Node 4 SMTP](node4-smtp.md).

```cpp

--8<-- "assets/snippets/node4-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>pin assignments, ADC constants, tank geometry</code> ·

lines 10–41 · commit <code>db6d9b8</code>
</div>

### ADC configuration

| Setting | Value | Note |

|---|---|---|

| Resolution | 12-bit | `analogReadResolution(12)` |

| Attenuation | `ADC_11db` | Largest practical input range |

| `ADC_SAMPLES` | 16 | Averaged per read |

| Settling | 1 discarded sample + 100 µs, then 150 µs between samples | Reduces channel-to-channel residue |

| Voltage conversion | `analogReadMilliVolts()` averaged over `ADC_SAMPLES` | Calibration-aware where supported |

| `ADC_RESOLUTION` | 4095.0 | Divisor used by the legacy helper |

| Tank constant | Value |

|---|---|

| `TANK_HEIGHT` | 178.0 cm |

| `TANK_RADIUS` | 59.5 cm |

| Ultrasonic timeout | 25000 µs |

## Power

> **Supply voltage and current draw are NOT verified from the current source.**

> No supply rail, regulator part number, current budget, enclosure wiring or

> schematic is present in the repository.

What the firmware states explicitly, in a comment above the ADC constants:

```text

ESP32 ADC is NOT a true 0-5V ADC.

The sensor boards may be powered from 5V, but their analog

output must remain within the ESP32 ADC input range.

```

Practical consequences for field work:

* The pH, turbidity and EC **probe boards may be powered from 5 V**, but their

  analogue outputs must stay inside the ESP32 ADC input range.

* The controller's own logic domain is 3.3 V. The validity gates (0.00 V to

  3.30 V on all three analogue channels) are consistent with that ceiling.

* The DS18B20, DHT11, HC-SR04, LCD and both UART links are 3.3 V logic

  peripherals.

* Never connect a 5 V push-pull signal directly to GPIO 12, 13 or 14.

See [Power](../hardware/power.md).

## Communication

| Aspect | Detail |

|---|---|

| Upstream | Node 3, UART1, GPIO 25 RX |

| Downstream | Controller (Arduino Mega), UART2, GPIO 33 TX; GPIO 32 RX is opened but the current source reads nothing from it |

| Protocol | Delimiter-separated ASCII key/value |

| Baud | 9600, `SERIAL_8N1` (`INTERNODE_BAUD`) |

| Frame | `<cleaned upstream>\|pH:%.1f\|Turb:%d\|EC:%.0f\|TCV:%d\|node4:1;` |

| Timing / cadence | Sensor task 1000 ms; UART task 50 ms; LCD task 500 ms; DHT11 paced to ≥ 2000 ms |

| Receive buffer | `char rxBuffer[384]`; assembled packet `static char fullPacket[512]` |

| Frame detection | Character `;` terminates; `\n` and `\r` are skipped |

| Integrity | **No checksum, no CRC, no sequence number, no acknowledgement, no retry.** Any frame ending in `;` is accepted and appended to — Node 4 does **not** validate the upstream structure the way Node 3 does |

| Response time | Node 4 forwards each upstream frame as it arrives; it does not re-time the chain |

### Failure behaviour

* **Buffer overflow.** The RX index resets to 0 and the frame is dropped.

* **Invalid local sensor.** The corresponding downstream field is sent as `0`

  (or `0.0`); `node4` is still `1`.

* **No upstream frame.** Node 4 sends nothing. There is no timeout fallback on

  this node — unlike Node 3.

* **Full-packet truncation.** `fullPacket` is 512 bytes and the cleaned upstream

  frame plus Node 4's fields is comfortably under that, but `snprintf` would

  silently truncate a pathologically long upstream frame.

* **Mutex timeout.** 50 ms for sensor commit, 20 ms for the UART and LCD

  snapshots. A timeout means a stale snapshot is used.

* **Fatal trap.** `[FATAL ERROR] Node 4 Task Failed: <name>` then delays

  forever.

## RTOS Architecture

| Task name | Function | Stack | Priority | Core | Period |

|---|---|---|---|---|---|

| `N4_Sensors` | `Task_Sensors_Node4` | 4096 | 2 | 1 | 1000 ms (`vTaskDelayUntil`) |

| `N4_UART` | `Task_UART_Node4` | 4096 | 3 | 0 | 50 ms (`vTaskDelayUntil`) |

| `N4_LCD` | `Task_LCD_Node4` | 3072 | 1 | 1 | 500 ms (`vTaskDelayUntil`) |

Mutex: **`xLocalN4Mutex`** protecting `g_localN4`, which holds pH, NTU, EC,

submerged temperature, ambient temperature, ambient humidity, TCV volume and

their seven validity flags.

| Lock | Timeout | Where |

|---|---|---|

| Sensor commit | 50 ms | End of `Task_Sensors_Node4` |

| Sensor read (carry-over snapshot) | 50 ms | Start of `Task_Sensors_Node4` |

| UART snapshot | 20 ms | `Task_UART_Node4` |

| LCD snapshot | 20 ms | `Task_LCD_Node4` |

As on Node 2, the task copies the previous state under the mutex at the top of

each cycle, so a value that was valid in cycle *n−1* survives a failure in

cycle *n* — only the validity flag is cleared.

The UART task also handles the calibration console, so **console commands are

serviced every 50 ms** and a `STATUS` command blocks that task while it performs

its multi-sample ADC reads:

```cpp

--8<-- "assets/snippets/node4-uart-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_UART_Node4</code> ·

lines 996–1181 · commit <code>db6d9b8</code>
</div>

## Firmware

### The PC serial calibration console

This is Node 4's most useful field feature. Connect a terminal at **115200 baud**

on the debug UART. Commands are **case-insensitive** and **newline-terminated**.

| Command | Effect |

|---|---|

| `HELP` | Lists the commands |

| `STATUS` | Prints live raw ADC counts and millivolts for pH, EC and turbidity, plus the three saved constants |

| `SET:EC_K=<val>` | Sets and persists `ecKFactor` in NVS `node4_cal`; **rejects values ≤ 0** |

| `SET:PH_S=<val>` | Sets and persists `phSlope` |

| `SET:PH_O=<val>` | Sets and persists `phOffset` |

| `RESET` | Clears the `node4_cal` namespace and reloads the factory defaults |

```cpp

--8<-- "assets/snippets/node4-calibration-console.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>handleSerialCalibrationCommands</code> ·

lines 717–931 · commit <code>db6d9b8</code>
</div>

### Turbidity: the source corrects a real legacy error

```cpp

--8<-- "assets/snippets/node4-turbidity-processing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>turbidity processing</code> ·

lines 511–582 · commit <code>db6d9b8</code>
</div>

The source carries this engineering note verbatim:

> **SEN0189 / DFRobot turbidity relationship. IMPORTANT: The original code used

> 5.0 V as the ADC reference. That is incorrect for the ESP32 ADC measurement.

> The voltage here is the actual voltage measured at the ESP32 ADC input.**

Piecewise conversion, in the ESP32 pin-voltage domain:

| Condition | Result |

|---|---|

| `V >= 3.20` | `0` NTU — very clear water / near the top of the sensor range |

| `V <= 0.50` | `3000` NTU — extremely turbid / below the useful formula range |

| otherwise | `-1120.4 V² + 5742.3 V - 4353.8`, clamped to `[0, 3000]` |

Validity: `0.00 <= V <= 3.30`. Saturation at either end is **deliberately not

invalidated** — the source comment states that saturation is a valid physical

condition.

!!! note "Manufacturer curve, and its domain"

    The quadratic is the SEN0189 / DFRobot relationship. That relationship is a

    manufacturer specification and normally assumes the module's own 5 V output

    range; the source applies it to the ESP32 pin voltage instead. **The mapping

    between the two has not been verified** in this repository. Treat absolute

    NTU values as unverified until checked against a known turbidity standard.

    See [Turbidity](../sensors/turbidity.md) and

    [Turbidity Calibration](../calibration/turbidity.md).

### pH and EC processing

```cpp

--8<-- "assets/snippets/node4-ph-processing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>pH processing</code> ·

lines 458–509 · commit <code>db6d9b8</code>
</div>

```cpp

--8<-- "assets/snippets/node4-ec-processing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>EC processing</code> ·

lines 584–635 · commit <code>db6d9b8</code>
</div>

The three formulas as implemented:

```text

pHcalculated = phSlope × Vph + phOffset

pH           = 7.0 + ((pHcalculated − 7.0) / (1.0 + 0.02 × (T − 25.0)))

                T = submerged DS18B20, else 25.0

EC (µS/cm)   = (V × ecKFactor) / (1.0 + 0.0185 × (T − 25.0)) × 1000,  clamped ≥ 0

```

Validity gates:

| Channel | Valid when |

|---|---|

| pH | `0.02 <= Vph <= 3.30` **and** `0.0 <= pH <= 14.0` |

| Turbidity | `0.0 <= Vt <= 3.30` (range-end saturation accepted) |

| EC | `0.0 <= Vec <= 3.30` — **zero EC is accepted as legitimate** |

| Ambient temperature | `!isnan` **and** `-20 <= T <= 80` °C |

| Ambient humidity | `!isnan` **and** `0 <= RH <= 100` % |

| Effluent volume | `pulseIn` > 0 **and** `0 <= distance <= TANK_HEIGHT + 20` cm |

## Sensors

| Page | Sensor | Used by Node 4 |

|---|---|---|

| [pH](../sensors/ph.md) | Analogue pH probe, ADC2 | **Yes** |

| [Turbidity](../sensors/turbidity.md) | SEN0189 / DFRobot analogue | **Yes** |

| [Conductivity (EC)](../sensors/conductivity.md) | Analogue EC probe, ADC2 | **Yes** |

| [Water Temperature (DS18B20)](../sensors/temperature.md) | DS18B20, submerged, 10-bit | **Yes** — supplies temperature compensation |

| [Humidity / Ambient (DHT11)](../sensors/humidity.md) | DHT11 | **Yes** |

| [Ultrasonic (HC-SR04)](../sensors/ultrasonic.md) | HC-SR04 | **Yes** — effluent level (TCV) |

| [Dissolved Oxygen](../sensors/dissolved-oxygen.md) | Analogue DO probe | No — Node 2 measures DO |

| [Flow](../sensors/flow.md) | Pulse flow meter | No — Node 3 measures flow |

### The blocking DS18B20 is intentional

```cpp

sensorsN4.setResolution(10);

sensorsN4.setWaitForConversion(true);

```

The source comment states that at 10-bit resolution the conversion takes

approximately **187.5 ms**, "which is completely acceptable because the sensor

task runs at 1 Hz". Node 4 therefore blocks for roughly a fifth of each cycle —

**by design**, unlike Node 2's non-blocking pipeline. At boot, `setup()` prints

the device count and warns if `getDeviceCount() == 0`:

```text

[DS18B20] Devices found: N

[DS18B20] WARNING: No temperature sensor detected!

```

## Calibration

All three calibration constants live in the ESP32 NVS namespace **`node4_cal`**

and can be changed at runtime from the serial console.

| Key | Default (this firmware) | Effect |

|---|---|---|

| `phSlope` | `3.5f` | pH volts → pH slope |

| `phOffset` | `-1.75f` | pH volts → pH offset |

| `ecKFactor` | `9.997f` | EC volts → EC K-factor |

```cpp

--8<-- "assets/snippets/node4-load-calibration.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>loadCalibration</code> ·

lines 132–156 · commit <code>db6d9b8</code>
</div>

!!! danger "The defaults are not a calibration"

    `phSlope = 3.5` and `phOffset = -1.75` are **fallback values written into

    the sketch**, not the result of any documented buffer procedure. Likewise

    `ecKFactor = 9.997`. If you see a pH of 7.00 with these defaults, that is a

    consequence of the arithmetic, not evidence that the probe is calibrated.

!!! warning "The SMTP variant has different defaults"

    `Node4_SMTP` defaults to `phOffset 0.0` and `ecKFactor 2.0`. Both firmwares

    read the **same** NVS namespace `node4_cal`, so flashing one variant onto a

    board that was calibrated for the other will silently apply the wrong

    constants. Record which variant each board runs before you calibrate.

### Field calibration procedure

1. Connect a terminal at 115200 baud and send `STATUS`. Record the raw ADC count

   and voltage for each of pH, EC and turbidity with the probes in a known

   solution.

2. For **pH**, take at least two points (pH 4 and pH 7 buffer solutions) and solve

   for slope and offset against the measured voltages. Enter them with

   `SET:PH_S=` and `SET:PH_O=`. Confirm with `STATUS` and with the LCD.

3. For **EC**, take one point against a known standard, compute

   `ecKFactor = EC_standard / V_measured`, and enter it with `SET:EC_K=`. The

   console rejects values ≤ 0.

4. For **turbidity**, the firmware has **no adjustable constant**. Compare the

   reported NTU against a known standard; if it does not agree, no field change

   can correct it without a source edit.

5. Send `RESET` to return to the defaults if the constants are ever in doubt.

Detailed procedures: [pH Calibration](../calibration/ph.md) ·

[Turbidity Calibration](../calibration/turbidity.md) ·

[Conductivity Calibration](../calibration/conductivity.md) ·

[Ultrasonic Calibration](../calibration/ultrasonic.md).

## Display / UI

16×4 character LCD over I²C at address `0x27`, refreshed every 500 ms by

`N4_LCD` (core 1).

Rows are written by directly commanding HD44780 DDRAM addresses — `lcdSetRow()`

issues `0x80 | addr` with `addr` from `{0x00, 0x40, 0x10, 0x50}`.

| Row | DDRAM address | Format string | Shown as |

|---|---|---|---|

| 0 | `0x00` | `EV:%dL pH:%.1f` | effluent volume in litres, pH to one decimal |

| 1 | `0x10` | `TU:%d EC:%duS` | turbidity in NTU, EC in **µS/cm** |

| 2 | `0x40` | `ST:%.1fC AT:%.1fC` | submerged temperature, ambient temperature |

| 3 | `0x50` | `AH:%.0f%%` | ambient humidity, no decimals |

Notes:

* There is **no status or error line** on Node 4. Unlike

  [Node 1](node1.md), it cannot tell you the link is down.

* The values printed are the raw snapshot values. When a channel is **invalid**,

  the last stored numeric value is still shown — the LCD has no invalid marker,

  so a stale number looks like a live one.

* The SMTP variant prints the same rows but with `EC:%.1fmS` on row 1.

* Row 0 uses the label `EV` even in this firmware, while the downstream frame

  field is named `TCV`.

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

### The debug UART is the real diagnostic surface

`Task_UART_Node4` prints a transaction block for **every** forwarded frame:

```text

================ [NODE 4 PACKET TRANSACTION] ================

[INCOMING] Raw Packet from Upstream: ...;

[CLEANED] Upstream Packet: ...

[LOCAL SENSORS] Current Node 4 Readings:

  - pH:       7.1 (Valid: YES)

  - Turbidity:120 NTU (Valid: YES)

  - EC:       850 uS/cm (Valid: YES)

  - TCV Volume:1120 L (Valid: YES)

[OUTGOING] Final Packet Sent Downstream: ...

=============================================================

```

This block gives you, per frame, the validity of every local sensor — which is

the only place `node4` health is actually expressed.

## Troubleshooting

| Symptom | Likely cause | Check | Action |

|---|---|---|---|

| LCD blank | I²C wiring, or the display is not at `0x27` | SDA GPIO 21, SCL GPIO 22 | Re-seat the cable; if the address differs, the sketch must change |

| LCD shows values but they never change | Snapshot taken but sensors dead | Send `STATUS` on the debug UART | Compare live ADC counts with the LCD |

| LCD shows a stale value for a failed sensor | The LCD prints numbers, never validity flags | `STATUS`, or the `[LOCAL SENSORS]` block with `Valid: NO` | Repair the sensor; the LCD cannot tell you |

| `pH` reads 0.0 downstream | `phValid` false: `V < 0.02` or `V > 3.30`, or the computed pH is outside 0–14 | `STATUS` — check the pH raw count and volts | Check the probe's supply, its BNC/board connection and the calibration constants |

| `pH` reads a constant 7.0 | The temperature compensation term is collapsing toward unity, or the defaults happen to produce 7.0 | Check submerged `ST`; if the DS18B20 is invalid, 25.0 °C is assumed | Repair the 1-Wire probe on GPIO 27 so compensation is real |

| `pH` drifts with temperature | Compensation uses `0.02 × (T − 25)`, a fixed coefficient | Compare pH at two water temperatures | Acceptable for a coarse correction; see [pH Calibration](../calibration/ph.md) |

| `Turb` stuck at `0` | `V >= 3.20` — probe saturated on the clear side | `STATUS`: check the turbidity voltage | Check the probe's orientation, its supply and clean the lens |

| `Turb` stuck at `3000` | `V <= 0.50` — below the useful formula range | `STATUS` | Clean the lens; check for an obstructed or disconnected probe |

| `Turb` NTU disagrees with a known standard | Manufacturer curve applied to ESP32 pin voltage | Compare with a turbidity standard | No field correction exists; see [Turbidity Calibration](../calibration/turbidity.md) |

| `EC` reads exactly `0` and `Valid: YES` | Zero EC is accepted as legitimate by design | `STATUS`: check the EC voltage | Distinguish "genuinely zero" from "probe disconnected" with a meter |

| `EC` reads 0 downstream | `ecValid` false: `V > 3.30` | `STATUS` | Check the probe supply and the K-factor |

| `EC` implausible (thousands of µS/cm) | `ecKFactor` mis-set, or the temperature compensation coefficient is off | `STATUS` shows the saved K | Recalibrate with `SET:EC_K=` |

| `TCV` reads `0` | `readTankVolume` rejected: timeout at 25 ms, or distance outside `[0, 198]` cm | Check TRIG GPIO 4 and ECHO GPIO 2 | Repair the ultrasonic head; clean the face |

| `TCV` plausible but wrong | Tank geometry never verified | Measure the real effluent tank | See [Ultrasonic Calibration](../calibration/ultrasonic.md) |

| Controller sees no frame at all | No upstream frame — Node 4 has no fallback of its own | Node 3 page: is Node 3 forwarding? | Fix the link upstream |

| Controller frame has no `AT`/`AH` | `cleanUpstreamPacket` strips them, and Node 4 does not re-add its own | Read the `[CLEANED]` line in the debug output | Expected behaviour, not a fault |

| Controller frame has two `AT`/`AH` pairs | An older Node 4 firmware without the cleaner | Compare with commit `db6d9b8` | Reflash |

| Debug UART floods with transaction blocks | Expected: one block per upstream frame, i.e. ~20 Hz while Node 2 transmits | — | Close the port; use `STATUS` on demand instead |

| `STATUS` command is slow to answer | It performs multi-sample ADC reads inside the 50 ms UART task | — | Expected; allow a second |

| `SET:EC_K=0` rejected | The console rejects values ≤ 0 | — | Enter a positive K-factor |

| Calibration lost after a power cycle | NVS should persist — check the namespace was not cleared | Send `RESET` intentionally? | If values vanish unexpectedly, the NVS partition may be corrupt; reflash |

| Fatal trap on the debug UART | Mutex or task creation failure | — | The node is dead by design; reflash |

## Validation

1. **Boot banners.** At power-up on the debug UART you should see, in order:

   ```text

   --- Loaded Calibration Constants ---

   pH Slope: 3.500 | pH Offset: -1.750 | EC K-Factor: 9.997

   [ADC] Resolution: 12-bit

   [ADC] Attenuation: 11 dB

   [ADC] Multi-sample filtering enabled

   [DS18B20] Devices found: 1

   [DHT11] Initialized

   ```

   A `[DS18B20] WARNING: No temperature sensor detected!` line means the 1-Wire

   probe is absent and **both** pH and EC temperature compensation are falling

   back to 25.0 °C.

2. **Calibration console.** Send `HELP`, then `STATUS`. Confirm three channels

   report with sensible counts in 0–4095 and voltages in 0–3.30 V. Move a

   calibrated probe into a different solution and confirm the voltage changes.

3. **Per-sensor validity.** For each of the seven channels, force a failure by

   disconnecting the sensor (or blocking the ultrasonic face) and confirm the

   `[LOCAL SENSORS]` block flips that channel to `Valid: NO` while the others

   stay `YES`. The downstream field must become `0`.

4. **Round-trip the frame.** Capture the Node 3 → Node 4 link at 9600 baud and

   the Node 4 → controller link at 9600 baud. Confirm the downstream frame is

   the upstream frame with `AT:` and `AH:` removed and

   `|pH:…|Turb:…|EC:…|TCV:…|node4:1;` appended.

5. **LCD versus frame.** Every value on the LCD must match the corresponding

   field in the downstream frame within one 500 ms refresh. A persistent

   mismatch means the UART task is reading a stale snapshot — check for mutex

   contention.

6. **Temperature compensation proof.** Change the submerged temperature and

   confirm pH and EC move in the compensated direction even though their raw

   voltages are unchanged.

7. **Ultrasonic rejection test.** Raise the water above the sensor's measurable

   range (distance > 198 cm) and confirm `TCV` becomes invalid rather than

   reporting a negative or implausible volume.

## Source

* Firmware file at the pinned commit:

  [`FreeRTOS_Implementation/Node4/Node4.ino`](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino)

* Directory listing:

  [`FreeRTOS_Implementation/Node4`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4)

* Extracted snippets used on this page:

  [node4-pin-definitions](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L10-L41),

  [node4-load-calibration](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L132-L156),

  [node4-ph-processing](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L458-L509),

  [node4-turbidity-processing](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L511-L582),

  [node4-ec-processing](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L584-L635),

  [node4-calibration-console](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L717-L931),

  [node4-packet-cleaner](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L936-L990),

  [node4-uart-task](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L996-L1181),

  [node4-lcd-task](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L1187-L1259)

* Commit: [`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/commit/db6d9b896341a9c7d8fd01913e854b663c110d55)

* Firmware Source Map: [../firmware/source-map.html](../firmware/source-map.md)

* Related: [Node 4 SMTP](node4-smtp.md) ·

  [Node 3](node3.md) ·

  [pH](../sensors/ph.md) ·

  [Turbidity](../sensors/turbidity.md) ·

  [Conductivity](../sensors/conductivity.md) ·

  [RTOS Tasks](../rtos/tasks.md)
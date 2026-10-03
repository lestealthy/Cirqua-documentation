---
title: Startup Checklist
description: An ordered, observable checklist for bringing a CIRQUA node up to a known-good state after power-up, installation or maintenance.
---

# Startup Checklist

Work through this in order after powering a node for the first time, after any sensor
work, or as a routine health check. Each step states what you should **see**, and what
to do if you do not see it.

Claim types used throughout: **Firmware implementation**, **Recommendation**.

!!! warning

    Isolate the power source before opening any enclosure. See the safety admonition on
    the [Field service index](index.md#safety-first).

## Know what "normal" looks like first

**Firmware implementation.** The cadences below come from the FreeRTOS task definitions.
They are what "healthy" looks like, and you are looking for *periodic change*, not
particular values.

| Behaviour | Period | Where |
|---|---|---|
| Node 1 ultrasonic measurement | 500 ms | `N1_Sensors` |
| Node 1 LCD refresh | 500 ms | `N1_LCD` |
| Node 1 transmit to Node 2 | 500 ms | `TX_INTERVAL_MS` |
| Node 2 / Node 3 / Node 4 sensor sampling | **1 Hz** | `N2_Sensors`, `N3_Flow`, `N4_Sensors` |
| Node 4 LCD refresh | 500 ms | `N4_LCD` |
| DHT11 read on all nodes | **at least every 2000 ms** | paced by `xLastDHTTick` |
| Node 4 blocking DS18B20 conversion | ~187.5 ms per cycle at 10-bit | by design, commented in the source |
| Node 2, 3, 4 UART service loop | 50 ms | `N2_UART`, `N3_UART`, `N4_UART` |
| Node 1 UART service loop | 1 ms | `N1_UART` |
| Node 1 link-loss threshold | **3000 ms** (`RX_TIMEOUT_MS`) | LCD status logic |
| Node 3 upstream-silence threshold | 2000 ms (`TIMEOUT_MS`) | Node 3 |

**Recommendation.** For the 1 Hz channels, count changes over about ten seconds. If a
value updates once and then freezes, the task has stalled — see
[Troubleshooting](troubleshooting.md).

**Firmware implementation.** A frame that Node 2 (and later nodes) fail to validate does
not stop the chain, but Node 1 declares `ERROR` on the LCD as soon as **3 seconds** pass
with no Node 2 frame. So a healthy Node 1 shows `STATUS: WAITING` for only a moment
after boot, then leaves `WAITING`.

## The fatal-trap behaviour

**Firmware implementation.** Every node creates its tasks and mutexes in `setup()` and
checks the return values. On failure it calls `systemFatalTrap()`, which prints a single
line on the **debug UART at 115200 baud** and then halts the node:

```text
[FATAL ERROR] System Initialization Failed: <name>. Halted.   ← Node 1 wording
[FATAL ERROR] Node 4 Task Failed: <name>                      ← Nodes 3, 4, 4 SMTP wording
```

**Engineering interpretation.** The trap loop is `while (1) { vTaskDelay(1000 ms); }` — it
idles rather than busy-looping, so the message prints **once** and then the node goes
quiet while still powered. No display task runs, so the LCD will be blank or frozen. If
you see a lit but static LCD and nothing on serial, check for this message.

Triggers include `xTaskCreatePinnedToCore` returning anything other than `pdPASS`, and a
`NULL` from `xSemaphoreCreateMutex()`. Named cases you may see:

| Message name | Node | Meaning |
|---|---|---|
| `Mutex Allocation` | Node 4, SMTP | Could not create `xLocalN4Mutex` |
| `N4_Sensors Task`, `N4_UART Task`, `N4_LCD Task` | Node 4, SMTP | Task creation failed |
| `N4_EmailUART Task` | SMTP | The 5120-byte task could not be created |
| `N1_Sensors Task`, `N1_UART Task`, `N1_LCD Task` | Node 1 | Task creation failed |
| `N2_Sensors Task`, `N2_UART Task` | Node 2 | Task creation failed |
| `N3_Flow Task`, `N3_UART Task` | Node 3 | Task creation failed |

**Recommendation.** If a fatal trap appears, do not attempt in-field recovery by cycling
power repeatedly. Capture the message, then re-flash with
[Firmware: flashing](../firmware/flashing.md) and escalate.

## Checklist

### 1. Visual inspection before power

- [ ] No water ingress, condensation pooling or visible corrosion in the enclosure.
- [ ] No cable with a damaged outer sheath, a chafed section near a gland or a strain
      point that has pulled.
- [ ] Connectors seated and finger-tight. No bare conductor visible.
- [ ] Sensor cables not under tension; the probe is not being used to hold anything up.
- [ ] Ultrasonic transducer face clean and undamaged — no biofilm, mineral deposit or
      condensation inside the housing.
- [ ] No moisture on the pH bulb, the EC cell or the turbidity optical window.
- [ ] Node identity label present and legible. If not, apply one —
      [Node identification](node-identification.md).

### 2. Correct controller and peripherals

- [ ] An **ESP32** is fitted. All four nodes are ESP32; there is no other controller in
      the design.
- [ ] The node is running the firmware build matching its role
      ([Node identification](node-identification.md)).
- [ ] Peripherals present for that node: no display on Nodes 2 and 3; a 16×4 I2C LCD at
      `0x27` on Nodes 1 and 4; the expected analogue modules on Nodes 2 and 4.
- [ ] For Node 4 (either variant): pH on GPIO 13, turbidity on 14, EC on 12.

  **If not:** a missing or misidentified peripheral will not prevent boot. The node will
  start and report invalid or zero values. Go to
  [Troubleshooting](troubleshooting.md) before re-wiring, because the GPIO tables differ
  per node.

### 3. Power-up and the debug UART

- [ ] Apply power.
- [ ] Connect the debug UART and open the terminal at **115200 baud, 8N1**.
- [ ] **On Node 4:** confirm the boot banner `--- Loaded Calibration Constants ---` and
      the three values on one line (`pH Slope`, `pH Offset`, `EC K-Factor`).

  **If not:** no banner means either this is not Node 4, or `setup()` never ran far
  enough. Look for `[FATAL ERROR]`. See [Troubleshooting](troubleshooting.md).

- [ ] **On every node:** confirm no `[FATAL ERROR]` line appears. The message prints only
      once; a silent terminal after that is consistent with a halted node.
- [ ] **On Node 4:** send `HELP` and confirm the banner and command list return.

  ```text
  ========== NODE 4 CALIBRATION DEBUG CONSOLE ==========
  STATUS        - View current raw ADC and calculated values
  SET:EC_K=<val>- Set and save EC K factor
  SET:PH_S=<val>- Set and save pH slope
  SET:PH_O=<val>- Set and save pH offset
  RESET         - Reset calibration to factory defaults
  =====================================================
  ```

  **If not:** confirm the baud rate, confirm the correct node, and confirm the USB cable
  is a data cable. Do not send `RESET` — it clears the pH and EC calibration from NVS.

- [ ] **On Node 4:** send `STATUS` and confirm all three analogue channels report a raw
      ADC count and a voltage.

  ```text
  --- Live Raw Sensor Diagnostics ---
  pH   -> Raw ADC:    0 | Voltage: 0.000V
  EC   -> Raw ADC:    0 | Voltage: 0.000V | K: 9.997
  Turb -> Raw ADC:    0 | Voltage: 0.000V
  Saved Constants -> pH Slope: 3.500 | pH Offset: -1.750 | EC K: 9.997
  ```

  Raw counts of `0` with `0.000 V` on all three channels point at a common supply or
  ground problem, not three failed sensors.

### 4. Node 1 — display and link

- [ ] The LCD is **backlit** and all four rows are populated. A blank or all-blank LCD
      with no serial error points at the I2C connection (SDA GPIO 21, SCL GPIO 22) or the
      backlight, not at the sensors.
- [ ] Row 1 shows the `C…L F…L` pattern; row 4 shows `STATUS: …`.
- [ ] Row 4 briefly shows `STATUS: WAITING`, then leaves `WAITING` within a few seconds
      once Node 2 is transmitting.
- [ ] Row 4 then shows `STATUS: NORMAL` for a healthy installation.

  **If not:** the status word is a complete diagnostic in itself. Use the status
  precedence table in [Troubleshooting](troubleshooting.md#node-1-status-word).

- [ ] `F…L` no longer shows `----`, and the `DO`, `T` and `AT`/`H` fields no longer show
  `--` or `--`/`----` placeholders.

  **If not:** the placeholders mean the field was absent or invalid in the last received
  frame. Persistent placeholders point upstream at Node 2 — see
  [Troubleshooting](troubleshooting.md).

- [ ] The `C…L` value changes plausibly with level, at roughly 2 Hz refresh.

### 5. Node 4 — display and console

- [ ] The LCD is backlit and shows the four Node 4 rows: `EV:…L pH:…`,
  `TU:… EC:…uS`, `ST:…C AT:…C`, `AH:…%`.
- [ ] `EC:` is followed by `uS` on `Node4` or `mS` on `Node4_SMTP`. **This is how you
      confirm which variant is running.**
- [ ] Values change approximately once per second.

  **If not:** values are changing but read zero, see
  [Troubleshooting: Node 4 display reads zero](troubleshooting.md#node-4-display-reads-zero).
  The Node 4 LCD prints stored values **without checking the validity flags**, so a
  confidently displayed `0` does not prove the channel is healthy.

### 6. Node 3 — no display expected

- [ ] Confirm **no LCD is fitted** and none is required. A blank or absent display on
      Node 3 is correct, not a fault.
- [ ] Confirm the flow sensor is wired to GPIO 23 and the pulse input behaves. There is
      **no local indication of flow on Node 3**; the value only appears in `FLM:` in the
      frame travelling downstream, and reaches Node 1's LCD only if Node 2, Node 3 and
      Node 4 all forward it.
- [ ] Confirm `FLM:` is present in the downstream frame.

  **If not:** see [Troubleshooting](troubleshooting.md).

### 7. Link and cadence confirmation

- [ ] With the whole chain powered, confirm Node 1 leaves `WAITING`.
- [ ] Confirm no node shows `ERROR`. If Node 1 shows `ERROR` for more than 3 seconds, the
      link has failed — work through
      [No data on the link](troubleshooting.md#no-data-on-the-link).
- [ ] Confirm sensor values are updating on a 1 Hz cadence rather than frozen.
- [ ] Confirm the controller at the end of the chain receives a frame containing the
      expected field set for the running Node 4 variant.

### 8. Post-calibration checks (only if calibration was touched)

- [ ] After any `SET:` command, send `STATUS` and record the stored constants.
- [ ] **Power-cycle** the node and send `STATUS` again — the pH and EC constants must be
      unchanged. They live in NVS namespace `node4_cal`.
- [ ] Confirm the `EC` unit suffix still matches the running variant after the reboot.
- [ ] If any ultrasonic geometry or Node 1 volume factor was changed, re-run
      [Ultrasonic calibration](../calibration/ultrasonic.md#step-by-step-verification-procedure).

### 9. Record

- [ ] Log the date, node, firmware variant, calibration constants in force, and every
      observed value in the maintenance log table
      ([Maintenance](maintenance.md)).
- [ ] Record anything you could not verify. The repository publishes no schematics, no
      enclosure data and no maintenance schedule, so field observations are the only
      record that will exist.

## Related pages

- [Field service index](index.md)
- [Node identification](node-identification.md)
- [Troubleshooting](troubleshooting.md)
- [Sensor replacement](sensor-replacement.md)
- [RTOS: tasks](../rtos/tasks.md)
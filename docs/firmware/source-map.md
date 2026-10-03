---

title: Firmware Source Map

description: Reverse index from documentation topic to node, firmware file, function or symbol and a permalink at commit db6d9b8, plus the extractable snippet id.

---

# Firmware Source Map

This is the maintainability index for the CIRQUA firmware. It answers one

question in the form a maintainer actually asks it: *"I want to change or verify

X — which node, which file, which function, which lines?"*

The map is bidirectional in spirit: the [global table](#global-index) is indexed

by symbol, and the per-node tables are indexed by engineering concern. Every row

carries a permalink pinned to commit

[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55),

so a link in a ticket resolves to exactly the lines described.

The machine-readable version of this table is

[`docs/assets/snippets/snippet-index.yml`](../assets/snippets/snippet-index.yml),

regenerated from the firmware by

`scripts/extract_code_snippets.py`. It records, for all **41** snippets: `id`,

`label`, `symbol`, `path`, `start_line`, `end_line`, `line_count`, `status`,

`commit` and `source_url`. If this page and that file ever disagree, the file is

authoritative — it is generated, this page is written.

## Reading the tables

| Column | Meaning |

|---|---|

| Concern | The engineering topic, phrased as this documentation set uses it |

| Function / symbol | Identifier as it appears in the source, or the `#define`/global name |

| Lines | Inclusive 1-based line range at commit `db6d9b8` |

| Snippet id | Embeddable file in `docs/assets/snippets/`, or `—` if not extracted |

| Link | Permalink into the firmware at that commit |

Line ranges are the extraction ranges where a snippet exists, so they are

guaranteed to match the embedded code exactly. Where a symbol is listed without

a snippet, the range is the function body as read from the source.

## Global index

| Node | File | Concern | Function / symbol | Lines | Snippet id |

|---|---|---|---|---|---|

| 1 | `Node1.ino` | Pins, tank geometry, alert thresholds | `PIN_N1_TRIG` … `TX_INTERVAL_MS` | 5–35 | `node1-pin-definitions` |

| 1 | `Node1.ino` | Ultrasonic acquisition | `Task_Sensors_Node1` | 77–116 | `node1-ultrasonic-measurement` |

| 1 | `Node1.ino` | Frame field extraction | `getFieldFromFrame` | 120–132 | `node1-frame-parser` |

| 1 | `Node1.ino` | Reverse telemetry commit | `processNode2Packet` | 133–157 | `node1-packet-processing` |

| 1 | `Node1.ino` | Bidirectional UART task | `Task_UART_Node1` | 161–204 | `node1-uart-task` |

| 1 | `Node1.ino` | LCD row writer | `printLCDLine` | 209–219 | — |

| 1 | `Node1.ino` | LCD render and status string | `Task_LCD_Node1` | 220–310 | `node1-lcd-task` |

| 1 | `Node1.ino` | Fatal trap | `systemFatalTrap` | 68–73 | — |

| 1 | `Node1.ino` | Task creation | `setup` | 314–335 | `node1-setup` |

| 2 | `Node2.ino` | Pins, DO constants, tank geometry | `PIN_DS18B20` … `TANK_RADIUS` | 10–32 | `node2-pin-definitions` |

| 2 | `Node2.ino` | DS18B20 + DO + TBV + DHT11 acquisition | `Task_Sensors_Node2` | 98–220 | `node2-sensor-task` |

| 2 | `Node2.ino` | Upstream parser | `parseNode1Packet` | 225–239 | `node2-parse-node1` |

| 2 | `Node2.ino` | Reverse telemetry parser | `parseNode3ReversePacket` | 240–254 | `node2-parse-node3` |

| 2 | `Node2.ino` | Routing, consolidation, echo | `Task_UART_Node2` | 259–370 | `node2-uart-routing` |

| 2 | `Node2.ino` | Fatal trap | `systemFatalTrap` | 88–93 | — |

| 2 | `Node2.ino` | Task creation | `setup` | 375–394 | `node2-setup` |

| 3 | `Node3.ino` | Pins and flow constant | `PIN_FLOW_SENSOR` … `TIMEOUT_MS` | 3–13 | `node3-pin-definitions` |

| 3 | `Node3.ino` | Pulse counter and ISR | `g_pulseCount`, `g_pulseMux`, `pulseISR` | 15–23 | `node3-pulse-isr` |

| 3 | `Node3.ino` | 1 Hz flow computation | `Task_Flow_Node3` | 43–69 | `node3-flow-task` |

| 3 | `Node3.ino` | Frame integrity check | `validateUpstreamFrame` | 71–78 | `node3-frame-validation` |

| 3 | `Node3.ino` | Forwarding and timeout fallback | `Task_UART_Node3` | 82–154 | `node3-uart-forwarding` |

| 3 | `Node3.ino` | Fatal trap | `systemFatalTrap` | 36–39 | — |

| 3 | `Node3.ino` | Task creation | `setup` | 158–170 | `node3-setup` |

| 4 | `Node4.ino` | Pins, ADC constants, tank geometry | `PIN_EFFLUENT_TRIG` … `TANK_RADIUS` | 10–41 | `node4-pin-definitions` |

| 4 | `Node4.ino` | Fatal trap | `systemFatalTrap` | 104–110 | — |

| 4 | `Node4.ino` | LCD row addressing | `lcdSetRow` | 116–127 | — |

| 4 | `Node4.ino` | NVS calibration declaration | `Preferences`, `CalibrationData`, `calData` | 53–66 | `node4-calibration-struct` |

| 4 | `Node4.ino` | Calibration load and banner | `loadCalibration` | 132–156 | `node4-load-calibration` |

| 4 | `Node4.ino` | Attenuation and resolution | `configureADC` | 161–189 | `node4-adc-configuration` |

| 4 | `Node4.ino` | Averaged raw ADC read | `readADCFiltered` | 194–213 | `node4-filtered-adc` |

| 4 | `Node4.ino` | Unused diagnostic converter | `adcToVoltage` | 219–241 | — |

| 4 | `Node4.ino` | Calibrated millivolt acquisition | `readSensorVoltage` | 246–266 | `node4-sensor-voltage` |

| 4 | `Node4.ino` | DS18B20 init and device count | `initializeDS18B20` | 272–297 | — |

| 4 | `Node4.ino` | DHT init | `initializeDHT` | 303–308 | — |

| 4 | `Node4.ino` | Effluent volume with range rejection | `readTankVolume` | 313–368 | `node4-tank-volume` |

| 4 | `Node4.ino` | Full sampling cycle | `Task_Sensors_Node4` | 374–712 | `node4-sensor-task` |

| 4 | `Node4.ino` | Serial calibration console | `handleSerialCalibrationCommands` | 717–931 | `node4-calibration-console` |

| 4 | `Node4.ino` | Upstream packet cleaner | `cleanUpstreamPacket` | 936–990 | `node4-packet-cleaner` |

| 4 | `Node4.ino` | UART, transaction log, packet assembly | `Task_UART_Node4` | 996–1181 | `node4-uart-task` |

| 4 | `Node4.ino` | LCD render | `Task_LCD_Node4` | 1187–1259 | `node4-lcd-task` |

| 4 | `Node4.ino` | Task creation | `setup` | 1264–1336 | `node4-setup` |

| 4 SMTP | `Node4_SMTP.ino` | Network and SMTP macros (placeholders) | `WIFI_SSID` … `RECIPIENT_EMAIL` | 11–24 | `node4-smtp-network-config` |

| 4 SMTP | `Node4_SMTP.ino` | Calibration load (**no banner**) | `loadCalibration` | 99–105 | — |

| 4 SMTP | `Node4_SMTP.ino` | Wi-Fi association and NTP sync | `initNetworkAndTime` | 107–136 | `node4-smtp-init-network` |

| 4 SMTP | `Node4_SMTP.ino` | SMTP session and dispatch | `sendMailMessage` | 138–171 | `node4-smtp-send-mail` |

| 4 SMTP | `Node4_SMTP.ino` | Sensor sampling, single-file form | `Task_Sensors_Node4` | 176–270 | — |

| 4 SMTP | `Node4_SMTP.ino` | Heartbeat, fault alert, UART forwarding | `Task_Email_And_UART_Node4` | 275–390 | `node4-smtp-alert-logic` (301–350) |

| 4 SMTP | `Node4_SMTP.ino` | LCD render (mS variant) | `Task_LCD_Node4` | 395–424 | — |

| 4 SMTP | `Node4_SMTP.ino` | Task creation | `setup` | 428–448 | `node4-smtp-setup` |

| Historical | `_OLD/node3_fixed/node3_fixed.ino` | Predecessor ping sketch | — | 1–40 | `legacy-node3-ping` |

## Node 1 — `FreeRTOS_Implementation/Node1/Node1.ino`

[Permalink to the file](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino) ·

339 lines · cluster head · one `HardwareSerial` (UART1) · 16×4 I²C LCD.

| Documentation topic | Function / symbol | Lines | Snippet | Link |

|---|---|---|---|---|

| [GPIO map](../hardware/gpio-map.md)), tank geometry, alert thresholds | `PIN_N1_TRIG`, `PIN_N1_ECHO`, `PIN_N1_UART_RX/TX`, `PIN_LCD_SDA/SCL`, `TANK_HEIGHT`, `TANK_RADIUS`, `TEMP_ALERT_TH`, `HUMID_ALERT_TH`, `TAV_LOW_ALERT_TH`, `TBV_LOW_ALERT_TH`, `RX_TIMEOUT_MS`, `TX_INTERVAL_MS` | 5–35 | `node1-pin-definitions` | [L10](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L10-L18) |

| [Shared data structures](../rtos/queues.md)) | `LocalSensorData`, `Node2Telemetry`, `g_localSensors`, `g_node2Data`, `g_lastNode2Rx` | 40–60 | — | [L40](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L40-L60) |

| Mutexes and peripherals | `xLocalDataMutex`, `xNode2DataMutex`, `lcd`, `NodeSerial` | 62–66 | — | [L62](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L62-L66) |

| [Fatal trap](../validation/known-limitations.md) | `systemFatalTrap` | 68–73 | — | [L68](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L68-L73) |

| [Ultrasonic level](../sensors/ultrasonic.md)), `TAV`, the `×2.0f` factor | `Task_Sensors_Node1` | 77–116 | `node1-ultrasonic-measurement` | [L78](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L78-L116) |

| [Frame parsing](../communication/message-format.md)) | `getFieldFromFrame` | 120–132 | `node1-frame-parser` | [L121](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L121-L132) |

| Reverse telemetry commit, `packetValid` | `processNode2Packet` | 133–157 | `node1-packet-processing` | [L134](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L134-L157) |

| [Transmit cadence](../communication/serial-links.md)), Node 1 → Node 2 frame | `Task_UART_Node1` | 161–204 | `node1-uart-task` | [L162](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L162-L204) |

| LCD 16-column truncation and padding | `printLCDLine` | 209–219 | — | [L209](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L209-L219) |

| [LCD content and the `STATUS:` precedence](../nodes/node1.md#display-ui) | `Task_LCD_Node1` | 220–310 | `node1-lcd-task` | [L221](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L221-L310) |

| [Task table](../rtos/tasks.md)), core pinning, `loop()` reclamation | `setup`, `loop` | 314–339 | `node1-setup` | [L315](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino#L315-L339) |

## Node 2 — `FreeRTOS_Implementation/Node2/Node2.ino`

[Permalink to the file](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino) ·

399 lines · router · two `HardwareSerial` (UART1, UART2) · no display.

| Documentation topic | Function / symbol | Lines | Snippet | Link |

|---|---|---|---|---|

| [GPIO map](../hardware/gpio-map.md)), DO electrical constants, tank geometry | `PIN_DS18B20`, `PIN_DO_ANALOG`, `PIN_N2_TRIG/ECHO`, `PIN_DHT11`, UART pins, `DHTTYPE`, `VREF`, `ADC_RESOLUTION`, `TWO_POINT_VOLTAGE`, `SATURATION_DO_25C`, `TANK_HEIGHT`, `TANK_RADIUS` | 10–32 | `node2-pin-definitions` | [L12](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L12-L32) |

| [Sensor objects](../nodes/node2.md#sensors) | `oneWireN2`, `sensorsN2`, `dhtN2`, `SerialNode1`, `SerialNode3` | 38–43 | — | [L38](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L38-L43) |

| [Telemetry structs](../rtos/queues.md)) | `Node2Sensors`, `Node1Telemetry`, `Node3ReverseTelemetry`, `g_n2Sensors`, `g_n1Data`, `g_n3Data` | 49–77 | — | [L49](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L49-L77) |

| Mutexes | `xSensorsMutex`, `xN1DataMutex`, `xN3DataMutex` | 80–82 | — | [L80](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L80-L82) |

| Fatal trap | `systemFatalTrap` | 88–93 | — | [L88](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L88-L93) |

| [Water temperature](../sensors/temperature.md)) (non-blocking DS18B20), [dissolved oxygen](../sensors/dissolved-oxygen.md)) (two-point + temperature compensation), [TBV level](../sensors/ultrasonic.md)), [DHT11 pacing](../sensors/humidity.md)) | `Task_Sensors_Node2` | 98–220 | `node2-sensor-task` | [L99](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L99-L220) |

| Parsing the `\|TAV:`/`\|node1:` upstream frame | `parseNode1Packet` | 225–239 | `node2-parse-node1` | [L226](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L226-L239) |

| Parsing the reverse telemetry frame (looks for `\|FR:`) | `parseNode3ReversePacket` | 240–254 | `node2-parse-node3` | [L241](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L241-L254) |

| [Frame construction](../communication/message-format.md)): consolidation downstream, echo upstream, health flag | `Task_UART_Node2` | 259–370 | `node2-uart-routing` | [L260](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L260-L370) |

| Task table and mutex allocation | `setup`, `loop` | 375–399 | `node2-setup` | [L376](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino#L376-L399) |

## Node 3 — `FreeRTOS_Implementation/Node3/Node3.ino`

[Permalink to the file](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino) ·

174 lines · the smallest sketch · two `HardwareSerial` · no display.

| Documentation topic | Function / symbol | Lines | Snippet | Link |

|---|---|---|---|---|

| [GPIO map](../hardware/gpio-map.md)), flow constant, upstream timeout | `PIN_FLOW_SENSOR`, `PIN_UP_UART_RX/TX`, `PIN_DOWN_UART_RX/TX`, `FLOW_CAL_FACTOR`, `TIMEOUT_MS` | 3–13 | `node3-pin-definitions` | [L6](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L6-L13) |

| [The ISR](../rtos/tasks.md#n3_flow-task_flow_node3), critical section, `FALLING` edge | `g_pulseCount`, `g_pulseMux`, `pulseISR` | 15–23 | `node3-pulse-isr` | [L16](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L16-L23) |

| Flow data and mutex | `UpstreamSerial`, `DownstreamSerial`, `FlowData`, `g_flowData`, `xFlowMutex` | 25–34 | — | [L25](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L25-L34) |

| Fatal trap | `systemFatalTrap` | 36–39 | — | [L36](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L36-L39) |

| [Flow rate computation](../sensors/flow.md)) and pulse-count reset | `Task_Flow_Node3` | 43–69 | `node3-flow-task` | [L44](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L44-L69) |

| **The only frame-integrity check in the firmware** — presence of `TAV:`, `\|node1:`, `\|DO:`, `\|node2:` | `validateUpstreamFrame` | 71–78 | `node3-frame-validation` | [L72](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L72-L78) |

| [Forwarding, `FLM` append, overflow reset, timeout fallback frame](../communication/fault-handling.md)) | `Task_UART_Node3` | 82–154 | `node3-uart-forwarding` | [L83](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L83-L154) |

| Task table and mutex allocation | `setup`, `loop` | 158–174 | `node3-setup` | [L159](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino#L159-L174) |

## Node 4 — `FreeRTOS_Implementation/Node4/Node4.ino`

[Permalink to the file](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino) ·

1346 lines · cluster tail · two `HardwareSerial` · 16×4 I²C LCD · NVS calibration

· serial calibration console. Note that this file is stored in a heavily

line-broken formatting style (each statement and brace on its own line); the

semantics are unaffected.

| Documentation topic | Function / symbol | Lines | Snippet | Link |

|---|---|---|---|---|

| [GPIO map](../hardware/gpio-map.md)), ADC constants, tank geometry, ADC2 warning | `PIN_EFFLUENT_TRIG/ECHO`, `PIN_PH_ANALOG`, `PIN_TURB_ANALOG`, `PIN_EC_ANALOG`, `PIN_SUB_DS18B20`, `PIN_N4_DHT11`, UART pins, LCD pins, `ADC_RESOLUTION`, `TANK_HEIGHT`, `TANK_RADIUS` | 10–41 | `node4-pin-definitions` | [L13](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L13-L41) |

| Filtering and attenuation constants | `ADC_SAMPLES`, `SENSOR_ADC_ATTENUATION` | 47–52 | — | [L48](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L48-L52) |

| [Calibration storage](../calibration/index.md)) | `Preferences preferences`, `CalibrationData`, `calData` | 53–66 | `node4-calibration-struct` | [L58](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L58-L66) |

| Sensor objects and local data | `oneWireN4`, `sensorsN4`, `dhtN4`, `lcdN4`, `UpstreamSerial`, `DownstreamSerial`, `LocalNode4Data`, `g_localN4`, `xLocalN4Mutex` | 72–98 | — | [L72](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L72-L98) |

| Fatal trap | `systemFatalTrap` | 104–110 | — | [L104](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L104-L110) |

| HD44780 row addressing | `lcdSetRow` | 116–127 | — | [L116](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L116-L127) |

| [Calibration load and the boot banner](../firmware/configuration.md)) | `loadCalibration` | 132–156 | `node4-load-calibration` | [L133](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L133-L156) |

| [ADC attenuation, resolution and boot messages](../sensors/ph.md)) | `configureADC` | 161–189 | `node4-adc-configuration` | [L162](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L162-L189) |

| 16-sample averaging with a discarded first reading | `readADCFiltered` | 194–213 | `node4-filtered-adc` | [L195](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L195-L213) |

| Diagnostic-only converter — computes millivolts, returns a 3.3 V reference value, **not called by the sensor path** | `adcToVoltage` | 219–241 | — | [L219](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L219-L241) |

| Calibrated `analogReadMilliVolts` averaging | `readSensorVoltage` | 246–266 | `node4-sensor-voltage` | [L247](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L247-L266) |

| [Submerged DS18B20](../sensors/temperature.md)): 10-bit, blocking conversion, device count | `initializeDS18B20` | 272–297 | — | [L272](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L272-L297) |

| DHT11 initialisation | `initializeDHT` | 303–308 | — | [L303](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L303-L308) |

| [Effluent volume](../sensors/ultrasonic.md)) and the `TANK_HEIGHT + 20` rejection | `readTankVolume` | 313–368 | `node4-tank-volume` | [L314](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L314-L368) |

| The whole 1 Hz sampling cycle: DS18B20 → pH → turbidity → EC → DHT11 → volume | `Task_Sensors_Node4` | 374–712 | `node4-sensor-task` | [L375](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L375-L712) |

| [pH model, temperature compensation, validity gate](../sensors/ph.md)) | inside `Task_Sensors_Node4` | 458–509 | `node4-ph-processing` | [L458](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L458-L509) |

| [Turbidity NTU mapping, saturation, SEN0189 note](../sensors/turbidity.md)) | inside `Task_Sensors_Node4` | 511–582 | `node4-turbidity-processing` | [L511](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L511-L582) |

| [Conductivity K-factor and temperature compensation](../sensors/conductivity.md)) | inside `Task_Sensors_Node4` | 584–635 | `node4-ec-processing` | [L584](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L584-L635) |

| [The serial calibration console](../firmware/configuration.md)) | `handleSerialCalibrationCommands` | 717–931 | `node4-calibration-console` | [L718](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L718-L931) |

| [Packet cleaner](../communication/message-format.md)): removes upstream `AT:`/`AH:` | `cleanUpstreamPacket` | 936–990 | `node4-packet-cleaner` | [L937](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L937-L990) |

| Node 4 → controller frame assembly, `[NODE 4 PACKET TRANSACTION]` debug block | `Task_UART_Node4` | 996–1181 | `node4-uart-task` | [L997](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L997-L1181) |

| [Node 4 LCD layout](../nodes/node4.md#display-ui) | `Task_LCD_Node4` | 1187–1259 | `node4-lcd-task` | [L1188](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L1188-L1259) |

| Task table, `delay(500)`, mutex allocation | `setup`, `loop` | 1264–1346 | `node4-setup` | [L1265](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino#L1265-L1345) |

### Cross-references inside `Task_Sensors_Node4`

The Node 4 sampling task is one function with six numbered phases. Each phase

is independently citable, which is why the extraction tool splits it:

| Phase | Lines | Feeds |

|---|---|---|

| Snapshot the previous state | 409–425 | — |

| 1. Submerged DS18B20 | 431–456 | pH and EC temperature compensation |

| 2. pH | 462–509 | `pH` field, LCD row 0 |

| 3. Turbidity | 515–582 | `Turb` field, LCD row 1 |

| 4. Conductivity | 588–635 | `EC` field, LCD row 1 |

| 5. DHT11 (paced ≥ 2000 ms) | 641–678 | LCD row 2 and 3 |

| 6. Effluent ultrasonic volume | 684–694 | `TCV` field, LCD row 0 |

| Commit the snapshot | 700–710 | `xLocalN4Mutex` |

## Node 4 SMTP variant — `FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino`

[Permalink to the file](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino) ·

452 lines · cluster tail with alerting. Same GPIO map as Node 4, different

conversion constants, different downstream frame, no calibration console.

| Documentation topic | Function / symbol | Lines | Snippet | Link |

|---|---|---|---|---|

| Wi-Fi and SMTP configuration — **placeholder values only** | `WIFI_SSID`, `WIFI_PASSWORD`, `SMTP_HOST`, `SMTP_PORT`, `AUTHOR_EMAIL`, `AUTHOR_PASSWORD`, `RECIPIENT_EMAIL` | 11–24 | `node4-smtp-network-config` (passwords redacted) | [L16](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L16-L24) |

| [GPIO map](../hardware/gpio-map.md)) (identical to Node 4) | `PIN_EFFLUENT_TRIG/ECHO`, `PIN_PH_ANALOG`, `PIN_TURB_ANALOG`, `PIN_EC_ANALOG`, `PIN_SUB_DS18B20`, `PIN_N4_DHT11`, UART pins, LCD pins | 26–41 | — | [L27](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L27-L41) |

| Variant ADC reference and tank geometry | `ESP32_VREF 3.3f`, `ADC_RESOLUTION`, `TANK_HEIGHT`, `TANK_RADIUS` | 43–49 | — | [L44](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L44-L49) |

| [Calibration defaults — different from `Node4`](../firmware/configuration.md)) | `loadCalibration` | 99–105 | — | [L99](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L99-L105) |

| [Wi-Fi association, NTP, Tunis UTC+1](../nodes/node4-smtp.md)) | `initNetworkAndTime` | 107–136 | `node4-smtp-init-network` | [L108](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L108-L136) |

| [SMTP session, SSL transport, base64 HTML](../nodes/node4-smtp.md)) | `sendMailMessage` | 138–171 | `node4-smtp-send-mail` | [L139](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L139-L171) |

| Sampling, with the variant's 5 V-referenced turbidity path | `Task_Sensors_Node4` | 176–270 | — | [L176](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L176-L270) |

| Startup e-mail, **heartbeat and error cooldown logic** | `Task_Email_And_UART_Node4` | 275–350 | `node4-smtp-alert-logic` | [L275](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L275-L350) |

| Fault e-mail itemisation and UART forwarding | `Task_Email_And_UART_Node4` | 324–390 | — | [L324](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L324-L390) |

| LCD layout with `EC:%.1fmS` | `Task_LCD_Node4` | 395–424 | — | [L395](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L395-L424) |

| Task table, 5120-byte e-mail/UART task | `setup`, `loop` | 428–452 | `node4-smtp-setup` | [L429](https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4_SMTP/Node4_SMTP.ino#L429-L452) |

## Symbols that exist in every sketch

Useful when searching the repository: these names are duplicated per file, so a

`grep` for one will hit up to five places.

| Symbol | Purpose | Variation between files |

|---|---|---|

| `INTERNODE_BAUD` | Link baud rate, `9600` | identical in all five |

| `TANK_HEIGHT`, `TANK_RADIUS` | Ultrasonic cylinder geometry | Node 1 `260.0/110.0`; Nodes 2, 4, 4 SMTP `178.0/59.5` |

| `systemFatalTrap` | Halt the node on allocation or task-creation failure | Message text differs per node |

| `setup`, `loop` | Arduino entry points | `loop()` is `vTaskDelete(NULL)` everywhere |

| `xTaskCreatePinnedToCore` | Task creation | Core 0 for UART/e-mail, core 1 for sensors and LCD |

| `vTaskDelayUntil` | Periodic pacing | 500 ms (Nodes 1, 4 LCD), 1000 ms (sensor tasks), 50 ms (UART tasks), 1 ms (Node 1 UART) |

| `xSemaphoreCreateMutex`, `xSemaphoreTake` | Shared-state protection | Lock timeouts of 50 / 20 / 10 ms |

## Historical symbols

`_OLD/` contains none of the current task names, so a search for

`Task_Sensors_Node1` or `cleanUpstreamPacket` returning nothing under `_OLD/` is

expected, not an error. The only extracted legacy fragment is

`legacy-node3-ping` (`_OLD/node3_fixed/node3_fixed.ino`, lines 1–40), used on

[Legacy Firmware](../historical/legacy-firmware.md)) and always labelled

<span class="cirqua-badge cirqua-badge--historical">historical</span>.

## Related

* [Repository](repository.md)) — the pin and the inventories.

* [Code Reference](code-reference.md)) — the same code read by concern, with

  rationale.

* [RTOS Tasks](../rtos/tasks.md)) — task names, stacks, priorities, cores,

  periods.

* [GPIO Map](../hardware/gpio-map.md)) — the same pins as a wiring reference.

* [Message Format](../communication/message-format.md)) — the same formats as

  the controller sees them.

* [Firmware Validation](../validation/firmware-validation.md) — which of these

  rows have been checked.
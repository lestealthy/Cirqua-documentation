---

title: Controllers

description: The ESP32 controller on every CIRQUA node — dual-core FreeRTOS, two HardwareSerial UARTs, I2C LCD bus, NVS calibration and 12-bit ADC configuration.

---

# Controllers

**Firmware implementation.** Every one of the four nodes — and the SMTP variant

of Node 4 — runs on an **ESP32** programmed as an Arduino `.ino` sketch. The

dual-core FreeRTOS model is used on every node, with each task pinned to a

specific core at creation time.

> **Not verified from the current source.** The exact ESP32 board variant,

> devkit model, module variant and PSRAM configuration. The firmware uses only

> ESP32-family APIs and does not name a specific board.

## What the source proves about the controller

| Property | Evidence in the firmware |

|---|---|

| Dual-core FreeRTOS | `xTaskCreatePinnedToCore` in every `setup()` |

| Two hardware UARTs | `HardwareSerial` instances for UART1 and UART2 on Nodes 2, 3 and 4; Node 1 uses UART1 only |

| I2C for the LCD | `Wire` used on Nodes 1 and 4 for the 16×4 HD44780 backpack at `0x27` |

| Non-volatile calibration | `Preferences.h` (ESP32 NVS) on Node 4, namespaces `node4_cal` and `email_state` |

| 12-bit ADC | `analogReadResolution(12)` and `ADC_11db` attenuation |

| Millivolt reads | `analogReadMilliVolts()` used rather than raw counts |

| Critical sections | `portMUX_TYPE` with `portENTER_CRITICAL` / `portEXIT_CRITICAL` on Node 3 |

| Debug console | `Serial.begin(115200)` |

| Arduino loop reclaimed | `loop()` calls `vTaskDelete(NULL)` |

## Node 1 pin and hardware definition

```cpp

--8<-- "assets/snippets/node1-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node1/Node1.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node1/Node1.ino</code> ·

<code>pin-definitions block</code> ·

lines 5–35 · commit <code>db6d9b8</code>
</div>

## Node 2 pin and hardware definition

```cpp

--8<-- "assets/snippets/node2-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>pin-definitions block</code> ·

lines 10–32 · commit <code>db6d9b8</code>
</div>

## Node 3 pin and hardware definition

```cpp

--8<-- "assets/snippets/node3-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node3/Node3.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node3/Node3.ino</code> ·

<code>pin-definitions block</code> ·

lines 3–13 · commit <code>db6d9b8</code>
</div>

## Node 4 pin and hardware definition

```cpp

--8<-- "assets/snippets/node4-pin-definitions.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>pin-definitions block</code> ·

lines 10–41 · commit <code>db6d9b8</code>
</div>

## ADC configuration

Node 4 configures the analogue front end explicitly.

```cpp

--8<-- "assets/snippets/node4-adc-configuration.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>configureADC</code> ·

lines 161–189 · commit <code>db6d9b8</code>
</div>

Reads are averaged over 16 samples before conversion to millivolts:

```cpp

--8<-- "assets/snippets/node4-filtered-adc.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>readADCFiltered</code> ·

lines 194–213 · commit <code>db6d9b8</code>
</div>

Node 2's dissolved oxygen channel uses `analogReadResolution(12)` with its own

`VREF 5000.0f` and `ADC_RESOLUTION 4095.0f` constants rather than

`analogReadMilliVolts`.

### Caution — ADC2 is unavailable while Wi-Fi is active

**Engineering interpretation.** This is not a comment in the source; it is the

documented behaviour of the ESP32 ADC peripheral, applied here to the actual

pin assignments.

| Node | Analogue input | GPIO | ADC unit |

|---|---|---|---|

| Node 2 | Dissolved oxygen | **34** | **ADC1_CH6** |

| Node 4 | pH | **13** | **ADC2** |

| Node 4 | Turbidity | **14** | **ADC2** |

| Node 4 | Conductivity (EC) | **12** | **ADC2** |

On the ESP32, ADC2 is shared with the Wi-Fi and Bluetooth radio path and

**cannot be read while Wi-Fi is active**. Node 4 therefore has three of its four

analogue channels on the ADC that becomes unusable the moment the radio starts.

This matters specifically for the **`Node4_SMTP` variant**, which includes

`WiFi.h` and calls `WiFi.begin()` in `initNetworkAndTime()`:

* The pH, turbidity and EC channels on GPIO 13, 14 and 12 are ADC2 reads.

* `Node4_SMTP` enables Wi-Fi for its e-mail reporting path.

* **Engineering interpretation:** pH, turbidity and EC on the SMTP variant are

  therefore at risk of returning invalid readings — the firmware's validity

  gates (`0.0 <= V <= 3.30`) would reject them, and the health flag would go to

  `0`.

* The non-SMTP `Node4` sketch contains no Wi-Fi code at all, so the same risk

  does not apply to it in its committed form.

**Recommendation.** If the SMTP variant is deployed, verify pH, turbidity and EC

behaviour with Wi-Fi associated before relying on them. Moving those three

inputs to ADC1-capable GPIOs, or reading them with a different strategy while

the radio is up, would remove the conflict — but that is a firmware change, not

a documentation change.

### Caution — GPIO 34 is input-only

**Engineering knowledge, not from the source.** On the ESP32, GPIO 34, 35, 36

and 39 are **input-only** and have no output driver and no internal pull-up or

pull-down. Node 2's dissolved oxygen input is on GPIO 34, which is consistent

with its use purely as an analogue input. Nothing in the source configures

`INPUT_PULLUP` on GPIO 34, which matters for the ultrasonic modules — see

<a href="wiring.html">Wiring</a>.

## Non-volatile storage

`Node4` uses the ESP32 `Preferences.h` API for two namespaces:

| Namespace | Contents | Used by |

|---|---|---|

| `node4_cal` | `phSlope`, `phOffset`, `ecKFactor` | `loadCalibration()`, calibration console |

| `email_state` | `lastHbEpoch`, `lastErrEpoch` | SMTP heartbeat and fault-alert rate limiting |

The default calibration constants **differ between the two Node 4 sketches**:

| Constant | `Node4` default | `Node4_SMTP` default |

|---|---|---|

| `phSlope` | 3.5 | 3.5 |

| `phOffset` | −1.75 | 0.0 |

| `ecKFactor` | 9.997 | 2.0 |

This is a real divergence between the variants, not a documentation artefact.

See <a href="../nodes/node4.html">Node 4</a> and

<a href="../nodes/node4-smtp.html">Node 4 (SMTP)</a>.

## Related pages

* <a href="gpio-map.html">GPIO Map</a> — full pin reference.

* <a href="power.html">Power</a> — logic levels and the power budget gaps.

* <a href="../rtos/tasks.html">RTOS Tasks</a> — core pinning and stack sizes.

* <a href="../calibration/index.html">Calibration</a> — how the NVS constants are

  measured and applied.


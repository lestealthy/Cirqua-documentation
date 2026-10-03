---

title: Calibration

description: What can and cannot be calibrated at runtime across the four CIRQUA nodes, with a matrix of constants, storage and change method.

---

# Calibration

This section separates what the firmware actually allows you to calibrate from what

people commonly assume is adjustable. The distinction is not cosmetic: **only two

quantities can be changed on a deployed node without re-flashing it**, and everything

else is baked into the sketch at compile time.

Claim types used throughout this section:

- **Firmware implementation** — read directly from the audited source.

- **Engineering interpretation** — our reading of what that code implies.

- **Recommendation** — advice, clearly labelled, not derived from the source.

## The critical honest finding

**Firmware implementation.** On the four ESP32 nodes, only **pH** and **electrical

conductivity (EC)** calibration constants are held in non-volatile memory and can be

adjusted on a running board. They live in the ESP32 `Preferences` (NVS) namespace

`node4_cal` with the keys `phSlope`, `phOffset` and `ecKFactor`, and they are editable

at runtime from the PC serial console on Node 4 at 115200 baud.

**Firmware implementation.** Every other calibration constant is a literal in the

`.ino` sketch:

| Constant | Sketch |

|---|---|

| `TANK_HEIGHT`, `TANK_RADIUS` (three separate node pairs) | `Node1.ino`, `Node2.ino`, `Node4.ino` |

| Node 1 volume multiplication by `2.0f` | `Node1.ino` |

| `VREF`, `ADC_RESOLUTION`, `TWO_POINT_VOLTAGE`, `SATURATION_DO_25C` (dissolved oxygen) | `Node2.ino` |

| Turbidity quadratic coefficients and thresholds | `Node4.ino` |

| `FLOW_CAL_FACTOR` (flow pulses per litre) | `Node3.ino` |

**Engineering interpretation.** This is an operational limitation with real

consequences: a technician who discovers that the Collection Tank A volume is wrong by

15 % cannot fix it in the field. They must edit the sketch, rebuild, and re-flash the

node over USB. Any calibration procedure that ends in "adjust the constant" must state

which of the two cases it is in.

## Calibration matrix

| Quantity | Node | Constant(s) | Default | Storage | How changed | Link |

|---|---|---|---|---|---|---|

| pH slope | 4 | `phSlope` | `3.5f` (`Node4`), `3.5f` (`Node4_SMTP`) | NVS `node4_cal` | Serial `SET:PH_S=<v>` (`Node4` only) | [pH](ph.md) |

| pH offset | 4 | `phOffset` | `-1.75f` (`Node4`), `0.0f` (`Node4_SMTP`) | NVS `node4_cal` | Serial `SET:PH_O=<v>` (`Node4` only) | [pH](ph.md) |

| EC K-factor | 4 | `ecKFactor` | `9.997f` (`Node4`), `2.0f` (`Node4_SMTP`) | NVS `node4_cal` | Serial `SET:EC_K=<v>` (`Node4` only) | [Conductivity](conductivity.md) |

| Collection Tank A geometry | 1 | `TANK_HEIGHT`, `TANK_RADIUS` | `260.0f` cm, `110.0f` cm | Sketch constant | Edit + re-flash | [Ultrasonic](ultrasonic.md) |

| Collection Tank A volume scale | 1 | `2.0f` multiplier | `2.0f` | Sketch constant | Edit + re-flash | [Ultrasonic](ultrasonic.md) |

| Feeding Tank B geometry | 2 | `TANK_HEIGHT`, `TANK_RADIUS` | `178.0f` cm, `59.5f` cm | Sketch constant | Edit + re-flash | [Ultrasonic](ultrasonic.md) |

| Effluent geometry | 4 | `TANK_HEIGHT`, `TANK_RADIUS` | `178.0f` cm, `59.5f` cm | Sketch constant | Edit + re-flash | [Ultrasonic](ultrasonic.md) |

| Ultrasonic sound speed | 1, 2, 4 | `0.0343f` cm/µs | `0.0343f` | Sketch constant | Edit + re-flash | [Ultrasonic](ultrasonic.md) |

| Ultrasonic `pulseIn` timeout | 1, 2, 4 | `30000` / `20000` / `25000` µs | per node | Sketch constant | Edit + re-flash | [Ultrasonic](ultrasonic.md) |

| Dissolved oxygen reference | 2 | `TWO_POINT_VOLTAGE`, `SATURATION_DO_25C` | `1000.0f` mV, `8.26f` mg/L | Sketch constant | Edit + re-flash | [Dissolved oxygen](dissolved-oxygen.md) |

| Dissolved oxygen temperature slope | 2 | `-0.02f` per °C | `-0.02f` | Sketch constant | Edit + re-flash | [Dissolved oxygen](dissolved-oxygen.md) |

| Flow K-factor | 3 | `FLOW_CAL_FACTOR` | `5.5f` pulses/litre | Sketch constant | Edit + re-flash | [Flow](../sensors/flow.md) |

| Turbidity curve | 4 | `-1120.4f`, `5742.3f`, `-4353.8f`; `3.20f`, `0.50f` | as listed | Sketch constant | Edit + re-flash | [Turbidity](turbidity.md) |

> **Not verified from the current source.** There is no flow K-factor calibration page

> in this documentation set, no pH electrode lot/serial tracking, and no stored record

> of which calibration solution was used for any node.

## What has no calibration path at all

- **Turbidity.** There are no offset or gain constants. The SEN0189/DFRobot quadratic is

  used verbatim. There is nothing to adjust and nothing in NVS. See

  [Turbidity](turbidity.md).

- **Dissolved oxygen.** No two-point slope/offset pair is stored or applied; the sensor

  is characterised entirely by compile-time constants. See

  [Dissolved oxygen](dissolved-oxygen.md).

- **Ultrasonic sensor mounting offset.** The firmware computes water height as

  `TANK_HEIGHT - distance` with **zero** offset compensation. If the sensor is fitted

  below the tank rim, every reading carries a systematic error that no constant can

  absorb without a firmware change. See [Ultrasonic](ultrasonic.md).

- **Relative humidity and ambient temperature.** The DHT11 is read and range-checked but

  never corrected.

## The NVS calibration structure

**Firmware implementation.** The three floats are held in a single struct, declared

identically in both Node 4 variants:

```cpp

--8<-- "assets/snippets/node4-calibration-struct.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>CalibrationData</code> ·

lines 53–66 · commit <code>db6d9b8</code>
</div>

They are loaded once in `setup()` before any task starts:

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

**Engineering interpretation.** Because the defaults are supplied as `getFloat()`

fallbacks, a fresh board and a board that has been `RESET` behave identically, and a

board that has had `SET:` commands issued behaves differently until the namespace is

cleared. `RESET` calls `preferences.clear()` on `node4_cal` and then re-runs

`loadCalibration()`, so it is a safe way to return a node to its as-built state.

> **Not verified from the current source.** Whether a given board's NVS namespace has

> already been written to cannot be determined without reading it back on the node

> (`STATUS` prints the stored values).

## Calibration pages

| Page | Covers |

|---|---|

| [Ultrasonic](ultrasonic.md) | Tank geometry, the Node 1 ×2 factor, mounting offset, verification |

| [Dissolved oxygen](dissolved-oxygen.md) | Two-point linear model, temperature coefficient, what "calibration" really means here |

| [pH](ph.md) | The only genuinely field-adjustable analogue channel; buffer procedure |

| [Turbidity](turbidity.md) | SEN0189 quadratic, the corrected ADC reference, why old data is not comparable |

| [Conductivity](conductivity.md) | K-factor determination, temperature compensation, the SMTP unit divergence |

## Related pages

- [Field service](../field-service/index.md) — bringing a calibrated node back into service

- [Firmware configuration](../firmware/configuration.md) — the compile-time constants as code

- [Validation](../validation/hardware-validation.md) — how calibration is verified

- [Hardware](../hardware/gpio-map.md) — which pin each calibrated channel is on
---

title: Water Temperature

description: DS18B20 water temperature on Node 2 and submerged temperature on Node 4, with 1-Wire bus behaviour, resolution choices and validity gating.

---

# Water Temperature

CIRQUA takes two water temperature measurements, both with a DS18B20 on a

1-Wire bus, and they serve different purposes:

| Node | Sensor | What it measures | Why it exists |

|---|---|---|---|

| 2 | DS18B20 on GPIO 4 | Feeding Tank B water temperature | Reported as `Temp`, shown on the Node 1 LCD, and used to temperature-compensate the dissolved oxygen reading on the same node |

| 4 | DS18B20 on GPIO 27 | Submerged temperature in the effluent stream | Reported as `ST` (`Node4_SMTP` only); it is the temperature compensation input for **both** the pH and the conductivity readings on Node 4 |

Node 4's submerged probe is therefore not just a reporting channel — it is an

input to two other measurements on that node.

<div class="cirqua-identity">

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Nodes</span>

    <span class="cirqua-identity__value">2 (water), 4 (submerged)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">GPIO</span>

    <span class="cirqua-identity__value">N2 <code>PIN_DS18B20</code> <code>4</code><br>N4 <code>PIN_SUB_DS18B20</code> <code>27</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Interface</span>

    <span class="cirqua-identity__value">1-Wire (single-wire digital bus)</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Signal type</span>

    <span class="cirqua-identity__value">Digital, 12-bit addressable device; firmware reads by index, not by address</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Firmware reading function</span>

    <span class="cirqua-identity__value"><code>Task_Sensors_Node2</code>, <code>Task_Sensors_Node4</code> → <code>getTempCByIndex(0)</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Status</span>

    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--current">current</span> <span class="cirqua-badge cirqua-badge--verified">verified in source</span></span>

  </div>

</div>

## Purpose and measured quantity

Both readings are **water temperature in degrees Celsius**, returned as a

floating-point value. No conversion, scaling or unit change is applied by the

firmware: `getTempCByIndex()` already returns Celsius.

The two measurements feed different parts of the system:

* **Node 2 water temperature** is carried as `Temp` in the frame, displayed on

  the Node 1 LCD as `T{value}C`, and is the temperature input to the

  [dissolved oxygen](dissolved-oxygen.md) compensation factor on the same

  node. Because the DO compensation reads the temperature *earlier in the same

  task iteration*, the DO reading uses the previous cycle's temperature.

* **Node 4 submerged temperature** is the temperature input to the

  [pH](ph.md) and [conductivity](conductivity.md) compensation expressions

  on that node.

!!! NOTE

    In the standard `Node4` sketch the submerged temperature is read and used

    for compensation but is **not** emitted downstream. The frame carries

    `pH`, `Turb`, `EC` and `TCV`. It is the `Node4_SMTP` variant that adds

    `|ST:%.1f` to the downstream frame. This is a real divergence between the

    two variants, not a documentation simplification — see

    [Message Format](../communication/message-format.md).

## Physical principle

> **Manufacturer specification.** `DS18B20` is the part name written in the

> firmware. No accuracy, resolution or conversion-time figure in this section

> is taken from a datasheet. The exact fitted part number and its manufacturer

> are **Not verified from the current source.**

Generic principle: a 1-Wire digital temperature sensor contains a

temperature-dependent oscillator or bandgap reference whose period or

threshold shifts with temperature. The device converts that internally to a

digital value and presents it over a single-wire bus, returning a fixed-point

temperature value in counts. Because the value is digital, the reported

resolution is a property of the configured conversion resolution, not of the

wiring.

Only the resolution setting is verified behaviour in this firmware: Node 4 sets

10-bit, and Node 2 leaves the library default. No accuracy specification is

asserted anywhere on this page.

## Electrical interface

A single-wire digital bus. On the ESP32 this is normally bit-banged or

otherwise handled by the 1-Wire support in the sensor library; the firmware

does not configure an ESP32 hardware peripheral for it.

What the firmware configures differs by node:

| Setting | Node 2 | Node 4 |

|---|---|---|

| Pin | GPIO 4 | GPIO 27 |

| `setResolution()` | not called — library default | `setResolution(10)` |

| `setWaitForConversion()` | `false` — **non-blocking** | `true` — **blocking** |

| Conversion trigger | `requestTemperatures()` every cycle | `requestTemperatures()` every cycle |

| Boot-time presence check | none | warns if `getDeviceCount() == 0` |

| Read | `getTempCByIndex(0)` | `getTempCByIndex(0)`, guarded by `getDeviceCount() > 0` |

### Node 2 — non-blocking by design

```cpp

sensorsN2.begin();

sensorsN2.setWaitForConversion(false);  // Non-blocking state machine

sensorsN2.requestTemperatures();        // Trigger initial conversion

```

Node 2 treats the sensor as a pipeline: it requests a conversion, and reads the

value that the *previous* conversion produced, requesting the next one at the

same moment.

```cpp

float tempC = sensorsN2.getTempCByIndex(0);

sensorsN2.requestTemperatures();  // Trigger conversion for NEXT cycle

```

The one-cycle latency this introduces is not compensated for and is not

documented in the source. It is harmless for the DO compensation factor, which

changes slowly.

### Node 4 — deliberately blocking

Node 4 takes the opposite approach and the source states its own reason: at

10-bit resolution the conversion takes roughly 187.5 ms, which is acceptable

given the 1 Hz task period. The reading returned on a given cycle is therefore

the one produced by the conversion requested on that same cycle.

Node 4 also checks for device presence at boot and warns if none is found:

```cpp

if (sensorsN4.getDeviceCount() > 0) {

    sensorsN4.requestTemperatures();

    st = sensorsN4.getTempCByIndex(0);

}

```

If the device count is zero, the local value is left at `DEVICE_DISCONNECTED_C`

and the validity test below fails — the same path as a disconnected probe.

## How CIRQUA uses it

### Validity gating

Both nodes use the same validity predicate, with slightly different

inequalities:

```text

valid  <=>  temp != DEVICE_DISCONNECTED_C

         AND  temp >  -55

         AND  temp <  125

```

Node 4 uses `>= -55` and `<= 125`; Node 2 uses `> -55` and `< 125`. The

difference is immaterial at any physically achievable temperature but is

recorded here for accuracy.

The `-55 / 125` window is the conventional range outside which a 1-Wire

temperature device reports its fault sentinel rather than a temperature. The

firmware's use of it is a *disconnected-device guard*, not a plausibility

check on the measured value.

### Node 2

```cpp

--8<-- "assets/snippets/node2-sensor-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>Task_Sensors_Node2</code> ·

lines 98–220 · commit <code>db6d9b8</code>
</div>

### Node 4

```cpp

--8<-- "assets/snippets/node4-sensor-task.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_Sensors_Node4</code> ·

lines 374–712 · commit <code>db6d9b8</code>
</div>

### Downstream compensation use

The temperature is consumed by other measurements on the same node. Both

compensations fall back to **25.0 °C** when the temperature reading is invalid:

```text

compTemp = tempValid ? temp : 25.0

```

This fallback is silent — the compensation continues to be applied, using a

default temperature, and the fact that the temperature sensor has failed is

recorded separately in the node health flag. See

[dissolved oxygen](dissolved-oxygen.md), [pH](ph.md) and

[conductivity](conductivity.md) for the three expressions involved.

### Frame field

| Node | Field | Format | Notes |

|---|---|---|---|

| 2 | `Temp` | `%.2f` | Carried upstream to Node 1 and onwards |

| 4 | `ST` | `%.1f` | `Node4_SMTP` only; absent from the standard `Node4` downstream frame |

## Calibration

**None.** There is no offset, gain or calibration constant for temperature

anywhere in the firmware, and no entry in the Node 4 calibration console. The

value read is the value reported.

The only adjustment available is the conversion resolution setting

(`setResolution(10)` on Node 4), which is a compile-time choice affecting the

digital resolution of the value, not a calibration.

## Expected values and typical ranges

Derivable from the firmware:

* Output is in **degrees Celsius**.

* Validity window accepted by the firmware: **-55 to 125 °C**.

* Fallback temperature used for compensation when the reading is invalid:

  **25.0 °C**.

* Node 4 configured resolution: **10-bit**, which the source comment ties to

  an approximately 187.5 ms conversion time.

* Node 1 displays Node 2's ambient values, not water temperature, and raises

  `OVERTEMP` at 45 °C — but that threshold applies to the

  [DHT11 ambient](humidity.md) reading, not to this sensor.

Observed water temperature ranges in any specific tank, and the achievable

accuracy of the fitted device:

> **Not verified from the current source.** No field data, no accuracy figure

> and no accuracy figure from a manufacturer datasheet is available to this

> documentation set.

## Failure modes

What the firmware treats as invalid:

* **Device absent from the bus.** `getTempCByIndex()` returns

  `DEVICE_DISCONNECTED_C`, which fails the `!= DEVICE_DISCONNECTED_C` test.

  On Node 4 a missing device at boot additionally produces a warning on the

  115200 baud debug serial port.

* **Reported value outside -55 to 125 °C.** Treated as a bus fault, not as a

  measurement.

What a field technician should look for:

* **A permanently invalid temperature.** Almost always an open or shorted 1-Wire

  run, a missing pull-up, or a probe that has been left out of the water and

  whose connector has wetted.

* **A plausible but constant value.** A probe left in still air reads the

  enclosure temperature perfectly consistently. The firmware cannot distinguish

  this from a genuine water measurement.

* **One-cycle lag on Node 2.** Expected behaviour, not a fault. If a rapid

  temperature step is being used to validate the reading, allow for the

  pipeline delay.

* **Compensation silently wrong.** If the temperature probe fails, the pH and

  EC readings on Node 4 continue to be produced using the 25 °C default. The

  node health flag will show the temperature as invalid, but the affected

  channels themselves will still report valid values. Always check the node

  health flag before trusting a compensated reading.

## Environmental considerations

* **Probe immersion.** A DS18B20 in a wet housing measures the enclosure, not

  the water. For the Node 4 submerged probe this matters more than usual, because

  it feeds two other measurements.

* **Thermal mass and response time.** A sealed probe in a moving stream reads

  well; a probe in a still tank with significant thermal mass lags diurnal

  change considerably.

* **1-Wire bus integrity.** The bus is single-wire and sensitive to cable

  length, parasitic capacitance and any moisture ingress on the run. Long runs

  or unshielded cables in a wet enclosure are a common cause of intermittent

  fault sentinels.

* **Readings feed compensation, so an error propagates.** A temperature error

  propagates directly into the DO value on Node 2 and into the pH and EC values

  on Node 4. A temperature that is *stable but wrong* is more damaging than one

  that is noisy but centred correctly.

* **Self-heating.** The device draws current on the bus during conversion. At

  low water flow this can bias a reading slightly high. No correction is

  applied.

## Limitations

Firmware-level limitations:

* **No calibration of any kind.** No offset, no slope, no NVS-stored constant.

* **Node 2 has a one-cycle pipeline delay** between the requested conversion and

  the value used. This is undocumented in the source and is invisible in steady

  state.

* **Node 4 blocks its sensor task** for approximately 187.5 ms out of every

  1000 ms while the conversion completes. The source states this is acceptable

  at 1 Hz; it does mean the whole of Node 4's sampling — pH, turbidity, EC,

  DHT11 and ultrasonic — is delayed by that interval each cycle.

* **No averaging.** A single read per cycle is used directly. There is no

  median, no moving average, no outlier rejection.

* **The temperature sensor's failure does not fail its dependents.** When the

  reading is invalid, the DO, pH and EC compensations silently substitute

  25 °C and continue to report as valid.

* **Only index 0 is read.** If more than one device is on the bus, only the

  first is used, and the firmware gives no indication that others are present —

  apart from Node 4's boot-time device count.

* **Different resolution on each node.** Node 4 is 10-bit; Node 2 uses the

  library default. The two channels are therefore not directly comparable in

  their digital resolution, and Node 4's is the lower of the two.

* **The node health flag is the only failure signal downstream.** A consumer of

  the frame sees a `Temp` value and a `node2` flag, not a reason.

## Maintenance and replacement

Replacing a DS18B20 requires attention to the 1-Wire run: bus polarity, bus

pull-up, and physical protection of the connector. Once replaced, no

calibration is required by the firmware — but the probe's physical immersion

depth and thermal contact should be restored to match the original

installation, because nothing in the firmware compensates for a probe that is

installed differently.

Procedure: [Sensor Replacement](../field-service/sensor-replacement.md).

Routine checks: [Maintenance](../field-service/maintenance.md).

> **Not verified from the current source.** Cable types, lengths, gauges and

> connector pinouts are not documented in the repository.

## Where it is used

| Node | GPIO | Reading function | Frame field | Used for |

|---|---|---|---|---|

| 2 | 4 (`PIN_DS18B20`) | `Task_Sensors_Node2` | `Temp` | Node 1 LCD; DO temperature compensation |

| 4 | 27 (`PIN_SUB_DS18B20`) | `Task_Sensors_Node4` | `ST` (`Node4_SMTP` only) | pH and EC temperature compensation |

Full pin table: [GPIO Map](../hardware/gpio-map.md).

Node detail: [Node 2](../nodes/node2.md), [Node 4](../nodes/node4.md),

[Node 4 SMTP](../nodes/node4-smtp.md).

## Source

Firmware repository: [lestealthy/Cirqua](https://github.com/lestealthy/Cirqua),

branch `main`, commit

[`db6d9b896341a9c7d8fd01913e854b663c110d55`](https://github.com/lestealthy/Cirqua/tree/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation)

(short `db6d9b8`).

| Snippet | Source path | Symbol | Lines |

|---|---|---|---|

| `node2-sensor-task` | `FreeRTOS_Implementation/Node2/Node2.ino` | `Task_Sensors_Node2` | 98–220 |

| `node4-sensor-task` | `FreeRTOS_Implementation/Node4/Node4.ino` | `Task_Sensors_Node4` | 374–712 |

| `node4-setup` | `FreeRTOS_Implementation/Node4/Node4.ino` | `setup()` | 1264–1336 |

| `node2-pin-definitions` | `FreeRTOS_Implementation/Node2/Node2.ino` | — | 10–32 |

| `node4-pin-definitions` | `FreeRTOS_Implementation/Node4/Node4.ino` | — | 10–41 |

Everything on this page is *firmware implementation*. Statements about the

sensor device itself are generic and unverified: `DS18B20` is the name used in

the source, and no manufacturer specification is asserted.

Related: [Sensors overview](index.md) ·

[Dissolved Oxygen](dissolved-oxygen.md) · [pH](ph.md) ·

[Conductivity](conductivity.md) ·

[Sensor Replacement](../field-service/sensor-replacement.md)


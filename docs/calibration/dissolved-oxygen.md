---

title: Dissolved Oxygen Calibration

description: The Node 2 two-point linear dissolved oxygen model, its compile-time constants, temperature coefficient and verification limits.

---

# Dissolved Oxygen Calibration

Dissolved oxygen (DO) is measured on **Node 2 only**, from a single analogue channel,

GPIO 34. This page describes what the firmware actually computes and — just as

importantly — what it does not.

Claim types used throughout: **Firmware implementation**, **Engineering

interpretation**, **Manufacturer specification** (where cited), **Recommendation**.

## The constants

**Firmware implementation.** Four compile-time constants define the entire

dissolved-oxygen channel:

| Constant | Value | Purpose |

|---|---|---|

| `VREF` | `5000.0f` (mV) | Full-scale analogue reference |

| `ADC_RESOLUTION` | `4095.0f` | 12-bit ADC count maximum |

| `TWO_POINT_VOLTAGE` | `1000.0f` (mV) | Voltage assumed to correspond to air saturation |

| `SATURATION_DO_25C` | `8.26f` (mg/L) | Saturation concentration at 25 °C |

They are declared as `const float` in `Node2.ino` and there is no `Preferences` usage

anywhere in that sketch. **There is no runtime calibration for dissolved oxygen, and no

non-volatile storage for it.**

## The formula

**Firmware implementation.** Inside `Task_Sensors_Node2`, run every 1000 ms:

```text

doVoltage    = (rawDO / 4095.0) * 5000.0                      [mV]

compTemp     = waterTemp_valid ? waterTemp : 25.0              [°C, DS18B20]

compFactor   = 1.0 + (compTemp - 25.0) * (-0.02)

dissolvedOxygen = (doVoltage / 1000.0) * 8.26 * compFactor    [mg/L]

```

The result is clamped to a minimum of zero. The node marks the reading invalid only

when `rawDO == 0`. Output unit is **mg/L** and the Node 1 LCD prints it as `mg/l`.

## The Node 2 sensor task

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

The DO block is lines 142–160 of that function, immediately after the DS18B20 block

that supplies `tempC` and `tempValid`.

## Honest assessment of the model

### It is a two-point linear model, not a calibration

**Firmware implementation.** The constant is named `TWO_POINT_VOLTAGE` and is `1000.0f`

mV. It is a single-point scale factor, not a two-point intercept-and-slope pair.

**Engineering interpretation.** The code says: *"if the pin is at 1000 mV, then the water

is at air saturation, which is 8.26 mg/L."* Everything in between is scaled linearly from

that one anchor. So the model has **exactly one** adjustable quantity, and it is not

adjustable at runtime — it is a literal.

Two consequences follow directly from that structure:

- A sensor that is 5 % low at 1000 mV is assumed to be 5 % low at every other voltage.

  Real optical DO probes are not linear across their range.

- If the sensor never reaches exactly 1000 mV, the error is multiplied by the ratio of

  expected to actual anchor voltage, and the error can be large.

### The temperature coefficient is a linearisation, not a law

**Firmware implementation.** `compFactor = 1.0 + (T - 25.0) * (-0.02)` — a straight

line through `(25 °C, 1.00)` with slope −0.02 per °C, applied multiplicatively to the

concentration.

**Engineering interpretation.** The true relationship between dissolved-oxygen

saturation concentration and temperature is a strongly non-linear curve that falls more

steeply at high temperatures than at low ones. A single −0.02/°C straight line

approximates that curve; it is a first-order approximation and it will be least accurate

away from 25 °C. It is not derived from the physical solubility of oxygen in water, and

the source does not cite a source for it.

Note also that `8.26f` is used as the anchor for *air* saturation at 25 °C. Whether that

matches the intended saturation condition (air-saturated vs. pure-oxygen-saturated) is

not stated in the source.

### The `VREF` question — read this carefully

**Firmware implementation.** Node 2 computes `doVoltage = (raw / 4095.0) * 5000.0`, and

the inline comment on the `VREF` declaration describes it as the "ADC Reference Voltage

(mV) on 3.3V ESP32". The ESP32 ADC is not a 0–5 V converter.

**Engineering interpretation.** This is a real inconsistency in the source: a

12-bit ESP32 ADC reading is being scaled as though full scale were 5000 mV. Whatever

voltage the sensor actually presents at the pin is therefore reported approximately

1.5× higher (5000 / 3300) than the pin voltage. The pH, turbidity and EC channels on

Node 4 do **not** make this mistake — they use `analogReadMilliVolts()`, which is

calibration-aware and returns the true pin voltage in millivolts. Node 2 does not.

This does not by itself mean the DO channel is unusable, because it is absorbed by the

anchor assumption — but it means the reported mg/L value cannot be reconciled against

the actual pin voltage without knowing the sensor's own scaling. Treat it as an

unverified calibration.

> **Not verified from the current source.** The make and model of the dissolved-oxygen

> module, its output current/voltage scaling, its warm-up time, its membrane type, and

> whether it is an analog or digital-output probe. Only the GPIO (34) and the four

> constants above are established by the source.

### No warm-up handling

**Engineering interpretation.** The first reading after power-up is taken at the same

1 Hz cadence as every other. Many dissolved-oxygen probes need a settling period after

power-up before the output is meaningful. The firmware has no warm-up timer and no

discard of early samples, so the first values after a restart should not be trusted.

## There is no runtime calibration

**Firmware implementation.** To change anything about the DO channel you must edit

`Node2.ino`, rebuild and re-flash. There is:

- no `Preferences` namespace in `Node2.ino`,

- no `SET:` command handler,

- no NVS key for DO,

- no adjustable slope or offset anywhere in the sketch.

This is stated explicitly because it is a genuine operational limitation: a technician

cannot bring a DO reading into tolerance on site.

## Verification procedure

**Recommendation.** The following compares the firmware output against a physical

anchor. It requires access to water of known DO concentration at a known temperature.

1. **Establish the software baseline.** Power Node 2 and record the `DO…` value from the

   Node 1 LCD (or read the `DO:` field from a serial capture of the Node 2 → Node 3

   frame). Note the `Temp` value at the same moment — the compensation factor depends on

   it, and it changes if the water warms.

2. **Prepare the air-saturated sample.** Bubble air through clean water of the same

   temperature until it will hold no more air. Verify saturation independently — a

   dissolved-oxygen meter or a Winkler titration. Without an independent check this

   procedure cannot validate anything.

3. **Submerge the probe** to the depth it is normally mounted at, and let it settle.

4. **Read the anchor voltage.** Node 2 has no `STATUS` command — the console described in

   [pH calibration](ph.md) exists on Node 4 only. Measure the module output with a

   meter, or read `rawDO` from a serial/ADC capture if you have added one.

5. **Compare.** At true saturation the firmware should output approximately

   `8.26 * compFactor`. Compute the expected value:

   ```text

   expected_mg_per_L = 8.26 * (1.0 + (T - 25.0) * (-0.02))

   ```

   For example at 20 °C: `8.26 * (1.0 + (20 - 25) * (-0.02)) = 8.26 * 1.10 = 9.09 mg/L`.

   At 30 °C: `8.26 * 0.90 = 7.43 mg/L`.

6. **Record the ratio** `reported / expected`. If it is within your measurement

   uncertainty, the channel is behaving as designed.

7. **Check the anchor voltage against 1000 mV.** If the module output at true air

   saturation is not close to 1000 mV, that ratio is the size of the error you are

   carrying, and it scales the whole range.

8. **Repeat at a second temperature** to expose the limitation of the linear

   coefficient. Compare the reported value against a true measurement at, for example,

   15 °C as well as 25 °C. A divergence that grows away from 25 °C confirms the

   linearisation limitation described above.

9. **Decide.**

   - Within tolerance → record as verified. No action.

   - Constant offset at both temperatures → the anchor voltage is wrong. **Correcting it

     requires editing `TWO_POINT_VOLTAGE` and `SATURATION_DO_25C` in `Node2.ino` and

     re-flashing.** There is no other path.

   - Divergence that grows away from 25 °C → the −0.02/°C coefficient is not adequate

     for the operating range. Only a firmware change addresses it.

10. **Record before and after readings** in the maintenance log

    ([Maintenance](../field-service/maintenance.md)).

## What this page does not claim

- No accuracy, precision or drift specification is given, because none is published in

  the repository and the sensor model is unknown.

- No calibration certificate, traceability statement or standard reference is claimed.

- No bench comparison against a reference DO meter has been recorded.

## Related pages

- [Calibration index](index.md)

- [Dissolved oxygen sensor](../sensors/dissolved-oxygen.md)

- [Node 2](../nodes/node2.md)

- [Node 1 LCD status](../field-service/troubleshooting.md) — how `DO` and `node2:0` appear

- [Known limitations](../validation/known-limitations.md)
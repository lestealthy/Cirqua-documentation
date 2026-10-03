---

title: Conductivity Calibration

description: Node 4 EC K-factor determination against a standard solution, temperature compensation, and the mS/cm divergence in the SMTP variant.

---

# Conductivity Calibration

Conductivity (EC) is the second genuinely adjustable channel on Node 4, alongside pH. It

uses the same NVS namespace and the same serial console. Its default value differs

between the two Node 4 variants, and one of those variants reports a different unit

entirely — see [the divergence section](#the-node4_smtp-divergence) below.

Claim types used throughout: **Firmware implementation**, **Engineering

interpretation**, **Recommendation**.

## The formula

**Firmware implementation.** On GPIO 12 with `ADC_11db` attenuation, 12-bit, evaluated

once per second in `Task_Sensors_Node4`:

```text

ecCoefficient    = 1.0 + 0.0185 * (T - 25.0)

rawEcMilliSiemens = V * ecKFactor

compensatedEc    = (rawEcMilliSiemens / ecCoefficient) * 1000.0    [µS/cm]

```

`V` is the calibrated pin voltage from `readSensorVoltage()` in volts, `T` is the

submerged DS18B20 reading or 25.0 °C if that probe is invalid, and the result is clamped

to a minimum of zero. Validity: accepted whenever `0.0 <= V <= 3.30`.

**Firmware implementation.** Zero EC is explicitly accepted. The source comment states

the intent: zero or very low conductivity is a legitimate measurement, not an error.

`ecCoefficient` is a single linear coefficient. It is a first-order approximation of

conductivity's temperature dependence — real reference solutions have a non-linear

temperature coefficient, typically around 2 %/°C, which is the basis of the ISO 6070

correction convention. The source does not cite a standard.

## The EC processing block

```cpp

--8<-- "assets/snippets/node4-ec-processing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node4/Node4.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node4/Node4.ino</code> ·

<code>Task_Sensors_Node4</code> (EC block) ·

lines 584–635 · commit <code>db6d9b8</code>
</div>

## Storage and defaults

**Firmware implementation.** The K-factor is stored in NVS namespace `node4_cal` under

the key `ecKFactor`:

| Variant | Default | Reported unit | Temperature compensated | Serial console |

|---|---|---|---|---|

| `Node4` | `9.997f` | µS/cm (`EC:%duS` on LCD) | Yes | Yes |

| `Node4_SMTP` | `2.0f` | mS/cm (`EC:%.1fmS` on LCD) | **No** | **No** |

Both variants read the same NVS key, so the SMTP default is only used when the key is

absent. Flashing one variant over a board calibrated for the other retains the old value.

## How the K-factor relates to EC and to TDS

**Engineering interpretation.** The firmware implements exactly one thing:

```text

EC (mS/cm) = V (V) * K          — the un-compensated relationship

```

`K` is the module's volts-to-mS/cm scale factor. Everything else in the expression is

temperature compensation and a unit change:

- Dividing by `ecCoefficient` normalises the reading to a 25 °C basis.

- Multiplying by `1000.0` converts mS/cm to µS/cm.

**The firmware does not compute TDS.** There is no division by a factor of 0.5, no

`TDS` field, no `TDS:` key in any frame, and no such column anywhere. If a TDS figure is

required it must be derived outside the node, and any conversion factor used for that is

an engineering decision that the firmware does not make and the documentation does not

assert.

## The `Node4_SMTP` divergence

**Firmware implementation.** In `Node4_SMTP.ino` the EC block is:

```text

ecVolt = (ecRaw * ESP32_VREF) / ADC_RESOLUTION        with ESP32_VREF = 3.3f

ec     = ecVolt * currentEcK                          — no temperature term, no x1000

```

**Engineering interpretation.** Two things follow, and both matter operationally:

1. **No temperature compensation.** `Node4_SMTP` reports the raw, uncompensated

   conductivity. `Node4` reports a 25 °C-normalised value. At a water temperature

   appreciably different from 25 °C these are different quantities, not the same

   quantity in different units.

2. **The unit is mS/cm, not µS/cm.** The `×1000` is absent. The default `ecKFactor` of

   `2.0f` is numerically close to the same module scale expressed in a different unit

   convention, but the two defaults must not be interchanged.

**Consequence: EC values from `Node4` and `Node4_SMTP` cannot be compared directly.**

To compare, you must (a) know the water temperature at each measurement, (b) invert the

`Node4` compensation, `EC_mS_cm = EC_uS_cm / 1000 * ecCoefficient`, and (c) confirm that

the two boards carry the same `ecKFactor` in NVS. If the two K-factors differ, the

conversion also requires `EC₂ = EC₁ × K₂/K₁`.

**Recommendation.** Label recorded EC data with the firmware variant. A dataset that

mixes the two without that label is not interpretable.

## Console procedure

The console is the same as for [pH](ph.md) — `Node4` only, **115200 baud, 8N1,

newline-terminated**. Commands are read in the UART task.

| Command | Effect |

|---|---|

| `STATUS` | Prints the EC raw ADC, EC volts, the **current** `ecKFactor`, and the other two channels |

| `SET:EC_K=<val>` | Persists `ecKFactor`. **Rejects values `<= 0`** with `[ERROR] Invalid value for EC K-Factor.` |

| `RESET` | Clears `node4_cal` and reloads the variant defaults |

Note the asymmetry with pH: the EC K-factor **is** validated, while `SET:PH_S=` and

`SET:PH_O=` are not. A rejected EC value is not written, so a typo there cannot corrupt

the stored calibration.

`STATUS` shows the currently loaded K-factor, which is the authoritative way to confirm

what a board is actually using — including a value left over from a previous firmware.

## Determining the K-factor against a standard solution

**Engineering interpretation.** Because the firmware's core relationship is

`EC_mS_per_cm = V * K`, the K-factor is obtained by dividing the known conductivity of a

standard solution by the measured voltage, with the temperature correction applied.

### Un-compensated case (what `Node4_SMTP` effectively reports)

```text

K = EC_standard (mS/cm) / V_measured (V)

```

### Temperature-compensated case (what `Node4` uses)

Set the standard solution and the immersed probe to a known temperature `T`, read the

firmware-reported EC in µS/cm, and solve the firmware's own equation for `K`:

```text

EC_uS = (V * K) / ecCoefficient * 1000

      →  K = (EC_uS * ecCoefficient) / (V * 1000)

```

If the water is at exactly 25 °C, `ecCoefficient` is 1.0 and this reduces to

`K = EC_uS / (V * 1000)`.

**Recommendation.** Work at 25 °C wherever possible. It removes one unknown from the

derivation and removes any dependence on the correctness of the 0.0185/°C coefficient.

### Worked example

**Illustrative numbers only — not measured data.** Suppose the probe is immersed in a

1413 µS/cm standard at 25.0 °C and `STATUS` reports an EC voltage of `V = 0.1413 V`.

```text

ecCoefficient = 1.0 + 0.0185 * (25.0 - 25.0) = 1.0

K             = (1413 * 1.0) / (0.1413 * 1000) = 1413 / 141.3 = 10.00

```

That is close to the `9.997f` default, which is consistent with the default having been

derived from a standard solution of approximately 1413 µS/cm. That is an inference from

the numbers, not a documented fact.

### Step-by-step procedure

**Recommendation.**

1. Connect the debug UART at 115200 baud, send `HELP`, then `STATUS`. Record the current

   `ecKFactor`. Do not proceed if the other channels are obviously faulty — a shared

   supply or ground fault corrupts every analogue channel.

2. **Rinse the probe cell** with deionised water and fill it with the standard solution

   as the manufacturer instructs. Allow it to reach the solution temperature.

3. **Record the solution temperature** `T`. Ideally this is 25.0 °C.

4. Submerge the probe and stir gently. Wait for the reading to stabilise — the firmware

   takes no special settling action.

5. Send `STATUS`. Record the `EC -> ... Voltage` value as `V`.

6. Read the reported EC from the Node 4 LCD row 1 (`TU:… EC:…uS`) as `EC_uS`.

7. **Cross-check with an independent reference meter** in the same solution. If you do

   not have one, you cannot distinguish a K-factor error from a sensor error, and the

   procedure below is not meaningful.

8. Compute `K` using the appropriate equation above.

9. Compare with the stored value. If they agree within your uncertainty, stop and record.

10. Otherwise enter the new value:

    ```text

    SET:EC_K=10.000

    ```

11. Send `STATUS` and confirm the stored K matches what you entered, to three decimals.

12. Immerse the probe back in the standard and confirm the reported EC now matches the

    known value.

13. Power-cycle the node, send `STATUS` again, and confirm the K-factor **survived the

    reboot**. This is the persistence check.

14. Record the standard's nominal and certified conductivity, its temperature, the

    measured voltage, the K-factor before and after, and the readings in the maintenance

    log ([Maintenance](../field-service/maintenance.md)).

### Multi-point determination

**Recommendation.** If a range of standards is available, repeat steps 2–12 at several

conductivities and plot reported EC against known EC. A linear fit through the origin

confirms the model. Systematic curvature means the relationship is not a single

multiplicative constant, and no K-factor will fit all points — that is a sensor or

module limitation.

### What this calibration does not fix

- **Cell constant / probe geometry mismatch.** The K-factor absorbs one average scaling

  error. It cannot correct for a probe used in a flow cell of a different geometry.

- **Cable capacitance or a resistive cell at high frequency.** Not modelled at all.

- **Polarisation and fouling.** A fouled or poorly-conditioned cell drifts in a way a

  single constant does not track. Clean the cell and re-check before adjusting K.

- **Non-linear temperature response.** See the `ecCoefficient` caveat above.

- **Cross-reference to pH or ion-selective data.** The firmware has no such facility.

> **Not verified from the current source.** The EC module make, model and cell constant;

> the identity, lot and certified values of any calibration solutions; whether the

  > `9.997f` default was derived from a particular standard; and any accuracy

  > specification or traceability statement for the channel.

## Related pages

- [Calibration index](index.md)

- [Conductivity sensor](../sensors/conductivity.md)

- [pH calibration](ph.md) — same console, same NVS namespace

- [Node 4](../nodes/node4.md) · [Node 4 SMTP](../nodes/node4-smtp.md)

- [Troubleshooting: `EC:0`](../field-service/troubleshooting.md)
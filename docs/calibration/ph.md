---

title: pH Calibration

description: Node 4 pH calibration in NVS, the full serial console procedure, two-point buffer derivation and the limits of the legacy linear model.

---

# pH Calibration

The pH channel on Node 4 is the best-supported calibration in the project: two

constants live in non-volatile memory, they survive power cycles and reboots, and they

can be changed on a running board from the PC serial console. It is also the channel

most likely to be trusted beyond what it can deliver, so the model's limitations are

covered in detail below.

Claim types used throughout: **Firmware implementation**, **Engineering

interpretation**, **Recommendation**.

## Storage and defaults

**Firmware implementation.** The constants are stored with ESP32 `Preferences` in the

NVS namespace **`node4_cal`**:

| Key | `Node4` default | `Node4_SMTP` default |

|---|---|---|

| `phSlope` | `3.5f` | `3.5f` |

| `phOffset` | `-1.75f` | `0.0f` |

| `ecKFactor` | `9.997f` | `2.0f` |

### The default divergence is real and must not be smoothed over

The two Node 4 variants ship **different** defaults in the same namespace:

- `Node4` defaults `phOffset` to `-1.75f`.

- `Node4_SMTP` defaults `phOffset` to `0.0f`.

**Engineering interpretation.** An `phOffset` of −1.75 on a slope of 3.5 corresponds to

a zero-voltage intercept at pH 0.5, while an offset of 0.0 with the same slope

corresponds to an intercept at pH 0.0. These are materially different sensor mappings.

A technician who copies calibration values between the two variants without

re-deriving them will get a systematically wrong result, typically by about 1.75 pH

units.

There is a second, harder consequence: both variants read the **same** NVS keys. If a

board is flashed with `Node4_SMTP` over a board previously calibrated as `Node4`, the

stored values persist and are used unchanged — the variant's own default is only

consulted when the key is absent. Flashing the other variant therefore does **not**

reset the calibration. Use `RESET` (on `Node4`) or erase flash before swapping

variants.

### `Node4_SMTP` has no calibration console

**Firmware implementation.** `handleSerialCalibrationCommands()` and the `SET:` command

handling exist **only** in `Node4.ino`. `Node4_SMTP.ino` loads the same three NVS keys at

boot (`loadCalibration`) but exposes no command handler.

**Engineering interpretation.** On an `Node4_SMTP` board there is no supported way to

change these values at all: they can only be altered by editing the sketch defaults,

rebuilding and re-flashing, or by the NVS contents left over from a previous firmware.

This matters when planning a service visit.

## The firmware model

**Firmware implementation.** In `Task_Sensors_Node4`, on GPIO 13 with `ADC_11db`

attenuation, 12-bit:

```text

k              = 1.0 + 0.02 * (T - 25.0)

pHcalculated   = phSlope * V + phOffset

pH             = 7.0 + ((pHcalculated - 7.0) / k)

```

where `V` is the calibrated pin voltage from `readSensorVoltage()` (an average of 16

`analogReadMilliVolts()` samples) and `T` is the submerged DS18B20 reading, or 25.0 °C

if that probe is invalid.

Validity gate: the reading is accepted only if `0.02 <= V <= 3.30` **and**

`0.0 <= pH <= 14.0`.

### Honest limitations of this model

**Engineering interpretation.** Three things are worth stating plainly.

1. **It is a legacy linear approximation, not a Nernst model.** A real pH electrode

   response is exponential: the output voltage changes by roughly 59 mV per pH decade

   at 25 °C, and the slope itself is proportional to absolute temperature. A single

   straight line `pH = slope * V + offset` can only ever be locally correct over a

   narrow window. The source explicitly preserves the legacy model — it comments that

   the "existing calibration model preserved".

2. **The temperature compensation divides by a growing factor.** `1 + 0.02*(T - 25.0)`

   increases by 0.02 per °C, so at 45 °C the divisor is 1.4 and the reported pH is

   compressed toward 7; at 5 °C it is 0.6 and the deviation from 7 is stretched by a

   factor of 1.67. The compensation is applied as a divisor on the *deviation from pH

   7*, which means it enlarges deviations at low temperature and shrinks them at high

   temperature. It is not derived from the electrochemistry.

3. **The 0.02/°C coefficient has no cited source** in the repository. It is a literal.

## The serial calibration console

**Firmware implementation.** `Node4` runs the debug UART at **115200 baud**. Commands

are read with `readStringUntil('\n')` and then `trim()`ed, so they are **newline

terminated**. `HELP`, `STATUS` and `RESET` are matched case-insensitively; the `SET:`

prefixes are matched case-**sensitively** with `startsWith()`, so `SET:PH_S=` works and

`set:ph_s=` does not.

| Command | Effect | Validation | Persisted |

|---|---|---|---|

| `HELP` | Lists the commands | — | No |

| `STATUS` | Prints raw ADC, volts and the saved constants | — | No |

| `SET:PH_S=<val>` | Sets `phSlope` | **None** — any float accepted | Yes, `node4_cal` |

| `SET:PH_O=<val>` | Sets `phOffset` | **None** — any float accepted | Yes, `node4_cal` |

| `SET:EC_K=<val>` | Sets `ecKFactor` | Rejects `<= 0` with `[ERROR]` | Yes, `node4_cal` |

| `RESET` | `preferences.clear()` on `node4_cal`, then reloads defaults | — | Clears |

**Engineering interpretation.** The absence of range checking on the pH values is a real

hazard: `SET:PH_S=0` is accepted and persisted, and every subsequent pH reading collapses

to the offset. There is no undo other than `RESET` or re-issuing a correct command.

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

### Console session — what the output looks like

```text

--- Loaded Calibration Constants ---

pH Slope: 3.500 | pH Offset: -1.750 | EC K-Factor: 9.997

========== NODE 4 CALIBRATION DEBUG CONSOLE ==========

STATUS        - View current raw ADC and calculated values

SET:EC_K=<val>- Set and save EC K factor

SET:PH_S=<val>- Set and save pH slope

SET:PH_O=<val>- Set and save pH offset

RESET         - Reset calibration to factory defaults

=====================================================

--- Live Raw Sensor Diagnostics ---

pH   -> Raw ADC: 1462 | Voltage: 1.176V

EC   -> Raw ADC:  803 | Voltage: 0.647V | K: 9.997

Turb -> Raw ADC:  312 | Voltage: 0.251V

Saved Constants -> pH Slope: 3.500 | pH Offset: -1.750 | EC K: 9.997

[SUCCESS] pH Slope updated and saved: 3.412

[SUCCESS] pH Offset updated and saved: -1.689

[SUCCESS] Calibration reset to defaults.

```

The raw ADC values and voltages in that example are illustrative of the *format only*.

Do not treat them as measured values from any node.

### Step-by-step single-point offset procedure

**Recommendation.** This is the simplest field procedure and is adequate when you have

one trusted buffer and limited time. Prefer the two-point method below if you have two

buffers.

1. Connect a USB-serial cable to the Node 4 debug UART and open the port at

   **115200 baud, 8N1**. Send `HELP` and confirm the banner is returned. If nothing is

   returned, see

   [troubleshooting](../field-service/troubleshooting.md) before changing any

   calibration value.

2. Send `RESET` to start from a known state. Note the three values printed by

   `loadCalibration()`.

3. Send `STATUS`. Record `pH -> Raw ADC` and `Voltage`, and the current constants.

4. Prepare **pH 7.00** buffer. Follow the buffer manufacturer's instructions on

   preparation, rinsing and immersion depth — the firmware does not compensate for

   immersion depth, cable or junction-potential effects.

5. Immerse the electrode. Allow the reading to settle, then compare the **LCD pH** (Node

   4 row 0, `EV:… pH:…`) with the buffer value.

6. If the reading is already within tolerance, stop here and record it.

7. Correct the offset with a single command, then verify:

   ```text

   SET:PH_O=-1.750

   ```

   Replace the number with the corrected value you have calculated. The value must be

   entered to three decimals or better because the firmware stores a `float` and prints

   only three decimals.

8. Re-send `STATUS` to confirm the constant is the one you intended, and confirm the

   LCD pH against the buffer again.

9. Power-cycle the node and repeat steps 3 and 8. **The value must survive the reboot.**

   If it does not, the NVS write failed or the namespace was cleared — investigate

   before leaving site.

10. Record the buffer lot, its nominal pH, the temperature, the slope and offset in

    force, and the readings before and after.

### Full two-point buffer calibration

**Recommendation.** Use **pH 7.00** plus either **pH 4.00** or **pH 10.00**. pH 7 is

mandatory because the firmware's compensation formula pivots on 7.0.

1. Perform steps 1–3 of the single-point procedure.

2. **Set the temperature to 25 °C if you can.** At 25 °C the compensation divisor `k`

   equals 1.0 and the derivation reduces to the simple two-point form below. If you

   cannot control temperature, use the general form and read the submerged DS18B20

   temperature from the LCD row 2 (`ST:…C`) — the derivation below accounts for `k`.

3. Immerse the electrode in the **pH 7.00** buffer. Settle. Send `STATUS` and record the

   voltage as `V7`.

4. Rinse the electrode thoroughly with deionised water, blot (do not wipe the bulb), and

   immerse it in the **pH 4.00** or **pH 10.00** buffer. Settle. Record the voltage as

   `V4` (or `V10`).

5. Read the submerged probe temperature `T` from the LCD and compute:

   ```text

   k = 1.0 + 0.02 * (T - 25.0)

   ```

### Deriving slope and offset

**Engineering interpretation — algebra with the firmware's own model.**

The firmware computes `pH = 7.0 + (pHcalculated - 7.0) / k`. Requiring a reported value

of exactly 7 at voltage `V7` gives:

```text

7 = 7 + (slope*V7 + offset - 7)/k   →   slope*V7 + offset = 7

```

Requiring a reported value of exactly 4 at voltage `V4`:

```text

4 = 7 + (slope*V4 + offset - 7)/k   →   slope*V4 + offset = 7 - 3k

```

Subtracting the two equations eliminates the offset:

```text

slope * (V7 - V4) = 3k

```

so:

```text

slope = 3k / (V7 - V4)

offset = 7 - slope * V7

```

**Special case, T = 25 °C:** `k = 1.0`, giving the familiar two-point form:

```text

slope = 3 / (V7 - V4)

offset = 7 - slope * V7

```

**Worked example at 25 °C** — illustrative numbers only, not measured data. Suppose

`V7 = 1.180 V` and `V4 = 0.430 V`:

```text

slope  = 3 / (1.180 - 0.430) = 3 / 0.750 = 4.000

offset = 7 - 4.000 * 1.180   = 7 - 4.720   = 2.280

```

Enter them:

```text

SET:PH_S=4.000

SET:PH_O=2.280

```

Note that this offset is very different in sign from the `-1.75f` default. That is

expected: the default is a factory placeholder, not a measurement of any particular

electrode.

**Using pH 10 instead of pH 4:** require a reported value of exactly 10 at `V10`:

```text

10 = 7 + (slope*V10 + offset - 7)/k   →   slope*V10 + offset = 7 + 3k

```

giving:

```text

slope = 3k / (V7 - V10)

offset = 7 - slope * V7

```

**Recommendation.** Check the sign of `V7 - V4` (or `V7 - V10`) before entering

anything. A reversed voltage order produces a negative slope, which the firmware will

happily accept, persist, and use to report an inverted pH.

### What the two-point method cannot fix

- **Non-linearity.** The model is straight-line in voltage. If the electrode checks at

  7 and 4 but reads wrong at 9, no slope and offset will correct all three.

- **Offset drift of the reference/junction.** Symmetric drift moves both points

  together; the two-point fit absorbs some of it but the fit degrades.

- **Cable and immersion effects.** The firmware measures at the ESP32 pin. Long cables,

  high-impedance electrodes and low-quality buffer electrodes all shift `V7` and `V4`

  in ways no arithmetic constant can distinguish from real pH error.

- **Temperature.** The `0.02/°C` divisor is not derived from the electrochemistry, so

  the two-point fit at 25 °C does not guarantee accuracy at other temperatures.

## Verifying persistence

**Firmware implementation.** `loadCalibration()` is called once in `setup()`, before the

tasks are created, and reads from the `node4_cal` namespace. Writes use

`preferences.putFloat()` inside the command handler.

**Recommendation.** After any calibration change:

- [ ] Send `STATUS` and record the constants.

- [ ] Power-cycle the node (do not just reset the console).

- [ ] Send `STATUS` again and confirm the constants are unchanged.

- [ ] Confirm the LCD pH against the buffer once more.

If the values reverted, the write did not commit. Record that as a hardware/firmware

fault, not as a calibration outcome.

> **Not verified from the current source.** The pH module make, model, electrode

> (combination or single) and reference type; the identity of the buffer solutions used;

> any NVS write endurance or survivability testing; and any measured accuracy

> specification for the channel.

## Related pages

- [Calibration index](index.md)

- [pH sensor](../sensors/ph.md)

- [Conductivity calibration](conductivity.md) — shares the same console and namespace

- [Node 4](../nodes/node4.md) · [Node 4 SMTP](../nodes/node4-smtp.md)

- [Startup checklist](../field-service/startup-checklist.md)

- [Troubleshooting](../field-service/troubleshooting.md)
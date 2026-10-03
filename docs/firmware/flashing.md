---

title: Flashing The Firmware

description: Per-node flashing procedure for the CIRQUA ESP32 nodes, the UART pin conflicts to respect, and the expected first-boot serial output for each sketch.

---

# Flashing The Firmware

Each CIRQUA node is an independent ESP32 board with its own sketch. There is no

combined image, no bootloader project and no over-the-air update path in the

repository, so **flashing is a USB operation performed once per physical

node**, repeated four or five times.

<div class="cirqua-identity">

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Debug UART</span>

    <span class="cirqua-identity__value"><code>Serial</code> = UART0 at <strong>115200 baud</strong>, all five sketches</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Inter-node links</span>

    <span class="cirqua-identity__value"><code>HardwareSerial</code> UART1 and UART2 at <strong>9600 baud</strong>, <code>SERIAL_8N1</code></span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Link pins</span>

    <span class="cirqua-identity__value">UART1 on GPIO 25/26 or 32/33, UART2 on GPIO 32/33 — never GPIO 1/3</span>

  </div>

  <div class="cirqua-identity__item">

    <span class="cirqua-identity__label">Updates</span>

    <span class="cirqua-identity__value"><span class="cirqua-badge cirqua-badge--unknown">none</span> no OTA, no bootloader partition logic, no remote config</span>

  </div>

</div>

## The UART picture on every node

This is the thing to get right before you plug anything in.

| Port | Instance | Pins on the node | Baud | Direction | What it is for |

|---|---|---|---|---|---|

| UART0 | `Serial` | the board's native USB-serial / FTDI pins (GPIO 1 TX, GPIO 3 RX on a classic devkit) | 115200 | — | Debug output **and** the Node 4 calibration console. Never used for inter-node traffic. |

| UART1 | `HardwareSerial(1)` | Node 1: RX 32 / TX 33 · Nodes 2, 3, 4: RX 25 / TX 26 | 9600 | link to the immediate neighbour upstream | Telemetry |

| UART2 | `HardwareSerial(2)` | RX 32 / TX 33 (Node 4: commented `// To Controller (Mega)`) | 9600 | link downstream | Telemetry |

Because UART1 and UART2 are routed to **general-purpose GPIOs** and not to the

USB bridge, the following is true:

* The USB serial port used for flashing and for the serial monitor is **UART0

  and only UART0**. The inter-node links do not share those pins.

* `Serial` at 115200 baud carries `Serial.println`/`Serial.printf` output and,

  on Node 4, console input. It is independent of the 9600 baud links.

* Node 4's calibration console therefore arrives on the **same** USB serial port

  used for flashing — no second adapter is needed.

!!! danger "Disconnect anything driving the UART or strapping pins before uploading"

    The link pins (GPIO 25, 26, 32, 33) are ordinary GPIOs and the ESP32 does

    not drive them while in the ROM bootloader, so a neighbour usually cannot

    block an upload on its own. The risk comes from *external* circuits:

    level shifters, pull-ups, sensor breakout boards and transceivers wired to

    the same GPIOs can hold a pin in a state that changes boot behaviour.

    Practical rule for every node:

    * Power the target node **alone** for a first flash, or at minimum

      disconnect the inter-node wiring on **both** UARTs of that node.

    * Confirm no external pull-up exists on GPIO 0, 2, 12 or 15.

    * Remove or park the sensors connected to the strapping pins listed below.

## Boot-strapping pins — general ESP32 knowledge

!!! warning "This section is general ESP32 platform knowledge, not a finding in this firmware"

    The statements below describe the ESP32's documented strapping behaviour.

    They are **not** derived from the CIRQUA source, and the documentation set

    has not been checked against a specific board's schematic — no schematic

    exists in the repository. Treat them as precautions, not as verified facts

    about the deployed hardware.

    * GPIO 0, GPIO 2, GPIO 5, GPIO 12 and GPIO 15 are sampled at reset. Their

      level at reset can change the boot mode, and on the classic ESP32 GPIO 12

      (MTDI) additionally selects the flash voltage when it is high.

    * GPIO 15 low at reset selects a normal boot; a sensor or pull-up that

      forces it high can leave the board looking unresponsive to a normal flash

      attempt.

    * Where a board shows no serial output and will not accept an upload,

      disconnect the peripherals and power-cycle before assuming a fault.

CIRQUA's pin maps touch several strapping pins, which is why the precaution

above is worth reading rather than skipping:

| Node | Strapping pin used by this firmware | Function | Precaution |

|---|---|---|---|

| 1 | GPIO 2 | ultrasonic TRIG (output) | Output-only after boot; ensure no external circuit pulls it high at reset |

| 4 | GPIO 2 | ultrasonic **ECHO** (input) | A pull-down/up on ECHO is read at reset; keep it high-impedance or at a benign level when unpowered |

| 4 | GPIO 5 | DHT11 data (input) | Keep high-impedance at reset |

| 4 | GPIO 12 | EC analogue input | The classic flash-voltage strapping pin — the highest-risk one on this cluster |

| 4 SMTP | GPIO 2, GPIO 5, GPIO 12 | same functions as Node 4 | same precautions |

> **Engineering interpretation.** GPIO 12 as an EC input is workable because

> the sensor's analogue output is high-impedance-ish and the ESP32 samples the

> pin only momentarily at reset, but it does mean the EC channel's state during

> reset is not guaranteed by the node itself. If a Node 4 ever fails to boot

> after a power cycle, GPIO 12 is the first pin to inspect.

## Flashing procedure

1. Identify the node you are holding before you flash it. See

   [Node Identification](../field-service/node-identification.md)).

2. Disconnect the inter-node UART wiring from that node, both directions.

3. Disconnect the sensors on the strapping pins if convenient, particularly the

   EC probe on Node 4 (GPIO 12) and the DHT11 (GPIO 5).

4. Connect USB to the node's own USB-serial interface.

5. Put the board into download mode **only if** a normal upload fails:

   hold **BOOT**, press and release **EN**, release **BOOT**. The IDE's

   *Upload* command performs the same sequence automatically on most boards.

6. In the Arduino IDE: select the board, select the port, open the node's

   `.ino`, then **Sketch ▸ Upload**. See [Building](build.md)) for library

   installation and compile.

7. Open **Tools ▸ Serial Monitor** at **115200 baud**, **newline** line ending,

   no flow control.

8. Compare the output against the expected first-boot output for that node

   below.

9. Reset the board once (press **EN**) and confirm the output repeats — this

   distinguishes a one-shot ROM boot message from the firmware's own output.

10. Only when the node has passed its checklist should you reconnect the link

    wiring and power the cluster.

## Expected first-boot serial output

### Node 1 — `Node1.ino`

**Expected: no output at all.**

`setup()` opens `Serial` at 115200 baud, creates two mutexes and three tasks,

and prints nothing. There is no banner. The only strings Node 1 can emit on the

debug UART are fatal-trap messages:

```text

[FATAL ERROR] System Initialization Failed: <task or mutex name>. Halted.

```

Candidate names: `Mutex Allocation`, `N1_Sensors Task`, `N1_UART Task`,

`N1_LCD Task`. After a successful boot the only proof of life is the LCD: see

[Node 1 display](../nodes/node1.md#display-ui). A `STATUS:` line reading

`WAITING` is the expected state until Node 2 starts sending its echo frame.

### Node 2 — `Node2.ino`

**Expected: no output at all.**

Same situation as Node 1. The only possible message is:

```text

[FATAL ERROR] Node 2 Task Failed: <task or mutex name>

```

Candidate names: `Mutex Allocation Failure`, `Task N2_Sensors Creation`,

`Task N2_UART Creation`. Node 2 has no display, so its proof of life is

observed **indirectly**: Node 1's `STATUS:` line leaves `WAITING` and Node 2's

fields appear in the frames flowing towards Node 4. See

[Serial Links](../communication/serial-links.md)).

### Node 3 — `Node3.ino`

**Expected: no output at all.**

Node 3 is the only sketch with **no external library dependency** and no boot

message. Its only possible message is:

```text

[FATAL ERROR] Node 3 Task Failed: <task or mutex name>

```

Candidate names: `Mutex Allocation`, `N3_Flow Task Creation`,

`N3_UART Task Creation`. Proof of life is the presence of a `FLM:` field in the

frames arriving at Node 4, or of the Node 3 timeout fallback frame described on

[Fault Handling](../communication/fault-handling.md)).

### Node 4 — `Node4.ino`

Node 4 is the only node with a **documented boot banner**. `setup()` waits

500 ms, calls `loadCalibration()`, then the sensor task runs its

initialisation functions. Expected sequence:

```text

--- Loaded Calibration Constants ---

pH Slope: 3.500 | pH Offset: -1.750 | EC K-Factor: 9.997

[ADC] Resolution: 12-bit

[ADC] Attenuation: 11 dB

[ADC] Multi-sample filtering enabled

[DS18B20] Devices found: 1

[DHT11] Initialized

```

Then, for **every** upstream frame, a transaction block:

```text

================ [NODE 4 PACKET TRANSACTION] ================

[INCOMING] Raw Packet from Upstream: <frame>;

[CLEANED] Upstream Packet: <cleaned frame>

[LOCAL SENSORS] Current Node 4 Readings:

  - pH:       7.1 (Valid: YES)

  - Turbidity:12.0 NTU (Valid: YES)

  - EC:       845 uS/cm (Valid: YES)

  - TCV Volume:1234 L (Valid: YES)

[OUTGOING] Final Packet Sent Downstream: <frame>

=============================================================

```

The numeric values above are placeholders; the field labels, spacing and

precision are exactly those in the source. What matters for bring-up:

| Line | Interpretation if different |

|---|---|

| `--- Loaded Calibration Constants ---` | Missing ⇒ the sketch did not boot, or the wrong sketch is flashed |

| `pH Slope: … \| pH Offset: … \| EC K-Factor: …` | Values other than the defaults ⇒ NVS in flash already holds saved calibration. See [Configuration](configuration.md)) |

| `[DS18B20] Devices found: 0` | The 1-Wire probe is not detected; the next line warns explicitly and pH/EC compensation will fall back to 25 °C |

| `[DS18B20] WARNING: No temperature sensor detected!` | Printed immediately after the count line when it is zero |

| `[DHT11] Initialized` | Missing ⇒ `dhtN4.begin()` did not run; the LCD humidity row will read 0 |

| `[FATAL ERROR] Node 4 Task Failed: <name>` | Names: `Mutex Allocation`, `N4_Sensors Task`, `N4_UART Task`, `N4_LCD Task`. The node is halted and will print nothing further |

!!! warning "Node 4's debug output is continuous while the chain is healthy"

    The transaction block is printed once per received upstream frame, and the

    upstream routing task emits at a 50 ms cadence, so a healthy chain makes the

    115200 baud monitor scroll continuously.

    > **Engineering interpretation.** The block is roughly 500–700 bytes. At the

    > frame cadence the upstream routing task implies, that is close to the

    > order of the 115200 baud link's throughput. The consequence is that the

    > debug channel can become the bottleneck for the Node 4 UART task, and

    > lines will interleave. It is a diagnostic aid, not a data channel — the

    > telemetry on UART2 is unaffected by the print statements themselves.

### Node 4 SMTP variant — `Node4_SMTP.ino`

Different banner. `loadCalibration()` in this variant prints **nothing**, so the

first thing on the serial monitor is the network sequence from

`initNetworkAndTime()`:

```text

Connecting to Wi-Fi: YOUR_WIFI_SSID

......................

[INFO] Wi-Fi Connected!

[INFO] Synchronizing NTP time for Tunis...

[INFO] Current Epoch Time: 1780000000

```

or, on failure:

```text

Connecting to Wi-Fi: YOUR_WIFI_SSID

..............................

[ERROR] Wi-Fi Connection Failed!

```

`YOUR_WIFI_SSID` is the **placeholder** value in the committed source; the

firmware prints whatever is configured at build time. Thirty dots means thirty

failed 500 ms attempts. After the network step, this variant prints **no ADC,

DS18B20 or DHT messages** — those initialisation prints exist only in `Node4`.

Subsequent serial output from this variant is limited to:

```text

[SMTP SUCCESS] Email sent successfully!

[SMTP ERROR] Connect failed: <reason>

[SMTP ERROR] Send failed: <reason>

```

The `<reason>` string comes from the ESP Mail Client library and is

third-party text, not written by this firmware. Note that a Node 4 SMTP unit

therefore looks almost silent on a serial monitor even when it is working; the

LCD and the downstream frame are the better indicators.

!!! danger "Do not expect real credentials to appear here"

    The committed SMTP configuration is placeholder text. This documentation

    never shows a working SSID, password, mailbox address or app password. The

    extracted snippet is redacted automatically. Supply real values at build

    time from an untracked source and never commit them.

## Per-node checklist

### Node 1

- [ ] BOOT/EN sequence completed if needed.

- [ ] `Sketch ▸ Upload` completes without error.

- [ ] Serial monitor opens at 115200; **no output is expected** — confirm no

      `[FATAL ERROR] System Initialization Failed:` line.

- [ ] LCD backlight on; line 1 shows `C…L F…L`, line 4 shows

      `STATUS: WAITING` with the link disconnected.

- [ ] After connecting the link to a running Node 2, line 4 leaves `WAITING`

      within about 3 seconds (`RX_TIMEOUT_MS`).

- [ ] Lines 2 and 3 populate with `DO`, `T`, `AT`, `H` values.

### Node 2

- [ ] Upload completes.

- [ ] **No output expected** — confirm no `[FATAL ERROR] Node 2 Task Failed:`.

- [ ] With Node 1 and Node 3 running, confirm a `|DO:…|Temp:…|TBV:…|AT:…|AH:…|node2:1;`

      frame appears in both directions.

- [ ] Confirm `node2:` is `1` with all four sensor families healthy, and `0`

      when a probe is disconnected.

- [ ] Confirm the echo frame reaches Node 1 (Node 1's `STATUS:` leaves

      `WAITING`).

### Node 3

- [ ] Upload completes.

- [ ] **No output expected** — confirm no `[FATAL ERROR] Node 3 Task Failed:`.

- [ ] Confirm `|FLM:` appears in the frames arriving at Node 4.

- [ ] With the flow sensor disconnected, `FLM` should read `0.00` while

      `node3:` still reports `1` (the flow task marks the sample valid

      unconditionally).

- [ ] With the upstream link cut, confirm exactly **one** fallback frame is

      emitted and then silence until the link returns.

### Node 4

- [ ] Upload completes.

- [ ] Serial monitor shows the calibration banner, three `[ADC]` lines, the

      `[DS18B20]` device count and `[DHT11] Initialized`, in that order.

- [ ] `[DS18B20] Devices found:` is `1` with the probe connected.

- [ ] Transaction blocks appear once the upstream link is live.

- [ ] LCD shows `EV:`, `TU:`, `EC:`, `ST:`, `AH:` rows with plausible values.

- [ ] The calibration console responds: send `HELP` + newline and expect the

      command list — see [Configuration](configuration.md)).

- [ ] `STATUS` returns raw ADC counts and volts for pH, EC and turbidity.

### Node 4 SMTP

- [ ] Credentials supplied from an **untracked** source; the committed

      placeholders left untouched in the repository.

- [ ] Upload completes.

- [ ] `Connecting to Wi-Fi:` appears; then either `[INFO] Wi-Fi Connected!` or

      `[ERROR] Wi-Fi Connection Failed!`.

- [ ] On a real network, a startup e-mail is attempted once on every boot.

- [ ] `NTP` epoch advances past `1700000000` in

      `[INFO] Current Epoch Time:`.

- [ ] LCD and downstream frame behave as for Node 4, except `EC:` is shown in

      `mS`.

- [ ] Confirm the unit emits **its own** downstream field set (`EC` in mS/cm,

      `EV`, `ST`) and not `TCV`.

## Verifying the flash

After flashing, verify in this order — it moves from the node outwards:

| # | Check | Method | Pass condition |

|---|---|---|---|

| 1 | The right sketch is on the board | Boot banner, or the absence of one for Nodes 1–3 | Matches the node's expected output exactly |

| 2 | Tasks are running | LCD refresh (Nodes 1, 4), or a changing `FLM`/`TAV` value in the traffic | Values change at the documented cadence |

| 3 | Sensor validity flags | `node1:`, `node2:`, `node3:`, `node4:` in the frames | `1` when healthy |

| 4 | Calibration state | `STATUS` on Node 4 | Slope, offset and K-factor match what you intended |

| 5 | Link integrity | Capture the link between two nodes for 30 s | Frames every cycle, no truncated or interleaved text |

| 6 | Cluster completeness | Capture the Node 4 → controller link | All expected fields present, in the expected units |

!!! note "There is no version string on the wire or on the LCD"

    Neither the frame nor the display carries a firmware version or commit

    identifier. Recording which commit is on each board is a **manual** task —

    keep it with the node's field documentation. This is a real gap; see

    [Known Limitations](../validation/known-limitations.md).

## Related

* [Building](build.md)) — libraries and IDE setup.

* [Configuration](configuration.md)) — the Node 4 console and the constants.

* [Serial Links](../communication/serial-links.md)) — baud rates, buffers, link

  topology.

* [Node Identification](../field-service/node-identification.md)) — which board

  am I holding?

* [Hardware Validation](../validation/hardware-validation.md)) — the same

  procedures written as a bring-up protocol.

* [Known Limitations](../validation/known-limitations.md) — what the flash

  cannot tell you.
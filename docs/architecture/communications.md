---

title: Communications

description: The inter-node serial link contract for the CIRQUA ESP32 chain — 9600 8N1 on HardwareSerial, ASCII framing rules, and what the format cannot guarantee.

---

# Communications

## Physical link summary

All inter-node communication is **asynchronous serial over `HardwareSerial`**.

There is no network protocol, no addressing layer and no addressing scheme —

position in the chain is determined by wiring alone.

| Property | Value |

|---|---|

| Interface | `HardwareSerial` UART1 and UART2 |

| Baud rate | `INTERNODE_BAUD` = **9600** |

| Data format | `SERIAL_8N1` — 8 data bits, no parity, 1 stop bit, no flow control |

| Signal encoding | Plain ASCII, delimiter-separated key/value pairs |

| Debug port | `Serial.begin(115200)` — separate from the inter-node UARTs |

> **Not verified from the current source.** Cable type, length, gauge, connector

> pinouts, termination or shielding. No schematic exists in the repository. See

> <a href="../hardware/wiring.html">Hardware: Wiring</a>.

## Framing rules

| Rule | Value |

|---|---|

| Field separator | `|` |

| Key/value separator | `:` |

| Frame terminator | `;` followed by `\n` |

| Frame start | a leading `|` — frames begin `|TAV:...` |

| Health flag | one `nodeN` key per contributing node, `1` = all local validity flags true |

| Checksum | **none** |

| Sequence number | **none** |

| Acknowledgement | **none** |

| Retry | **none** |

Because `|` both terminates a field and starts a new frame, a new frame is

*always* introduced by a leading pipe. That is a deliberate, reflected design: it

lets the receiver resynchronise on delimiters alone, without any byte-counting or

timing discipline.

## Node 2's routing role

Node 2 sits between Node 1 and Node 3 and is the only node that terminates more

than one upstream link. It therefore parses, stores and re-emits rather than

blindly forwarding. Its routing is worth reading as the reference example of the

pattern:

```cpp

--8<-- "assets/snippets/node2-uart-routing.cpp"

```

<div class="cirqua-source">

<span class="cirqua-source__label">Source</span>

<a href="https://github.com/lestealthy/Cirqua/blob/db6d9b896341a9c7d8fd01913e854b663c110d55/FreeRTOS_Implementation/Node2/Node2.ino">lestealthy/Cirqua</a> ·

<code>FreeRTOS_Implementation/Node2/Node2.ino</code> ·

<code>Task_UART_Node2</code> ·

lines 259–370 · commit <code>db6d9b8</code>
</div>

## Receive buffers

| Node | Buffer |

|---|---|

| Node 1 | `String`, 256-byte cap, index reset at 250 |

| Node 2 | `char[128]` per link |

| Node 3 | `char[256]` |

| Node 4 | `char[384]`, assembled packet `char[512]` |

**On overflow the receiver resets its index**, discarding the frame in progress.

There is no partial-frame recovery and no re-request.

## The downstream link and the SMTP variant

The final hop leaves Node 4 over UART2 to the **Controller (Arduino Mega)**; the

pins are annotated `// To Controller (Mega)`. The controller has no code in this

repository.

The `Node4_SMTP` variant adds the only network path in the entire codebase:

| Aspect | Detail |

|---|---|

| Libraries | `WiFi.h`, `ESP_Mail_Client.h` |

| Network join | `WiFi.begin`, up to 30 attempts at 500 ms spacing |

| Time | `configTime(3600, 0, "pool.ntp.org", "time.nist.gov")` — UTC+1, **zero daylight saving**; waits for epoch > 1700000000, 15 retries |

| Transport | SSL (`esp_mail_secure_transport_ssl`), server `smtp.gmail.com:465` |

| Sender name | `WattLab Node 4` |

| Content | HTML, base64-encoded, high priority |

| Cadence | start-up e-mail on **every boot**, then a heartbeat every **86400 s** (24 h) with a **12 h** error cooldown, both epochs persisted in the `email_state` NVS namespace |

!!! danger "The committed network configuration is a placeholder"

    The Wi-Fi SSID, Wi-Fi password, sender address and recipient address in the

    committed source are **placeholders**, not working credentials. They must

    never be presented as a working configuration, and no credential value

    appears anywhere in this documentation. See

    <a href="../nodes/node4-smtp.html">Node 4 (SMTP)</a>.

The SMTP path is **fire-and-forget**: it carries telemetry out, and there is no

command or configuration downlink. It is not a substitute for a management link.

## Network configuration caveat

> **Engineering interpretation.** `configTime(3600, 0, ...)` is a fixed UTC+1 with

> daylight saving forced to zero. Tunis observes daylight saving, so during the

> summer the node's clock will be one hour behind local civil time and the

> timestamps on its e-mails will be one hour out. The firmware does not

> implement any seasonal adjustment.

## Continue

For the protocol definition itself, buffer handling and fault behaviour, see the

Communication section:

* <a href="../communication/index.html">Communication</a> — section index

* <a href="../communication/serial-links.html">Serial Links</a>

* <a href="../communication/message-format.html">Message Format</a>

* <a href="../communication/fault-handling.html">Fault Handling</a>

And for the wire content hop by hop, see <a href="data-flow.html">Data Flow</a>.


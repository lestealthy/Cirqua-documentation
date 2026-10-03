---
title: Communication
description: Index of the communication pages — the 9600 baud UART chain, the ASCII key/value telemetry protocol and the fault-handling behaviour of each link.
---

# Communication

The four CIRQUA nodes are chained over a single pair of UART lines each, and
speak an ASCII, delimiter-separated key/value protocol at **9600 baud, 8N1**.
This section documents the physical links, the wire format and what each node
does when something goes wrong.

| Page | What it covers |
|---|---|
| <a href="serial-links.html">Serial Links</a> | Physical link table — which UART instance and GPIO pair connects which nodes, plus cable and earthing guidance |
| <a href="message-format.html">Message Format</a> | **Authoritative protocol reference** — field dictionary, real frame examples for every link, and an explicit list of what the format does not guarantee |
| <a href="fault-handling.html">Fault Handling</a> | Timeouts, structural validation, the zero-reading ambiguity, and the fault-mode matrix |

## The short version

* The chain is a **line**: Node 1 → Node 2 → Node 3 → Node 4 → controller.
* Node 1 is the **head** and originates the upstream frame. Node 4 is the
  **tail** and forwards to the downstream controller.
* Node 2 additionally sends a **reverse echo** back to Node 1 for the Node 1
  display, and receives a reverse telemetry frame from Node 3.
* The wire format is ASCII: fields separated by `|`, key from value by `:`,
  frame terminated by `;` then a newline, with a **leading `|`**.
* Each frame carries **its own node health flag** — `node1` through `node4` —
  where `1` means every local validity flag on that node was true.
* There is **no checksum, no CRC, no sequence number, no acknowledgement and no
  retry**. Integrity is structural only.
* There is **no store-and-forward**. A broken link loses data permanently.

## Claim types used on these pages

* **Firmware implementation** — read from the source at commit `db6d9b8`.
* **Engineering interpretation** — labelled reasoning about why the code is as
  it is.
* **Recommendation** — advice from the documentation author.

## Related architecture pages

* <a href="../architecture/communications.html">Communications</a> — the
  architecture-layer view of the same links, framed against the rest of the
  system.
* <a href="../architecture/data-flow.html">Data Flow</a> — the step-by-step
  propagation of one frame through all four nodes.
* <a href="../architecture/node-topology.html">Node Topology</a> — the chain
  with node roles.

## Related pages elsewhere

* <a href="../rtos/tasks.html">RTOS Tasks</a> — the tasks that service each
  link.
* <a href="../hardware/gpio-map.html">GPIO Map</a> — the pins behind each link.
* <a href="../validation/known-limitations.html">Known Limitations</a> — the
  protocol weaknesses recorded across the project.

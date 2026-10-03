---
title: Architecture
description: Index of the architecture pages — layered system view, node topology, frame data flow, communications and timing for the ESP32 node chain.
---

# Architecture

This section describes how the four ESP32 nodes are put together: which
measurements exist, which task produces them, how a frame travels from one node
to the next, and how the timing works.

| Page | What it covers |
|---|---|
| <a href="system-architecture.html">System Architecture</a> | Layered view — sensing, RTOS, link, and the head/tail nodes — plus the full FreeRTOS task table |
| <a href="node-topology.html">Node Topology</a> | The UART chain, per-node UART assignments, the GPIO-conflict warning and the node role table |
| <a href="data-flow.html">Data Flow</a> | Step-by-step frame propagation with real `snprintf` formats and a sequence diagram of one full pass |
| <a href="communications.html">Communications</a> | Physical link summary, 9600 8N1 framing rules, and what the format does not guarantee |
| <a href="timing.html">Timing</a> | Task periods, poll cadence, lock timeouts, RX timeouts and the latency budget |

## The short version

* Every node is an **ESP32** running the Arduino ESP32 framework over FreeRTOS.
* Nodes are wired in a **line**: Node 1 → Node 2 → Node 3 → Node 4 → Controller.
* Node 1 is the **head**: it starts each frame. Node 4 is the **tail**: it ends
  the chain and forwards to the controller.
* Node 2 also sends a **reverse echo** back to Node 1 for the Node 1 display.
* The wire format is **ASCII, delimiter-separated key/value pairs** at
  **9600 baud, 8N1**.
* There is **no checksum, no CRC, no sequence number, no acknowledgement and no
  retry**. Integrity is structural only.

## Reading order

If you are new to the platform, read
<a href="node-topology.html">Node Topology</a> first so the physical chain is
clear, then <a href="data-flow.html">Data Flow</a> to see what actually goes over
it, then <a href="timing.html">Timing</a> to understand why a value can be
stale. <a href="system-architecture.html">System Architecture</a> is the
reference view for task names, stacks and core assignment.

For the framework-level detail, see <a href="../rtos/index.html">RTOS</a>; for the
link itself, see <a href="../communication/index.html">Communication</a>.

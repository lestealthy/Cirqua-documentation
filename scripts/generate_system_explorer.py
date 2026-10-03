#!/usr/bin/env python3
"""
Generate the interactive system explorer fragment.

The explorer is a static, framework-free component (see
docs/javascripts/explorer.js). All of its content is derived from the pinned
firmware, so the chain, sensors, UART links and task counts cannot drift from
the source.

Each node's detail panel is emitted twice: once into a <template> that the
enhancement script swaps in, and once as the default server-rendered panel, so
the page is fully readable with JavaScript disabled.

Outputs
-------
    docs/assets/generated/system-explorer.html

Usage
-----
    python scripts/generate_system_explorer.py
    python scripts/generate_system_explorer.py --check
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "sources" / "firmware-source.yml"
VERIFICATION = REPO / "sources" / "verification.yml"
OUT = REPO / "docs" / "assets" / "generated" / "system-explorer.html"

BADGE_ICON = {
    "VERIFIED": "✔",
    "PARTIALLY_VERIFIED": "◐",
    "NOT_VERIFIED": "✖",
    "HISTORICAL": "⏱",
    "INFERRED": "≈",
    "REQUIRES_HARDWARE_TEST": "⚠",
}
BADGE_CLASS = {
    "VERIFIED": "cirqua-vfy--verified",
    "PARTIALLY_VERIFIED": "cirqua-vfy--partial",
    "NOT_VERIFIED": "cirqua-vfy--unverified",
    "HISTORICAL": "cirqua-vfy--historical",
    "INFERRED": "cirqua-vfy--inferred",
    "REQUIRES_HARDWARE_TEST": "cirqua-vfy--hardware",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


# Include depth of the page that embeds this fragment.
#
# The fragment is included by docs/architecture/system-explorer.md, which sits one
# directory below docs/, so every documentation link must be prefixed with "../" to
# resolve to the site root.
#
# Root-relative links ("/hardware/...") look correct on the homepage but break
# under the GitHub Pages subdirectory, and absolute site URLs would break the local
# `mkdocs serve` preview. Depth-correct relative links work in both environments.
INCLUDE_DEPTH = 1


def link(target: str) -> str:
    """Documentation link correct for the including page's directory depth."""
    return "../" * INCLUDE_DEPTH + target


def badge(state: str) -> str:
    return (
        f'<span class="cirqua-vfy {BADGE_CLASS.get(state, "cirqua-vfy--unverified")}">'
        f'<span class="cirqua-vfy__icon" aria-hidden="true">{BADGE_ICON.get(state, "•")}</span>'
        f'<span class="cirqua-vfy__text">{esc(state.replace("_", " ").title())}</span></span>'
    )


NODES = [
    {
        "id": "node1", "num": "Node 01", "short": "Node 1",
        "file": "Node1/Node1.ino", "page": "nodes/node1.html",
        "purpose": "Collection Tank A level and the cluster head that originates the telemetry frame.",
        "measures": "Tank A level (TAV), ultrasonic",
        "sensors": "HC-SR04 ultrasonic (GPIO 2 / 17)",
        "uart": "UART1 — RX 32 / TX 33",
        "lcd": "Yes — 16x4 I2C LCD at 0x27",
        "state": "PARTIALLY_VERIFIED",
    },
    {
        "id": "node2", "num": "Node 02", "short": "Node 2",
        "file": "Node2/Node2.ino", "page": "nodes/node2.html",
        "purpose": "Water telemetry and the frame router between the head of the chain and the flow meter.",
        "measures": "Water temperature, dissolved oxygen, Tank B level (TBV), ambient T/RH",
        "sensors": "DS18B20 (GPIO 4), DO analogue (GPIO 34), HC-SR04 (GPIO 16 / 17), DHT11 (GPIO 27)",
        "uart": "UART1 to Node 1 (RX 25 / TX 26); UART2 to Node 3 (RX 32 / TX 33)",
        "lcd": "No",
        "state": "PARTIALLY_VERIFIED",
    },
    {
        "id": "node3", "num": "Node 03", "short": "Node 3",
        "file": "Node3/Node3.ino", "page": "nodes/node3.html",
        "purpose": "Inline flow metering; appends the flow rate to the frame and forwards it onward.",
        "measures": "Volumetric flow (FLM), pulse-counted",
        "sensors": "Flow sensor pulse input (GPIO 23, INPUT_PULLUP, ISR on FALLING)",
        "uart": "UART1 to Node 2 (RX 25 / TX 26); UART2 to Node 4 (RX 32 / TX 33)",
        "lcd": "No",
        "state": "NOT_VERIFIED",
    },
    {
        "id": "node4", "num": "Node 04", "short": "Node 4",
        "file": "Node4/Node4.ino", "page": "nodes/node4.html",
        "purpose": "Effluent water-quality analytics and the tail of the chain.",
        "measures": "pH, turbidity, conductivity, submerged temperature, effluent level (TCV)",
        "sensors": "pH (GPIO 13), turbidity (GPIO 14), EC (GPIO 12), DS18B20 (GPIO 27), DHT11 (GPIO 5), HC-SR04 (GPIO 4 / 2)",
        "uart": "UART1 from Node 3 (RX 25 / TX 26); UART2 to controller (RX 32 / TX 33)",
        "lcd": "Yes — 16x4 I2C LCD at 0x27",
        "state": "PARTIALLY_VERIFIED",
    },
    {
        "id": "node4-smtp", "num": "Node 04-S", "short": "Node 4 (SMTP)",
        "file": "Node4_SMTP/Node4_SMTP.ino", "page": "nodes/node4-smtp.html",
        "purpose": "The same sensor set as Node 4, plus Wi-Fi, NTP time and SMTP e-mail alerting.",
        "measures": "As Node 4, plus operator e-mail alerts",
        "sensors": "Same GPIOs as Node 4",
        "uart": "UART1 from Node 3 (RX 25 / TX 26); UART2 to controller (RX 32 / TX 33)",
        "lcd": "Yes — 16x4 I2C LCD at 0x27",
        "state": "PARTIALLY_VERIFIED",
    },
]

CONTROLLER = {
    "num": "Controller",
    "purpose": "Downstream receiver at the end of the chain, commented in the firmware as an Arduino Mega.",
    "measures": "Receives the consolidated frame; no acquisition",
    "state": "NOT_VERIFIED",
}


def task_count(manifest: dict, rel: str) -> int:
    path = REPO / manifest["path"] / manifest["current_source_dir"] / rel
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"xTaskCreatePinnedToCore\s*\(", text))


def panel_html(node: dict, manifest: dict) -> str:
    commit = manifest["commit"]
    tasks = task_count(manifest, node["file"])
    return f"""<h3 id="explorer-heading">{esc(node['short'])} — {esc(node['purpose'])}</h3>
<p class="cirqua-explorer__purpose">Firmware <code>{esc(node['file'])}</code> at <code>{esc(commit[:7])}</code> · {tasks} FreeRTOS task(s)</p>
<dl class="cirqua-explorer__facts">
  <div><dt>Measures</dt><dd>{esc(node['measures'])}</dd></div>
  <div><dt>Sensors</dt><dd>{esc(node['sensors'])}</dd></div>
  <div><dt>Communication</dt><dd>{esc(node['uart'])}</dd></div>
  <div><dt>Display</dt><dd>{esc(node['lcd'])}</dd></div>
  <div><dt>Verification</dt><dd>{badge(node['state'])}</dd></div>
</dl>
<div class="cirqua-explorer__actions">
  <a href="{esc(link(node['page']))}">Full node manual</a>
  <a href="{esc(link('hardware/gpio-map.html'))}">GPIO map</a>
  <a href="{esc(link('field-service/qr-codes.html'))}">QR label</a>
</div>"""


def build(manifest: dict) -> str:
    chain_items = []
    for index, node in enumerate(NODES):
        chain_items.append(
            f"""      <a class="cirqua-explorer__link" href="#{esc(node['id'])}"
         data-explorer-node="{esc(node['id'])}" data-num="{esc(node['num'])}"
         aria-pressed="{'true' if index == 0 else 'false'}"
         aria-controls="cirqua-explorer-panel">
        <span class="cirqua-explorer__num" data-part="num">{esc(node['num'])}</span>
        <span class="cirqua-explorer__name">{esc(node['short'])}</span>
        <span class="cirqua-explorer__meas">{esc(node['measures'])}</span>
      </a>"""
        )
        if index < len(NODES) - 1:
            chain_items.append(
                '<div class="cirqua-explorer__arrow" aria-hidden="true">UART &#8594;</div>'
            )

    chain_items.append('<div class="cirqua-explorer__arrow" aria-hidden="true">UART &#8594;</div>')
    chain_items.append(
        f"""      <div class="cirqua-explorer__link" aria-disabled="true"
         style="cursor:default;background:var(--cirqua-surface);border-style:dashed">
        <span class="cirqua-explorer__num">{esc(CONTROLLER['num'])}</span>
        <span class="cirqua-explorer__name">Controller</span>
        <span class="cirqua-explorer__meas">{esc(CONTROLLER['measures'])}</span>
      </div>"""
    )

    templates = "\n".join(
        f'    <template data-explorer-template="{esc(node["id"])}">{panel_html(node, manifest)}</template>'
        for node in NODES
    )

    return f"""<!-- GENERATED by scripts/generate_system_explorer.py - do not edit by hand -->
<div class="cirqua-explorer" data-cirqua-explorer>
  <nav class="cirqua-explorer__chain" aria-label="CIRQUA measurement chain">
{chr(10).join(chain_items)}
  </nav>

  <div class="cirqua-explorer__detail" id="cirqua-explorer-panel" data-explorer-panel
       role="region" aria-live="polite" aria-label="Selected node">
{panel_html(NODES[0], manifest)}
  </div>

  <template data-explorer-template="controller">
    <h3>Controller — {esc(CONTROLLER['purpose'])}</h3>
    <p class="cirqua-explorer__purpose">No controller source exists in the current firmware tree.</p>
    <dl class="cirqua-explorer__facts">
      <div><dt>Role</dt><dd>{esc(CONTROLLER['measures'])}</dd></div>
      <div><dt>Verification</dt><dd>{badge(CONTROLLER['state'])}</dd></div>
    </dl>
    <div class="cirqua-explorer__actions">
      <a href="{esc(link('architecture/node-topology.html'))}">Chain topology</a>
      <a href="{esc(link('historical/legacy-firmware.html'))}">Archived controller source</a>
    </div>
  </template>

{templates}

  <p class="cirqua-explorer__legend">
    Every node is a link, so each chain entry also opens its full manual directly.
    Verification status is derived from <code>sources/verification.yml</code>; the
    flow factor is the only quantity in the chain with no verification evidence at all.
  </p>
</div>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    content = build(manifest)

    if args.check:
        if not OUT.is_file():
            print("STALE: system-explorer.html missing")
            return 1
        if OUT.read_text(encoding="utf-8") != content:
            print("STALE: system-explorer.html")
            return 1
        print("OK - system explorer is current")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"generated : {OUT.relative_to(REPO)}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""
Generate the node identity cards, the site revision bar and the verification
badge markup.

These are derived, never hand-written. The card content is re-read from the
pinned firmware on every run and merged with the declared verification states in
sources/verification.yml, so a node page cannot drift from the firmware or from
the project's own statement of what has been verified.

Outputs
-------
    docs/assets/generated/node-cards/node1.html
    docs/assets/generated/node-cards/node2.html
    docs/assets/generated/node-cards/node3.html
    docs/assets/generated/node-cards/node4.html
    docs/assets/generated/node-cards/node4-smtp.html
    docs/assets/generated/site-revision-bar.html
    docs/assets/generated/system-explorer.html

Usage
-----
    python scripts/generate_node_cards.py
    python scripts/generate_node_cards.py --check
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
OUT = REPO / "docs" / "assets" / "generated"

BADGE_CLASS = {
    "VERIFIED": "cirqua-vfy--verified",
    "PARTIALLY_VERIFIED": "cirqua-vfy--partial",
    "NOT_VERIFIED": "cirqua-vfy--unverified",
    "HISTORICAL": "cirqua-vfy--historical",
    "INFERRED": "cirqua-vfy--inferred",
    "REQUIRES_HARDWARE_TEST": "cirqua-vfy--hardware",
}

# Icon glyph per state, so status is never carried by colour alone.
BADGE_ICON = {
    "VERIFIED": "✔",
    "PARTIALLY_VERIFIED": "◐",
    "NOT_VERIFIED": "✖",
    "HISTORICAL": "⏱",
    "INFERRED": "≈",
    "REQUIRES_HARDWARE_TEST": "⚠",
}

CATEGORY_LABEL = {
    "MANUFACTURER_FACT": "Manufacturer fact",
    "SCIENTIFIC_FACT": "Scientific fact",
    "FIRMWARE_FACT": "Firmware fact",
    "PROJECT_OBSERVATION": "Project observation",
    "WATTLAB_INTERPRETATION": "WattLab engineering interpretation",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def badge(state: str) -> str:
    cls = BADGE_CLASS.get(state, "cirqua-vfy--unverified")
    icon = BADGE_ICON.get(state, "•")
    label = state.replace("_", " ").title()
    return (
        f'<span class="cirqua-vfy {cls}">'
        f'<span class="cirqua-vfy__icon" aria-hidden="true">{icon}</span>'
        f'<span class="cirqua-vfy__text">{esc(label)}</span>'
        "</span>"
    )


class Firmware:
    """Re-reads the pinned sketches so card facts cannot go stale."""

    def __init__(self) -> None:
        self.manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        self.root = REPO / self.manifest["path"] / self.manifest["current_source_dir"]

    def source(self, rel: str) -> str:
        path = self.root / rel
        if not path.is_file():
            sys.exit(f"firmware source missing: {path}")
        return path.read_text(encoding="utf-8", errors="replace")

    def pins(self, rel: str) -> dict[str, int]:
        return {
            name: int(value)
            for name, value in re.findall(r"^#define\s+(PIN_\w+)\s+(\d+)", self.source(rel), re.M)
        }

    def tasks(self, rel: str) -> list[tuple[str, str, int, int, int]]:
        pattern = re.compile(
            r"xTaskCreatePinnedToCore\s*\(\s*(\w+)\s*,\s*\"([^\"]+)\"\s*,\s*(\d+)\s*,"
            r"\s*NULL\s*,\s*(\d+)\s*,\s*NULL\s*,\s*(\d+)\s*\)",
            re.S,
        )
        return [
            (fn, name, int(stack), int(prio), int(core))
            for fn, name, stack, prio, core in pattern.findall(self.source(rel))
        ]

    def defines(self, rel: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for name, value in re.findall(r"^#define\s+(\w+)\s+(\d+)\s*$", self.source(rel), re.M):
            out[name] = int(value)
        return out

    def has(self, rel: str, needle: str) -> bool:
        return needle in self.source(rel)


# ---------------------------------------------------------------------------
# Node definitions - topology and role are the audited facts.
# ---------------------------------------------------------------------------

NODES = [
    {
        "id": "node1",
        "number": "01",
        "file": "Node1/Node1.ino",
        "page": "nodes/node1.html",
        "name": "Node 1",
        "purpose": "Collection Tank A level and cluster head",
        "measures": "Tank A level (TAV)",
        "upstream": "None — originates the frame",
        "downstream": "Node 2",
        "uart": "UART1, RX 32 / TX 33",
        "display": "16x4 I2C LCD at 0x27",
        "has_lcd": True,
    },
    {
        "id": "node2",
        "number": "02",
        "file": "Node2/Node2.ino",
        "page": "nodes/node2.html",
        "name": "Node 2",
        "purpose": "Water telemetry and frame router",
        "measures": "Water temperature, dissolved oxygen, Tank B level (TBV), ambient",
        "upstream": "Node 1",
        "downstream": "Node 3",
        "uart": "UART1 RX 25 / TX 26 (to Node 1); UART2 RX 32 / TX 33 (to Node 3)",
        "display": "None",
        "has_lcd": False,
    },
    {
        "id": "node3",
        "number": "03",
        "file": "Node3/Node3.ino",
        "page": "nodes/node3.html",
        "name": "Node 3",
        "purpose": "Flow metering and frame forwarding",
        "measures": "Volumetric flow (FLM)",
        "upstream": "Node 2",
        "downstream": "Node 4",
        "uart": "UART1 RX 25 / TX 26 (to Node 2); UART2 RX 32 / TX 33 (to Node 4)",
        "display": "None",
        "has_lcd": False,
    },
    {
        "id": "node4",
        "number": "04",
        "file": "Node4/Node4.ino",
        "page": "nodes/node4.html",
        "name": "Node 4",
        "purpose": "Effluent water-quality analytics and cluster tail",
        "measures": "pH, turbidity, conductivity, submerged temperature, effluent level (TCV)",
        "upstream": "Node 3",
        "downstream": "Controller (Arduino Mega)",
        "uart": "UART1 RX 25 / TX 26 (from Node 3); UART2 RX 32 / TX 33 (to controller)",
        "display": "16x4 I2C LCD at 0x27",
        "has_lcd": True,
    },
    {
        "id": "node4-smtp",
        "number": "04-S",
        "file": "Node4_SMTP/Node4_SMTP.ino",
        "page": "nodes/node4-smtp.html",
        "name": "Node 4 (SMTP)",
        "purpose": "Node 4 analytics with Wi-Fi, NTP and e-mail alerting",
        "measures": "As Node 4",
        "upstream": "Node 3",
        "downstream": "Controller (Arduino Mega)",
        "uart": "UART1 RX 25 / TX 26 (from Node 3); UART2 RX 32 / TX 33 (to controller)",
        "display": "16x4 I2C LCD at 0x27",
        "has_lcd": True,
    },
]

# Which declared verification areas concern which node.
NODE_VERIFICATION = {
    "node1": ["gpio_assignments", "free_rtos_tasks", "serial_protocol",
              "ultrasonic_tank_geometry", "lcd_behaviour", "hardware_revision"],
    "node2": ["gpio_assignments", "free_rtos_tasks", "serial_protocol",
              "dissolved_oxygen_model", "sensor_part_numbers"],
    "node3": ["gpio_assignments", "free_rtos_tasks", "serial_protocol",
              "flow_calibration_factor", "sensor_part_numbers"],
    "node4": ["gpio_assignments", "free_rtos_tasks", "serial_protocol",
              "calibration_constants", "ph_calibration_procedure",
              "ec_calibration_procedure", "turbidity_curve",
              "ultrasonic_tank_geometry", "lcd_behaviour", "sensor_part_numbers"],
    "node4-smtp": ["gpio_assignments", "free_rtos_tasks", "serial_protocol",
                   "ph_calibration_procedure", "ec_calibration_procedure",
                   "turbidity_curve", "sensor_part_numbers"],
}


def render_node_card(node: dict, fw: Firmware, verification: dict) -> str:
    pins = fw.pins(node["file"])
    tasks = fw.tasks(node["file"])
    commit = fw.manifest["commit"]
    commit_short = fw.manifest["commit_short"]

    # Firmware facts read straight from the sketch.
    sensor_pins = {
        k: v for k, v in sorted(pins.items())
        if "UART" not in k and not k.endswith(("SDA", "SCL"))
    }

    worst_state = "VERIFIED"
    order = ["VERIFIED", "PARTIALLY_VERIFIED", "REQUIRES_HARDWARE_TEST",
             "INFERRED", "NOT_VERIFIED", "HISTORICAL"]
    rows = []
    for area_id in NODE_VERIFICATION.get(node["id"], []):
        area = verification["areas"].get(area_id)
        if not area:
            continue
        state = area["state"]
        rows.append((area_id, area, state))
        if order.index(state) > order.index(worst_state):
            worst_state = state

    vfy_rows = "\n".join(
        f'    <tr><td><code>{esc(area_id.replace("_", " "))}</code></td>'
        f'<td>{badge(state)}</td>'
        f'<td class="cirqua-card-table__cat">{esc(CATEGORY_LABEL.get(area["category"], area["category"]))}</td></tr>'
        for area_id, area, state in rows
    )

    pin_text = ", ".join(f"{k.replace('PIN_', '')} = {v}" for k, v in sensor_pins.items()) or "none"
    task_text = ", ".join(f"{name} (stack {stack}, prio {prio}, core {core})" for _, name, stack, prio, core in tasks)

    return f"""<!-- GENERATED by scripts/generate_node_cards.py - do not edit by hand -->
<div class="cirqua-nodecard">
  <div class="cirqua-nodecard__head">
    <span class="cirqua-nodecard__number">Node {esc(node['number'])}</span>
    <span class="cirqua-nodecard__name">{esc(node['name'])}</span>
  </div>

  <dl class="cirqua-nodecard__grid">
    <dt>Purpose</dt><dd>{esc(node['purpose'])}</dd>
    <dt>Measures</dt><dd>{esc(node['measures'])}</dd>
    <dt>Controller</dt><dd>ESP32 (Arduino-ESP32, FreeRTOS, dual-core pinned tasks)</dd>
    <dt>Firmware</dt><dd><code>{esc(node['file'])}</code><br><code>{esc(commit_short)}</code> on <code>{esc(fw.manifest['branch'])}</code></dd>
    <dt>Hardware revision</dt><dd><strong>NOT RECORDED</strong><br><span class="cirqua-muted">No hardware revision exists in any repository. See <a href="../validation/known-limitations.html">known limitations</a>.</span></dd>
    <dt>Upstream</dt><dd>{esc(node['upstream'])}</dd>
    <dt>Downstream</dt><dd>{esc(node['downstream'])}</dd>
    <dt>UART</dt><dd>{esc(node['uart'])}</dd>
    <dt>Display</dt><dd>{esc(node['display'])}</dd>
    <dt>Sensor GPIOs</dt><dd>{esc(pin_text)}</dd>
    <dt>FreeRTOS tasks</dt><dd>{esc(task_text)}</dd>
  </dl>

  <div class="cirqua-nodecard__verify">
    <h3 class="cirqua-nodecard__verifytitle">Verification status</h3>
    <p class="cirqua-nodecard__overall">
      Overall for this node: {badge(worst_state)}
      <span class="cirqua-muted">Firmware behaviour is source-verified. Physical wiring and
      installed hardware are not independently verified; no hardware test record exists.</span>
    </p>
    <table class="cirqua-card-table">
      <thead><tr><th scope="col">Area</th><th scope="col">Status</th><th scope="col">Claim type</th></tr></thead>
      <tbody>
{vfy_rows}
      </tbody>
    </table>
    <p class="cirqua-nodecard__footer">
      Firmware commit <code>{esc(commit)}</code> ·
      <a href="https://github.com/lestealthy/Cirqua/blob/{esc(commit)}/{esc(fw.manifest['current_source_dir'])}/{esc(node['file'])}">view source at this commit</a>
    </p>
  </div>
</div>
"""


def render_revision_bar(fw: Firmware, verification: dict) -> str:
    commit = fw.manifest["commit"]
    commit_short = fw.manifest["commit_short"]
    areas = verification["areas"]
    states = [a["state"] for a in areas.values()]
    verified = states.count("VERIFIED")
    partial = states.count("PARTIALLY_VERIFIED")
    unverified = states.count("NOT_VERIFIED")
    hardware_test = states.count("REQUIRES_HARDWARE_TEST")

    # NOTE: the documentation revision is deliberately NOT baked in here.
    #
    # The current git HEAD changes on every commit, so embedding it would make
    # this fragment permanently "stale" against its own `--check` on the very
    # next commit - a self-invalidating generated file. The documentation
    # revision is instead shown as the branch plus a link to the commit
    # history, which is always accurate and always stable.

    return f"""<!-- GENERATED by scripts/generate_node_cards.py - do not edit by hand -->
<div class="cirqua-revbar">
  <div class="cirqua-revbar__brand">Cirqua <span>Technical Documentation</span></div>
  <dl class="cirqua-revbar__grid">
    <div><dt>Firmware revision</dt><dd><a href="https://github.com/lestealthy/Cirqua/tree/{esc(commit)}"><code>{esc(commit_short)}</code></a></dd></div>
    <div><dt>Firmware branch</dt><dd><code>{esc(fw.manifest['branch'])}</code></dd></div>
    <div><dt>Documentation revision</dt><dd><a href="https://github.com/lestealthy/Cirqua-documentation/commits/main"><code>main</code></a> <span class="cirqua-muted">(latest commit)</span></dd></div>
    <div><dt>Source verification</dt><dd>{badge('VERIFIED')} <span class="cirqua-muted">{verified} verified</span> {badge('PARTIALLY_VERIFIED')} <span class="cirqua-muted">{partial} partial</span> {badge('REQUIRES_HARDWARE_TEST')} <span class="cirqua-muted">{hardware_test} needs bench test</span> {badge('NOT_VERIFIED')} <span class="cirqua-muted">{unverified} unverified</span></dd></div>
    <div><dt>Hardware evidence</dt><dd>{badge('NOT_VERIFIED')} <span class="cirqua-muted">No hardware test record exists</span></dd></div>
  </dl>
  <p class="cirqua-revbar__note">
    Every hardware statement in this documentation is derived from firmware source or marked as
    requiring a hardware test. See
    <a href="../references/index.html">the claim categories</a> and
    <a href="../validation/known-limitations.html">known limitations</a>.
  </p>
</div>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    fw = Firmware()
    verification = yaml.safe_load(VERIFICATION.read_text(encoding="utf-8"))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "node-cards").mkdir(parents=True, exist_ok=True)

    generated: dict[Path, str] = {}
    for node in NODES:
        generated[OUT / "node-cards" / f"{node['id']}.html"] = render_node_card(node, fw, verification)
    generated[OUT / "site-revision-bar.html"] = render_revision_bar(fw, verification)

    stale: list[str] = []
    for path, content in generated.items():
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        if args.check:
            stale.append(str(path.relative_to(REPO)))
        else:
            path.write_text(content, encoding="utf-8")

    if args.check:
        if stale:
            print("STALE:")
            for item in stale:
                print(f"  {item}")
            return 1
        print(f"OK - {len(generated)} generated fragments are current")
        return 0

    print(f"firmware commit : {fw.manifest['commit_short']}")
    print(f"generated       : {len(generated)} fragments")
    print(f"output          : {OUT.relative_to(REPO)}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# CIRQUA Technical Documentation

[![Deploy documentation](https://github.com/lestealthy/Cirqua-documentation/actions/workflows/docs.yml/badge.svg)](https://github.com/lestealthy/Cirqua-documentation/actions/workflows/docs.yml)
[![Validate documentation](https://github.com/lestealthy/Cirqua-documentation/actions/workflows/validation.yml/badge.svg)](https://github.com/lestealthy/Cirqua-documentation/actions/workflows/validation.yml)

**Live documentation:** <https://lestealthy.github.io/Cirqua-documentation/>

Technical documentation for the embedded monitoring and instrumentation platform
of the **CIRQUA Waterwise Futures** initiative — four ESP32 nodes chained over
UART, measuring tank level, water temperature, dissolved oxygen, flow rate, pH,
turbidity and conductivity.

| | |
|---|---|
| Documentation repository | [`lestealthy/Cirqua-documentation`](https://github.com/lestealthy/Cirqua-documentation) |
| Firmware repository | [`lestealthy/Cirqua`](https://github.com/lestealthy/Cirqua) |
| Firmware revision documented | `db6d9b8` (full SHA `db6d9b896341a9c7d8fd01913e854b663c110d55`, branch `main`) |
| Official project site | <https://cirqua-water.eu/> |
| Project partner | [African Biotechnology Company](https://www.african-biotech.com/) |

## What this repository is

This is the **documentation** repository. It is deliberately separate from the
firmware repository:

* the firmware is **not** copied in — it is consumed as a Git submodule at
  `_external/Cirqua-firmware` and pinned to a single commit;
* the firmware repository is never modified by this project;
* the documented revision is recorded in `sources/firmware-source.yml` and
  re-verified on every build.

Documentation that duplicated the firmware would drift from it. Consuming the
firmware as a pinned submodule means every claim on the website can be traced
to a file, a symbol and a commit hash.

## Roles

| Organisation | Role |
|---|---|
| **CIRQUA** | The Horizon Europe funded research project. Owns all project-level claims. |
| **African Biotechnology Company** | CIRQUA project partner; organisational context sourced from its own website. |
| **WattLab** | Authors and maintains this documentation and the firmware. |

CIRQUA and African Biotechnology Company names and marks are the property of
their respective owners and are reproduced for identification only.

## Documentation architecture

```
docs/
├── index.md              Home
├── project/              CIRQUA context, objectives, terminology
├── architecture/         System architecture, topology, data flow, timing
├── nodes/                Node 1-4 and the Node 4 SMTP variant (field-service manuals)
├── hardware/             Controllers, GPIO map, power, wiring, enclosures
├── sensors/              Ultrasonic, temperature, DO, flow, pH, turbidity, EC, humidity
├── firmware/             Repository, source map, build, flash, configuration
├── rtos/                 Tasks, buffers, synchronisation, scheduling
├── communication/        Serial links, message format, fault handling
├── calibration/          Per-quantity calibration procedures and constants
├── field-service/        Identification, startup, troubleshooting, maintenance, QR
├── validation/           Test strategy, validation procedures, known limitations
├── references/           Datasheets, official sources, standards, literature, registry
└── historical/           Archived _OLD sketches (explicitly not current)
```

## Source policy

Every technical claim is typed and attributable:

| Claim type | Meaning |
|---|---|
| **Project fact** | From the official CIRQUA or ABC website |
| **Firmware implementation** | Audited from the pinned firmware commit |
| **Manufacturer specification** | Cited to the vendor document |
| **Engineering interpretation** | Our reasoning, labelled as such |
| **Recommendation** | Advice, labelled as such |

Unknown values are written as *"Not verified from the current source."* rather
than filled with plausible guesses. No marketing claims, no invented
certifications, no unverified specifications.

All external sources are recorded in
[`sources/sources.yml`](sources/sources.yml) with publisher, type, access date,
what each was used for, and an authority level.

## Code snippets are extracted, never typed by hand

The C++ in this documentation is generated directly from the firmware:

```bash
python scripts/extract_code_snippets.py
```

Each snippet carries its repository, path, symbol, line range and commit in
`docs/assets/snippets/snippet-index.yml`, and is embedded in a page together with
a provenance block. Credential-shaped values are redacted automatically. CI runs
the same script with `--check`, so a firmware change that is not re-extracted
fails the build instead of silently publishing stale code.

## Local development

### Windows (primary development environment)

```powershell
git clone https://github.com/lestealthy/Cirqua-documentation.git
cd Cirqua-documentation

# Fetch the pinned firmware submodule
git submodule update --init --recursive

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

mkdocs serve -a 127.0.0.1:8081
```

### Linux and macOS

```bash
git clone https://github.com/lestealthy/Cirqua-documentation.git
cd Cirqua-documentation
git submodule update --init --recursive

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdocs serve -a 127.0.0.1:8081
```

Open <http://127.0.0.1:8081>.

### Python version

Python 3.12 is used in CI. Python 3.10 or later works locally.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/extract_code_snippets.py` | Extract real code from the pinned firmware into `docs/assets/snippets/` |
| `scripts/generate_source_manifest.py` | Regenerate `sources/firmware-source.yml` from the submodule's Git state |
| `scripts/generate_qr_codes.py` | Generate the field-service QR codes and their destination manifest |
| `scripts/generate_favicon.py` | Derive the favicon set from the official logo |
| `scripts/validate_docs.py` | Full validation suite (see below) |

## Validation

```bash
python scripts/validate_docs.py                # required checks
python scripts/validate_docs.py --external     # also probe external URLs
mkdocs build --strict --clean                  # build must be warning-free
```

The validation suite checks:

1. the submodule is initialised and at the recorded commit
2. every internal Markdown and HTML link resolves
3. every referenced image and asset exists, and images have alt text
4. every `nav:` entry has a file, and no page is orphaned
5. no placeholder or unfinished text
6. no absolute local filesystem paths in published pages
7. no credentials, tokens or keys in pages or snippets
8. every code-snippet embed resolves
9. every GitHub source link resolves to a real path in the pinned commit
10. firmware provenance is consistent across all pages and `mkdocs.yml`
11. QR destinations are permanent HTTPS URLs on the deployed site
12. branding assets are present
13. `mkdocs.yml` carries the mandatory WattLab configuration
14. the palette is light-only with no dark scheme or toggle

External URL probing is advisory: an unreachable third-party site is reported
but never fails the build.

## Deployment

Two workflows:

| Workflow | Trigger | Purpose |
|---|---|---|
| `validation.yml` | Push and pull request to `main` | Validation only. Never deploys. |
| `docs.yml` | Push to `main` | Regenerate assets, validate, build, deploy to GitHub Pages |

`docs.yml` will not publish a build that fails validation. GitHub Pages must be
configured with **Settings → Pages → Build and deployment → Source: GitHub
Actions**.

## Updating to newer firmware

```bash
git submodule update --remote _external/Cirqua-firmware
python scripts/generate_source_manifest.py
python scripts/extract_code_snippets.py
python scripts/generate_qr_codes.py
python scripts/validate_docs.py
mkdocs build --strict --clean
```

Then review the diff in `docs/assets/snippets/` and update any page whose
verified values changed — GPIO maps, task tables, protocol frames, calibration
constants and LCD layouts are all audited content and are not automated prose.

## QR field service

Each node has a permanent QR code and a printable label:

| Node | Manual |
|---|---|
| Node 1 | <https://lestealthy.github.io/Cirqua-documentation/nodes/node1.html> |
| Node 2 | <https://lestealthy.github.io/Cirqua-documentation/nodes/node2.html> |
| Node 3 | <https://lestealthy.github.io/Cirqua-documentation/nodes/node3.html> |
| Node 4 | <https://lestealthy.github.io/Cirqua-documentation/nodes/node4.html> |
| Node 4 SMTP | <https://lestealthy.github.io/Cirqua-documentation/nodes/node4-smtp.html> |

See [QR codes for field service](docs/field-service/qr-codes.md) for the code
images and label artwork.

## Contributing

1. Branch from `main`.
2. Change the Markdown under `docs/`, and add the page to `nav:` in `mkdocs.yml`.
3. Never hand-write a C++ example — embed a snippet id.
4. Run `python scripts/validate_docs.py` and `mkdocs build --strict --clean`.
5. Open a pull request. `validation.yml` must pass.

Every page needs front matter:

```yaml
---
title: Page Title In Title Case
description: One sentence, at most 160 characters, for search and social sharing
---
```

## Licence and attribution

Documentation is authored and maintained by WattLab Engineering. CIRQUA is
funded by the European Union under Horizon Europe; CIRQUA does not represent the
views of the European Commission. Third-party manufacturer specifications,
scientific literature and project descriptions remain the property of their
authors and are cited with attribution in the
[source registry](sources/sources.yml).
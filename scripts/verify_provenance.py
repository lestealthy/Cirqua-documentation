"""Cross-check every provenance block in the docs against snippet-index.yml.

For each `cirqua-source` div we find the preceding `--8<-- "assets/snippets/<id>.cpp"`
embed and verify that:
  * the snippet id is known
  * the firmware path quoted in the block matches the index
  * the commit matches
  * a quoted line range (when present) matches the index
  * the GitHub blob URL uses the audited commit
"""
import re
import sys
from pathlib import Path

import yaml

DOCS = Path("docs")
index = yaml.safe_load((DOCS / "assets/snippets/snippet-index.yml").read_text(encoding="utf-8"))
by_id = {s["id"]: s for s in index["snippets"]}
COMMIT = "db6d9b896341a9c7d8fd01913e854b663c110d55"

EMBED = re.compile(r'--8<--\s+"assets/snippets/([a-z0-9\-]+)\.cpp"')
RANGE = re.compile(r"lines?\s+(\d+)\s*(?:[-–—]\s*(\d+))?", re.IGNORECASE)

problems = []
checked = 0

for md in sorted(DOCS.rglob("*.md")):
    rel = md.relative_to(DOCS).as_posix()
    lines = md.read_text(encoding="utf-8").splitlines()

    for i, line in enumerate(lines):
        m = EMBED.search(line)
        if not m:
            continue
        sid = m.group(1)
        if sid not in by_id:
            problems.append(f"{rel}:{i+1}: unknown snippet id '{sid}'")
            continue
        entry = by_id[sid]
        checked += 1

        # find the provenance div within the next 12 lines
        block = "\n".join(lines[i : i + 14])
        if "cirqua-source" not in block:
            problems.append(f"{rel}:{i+1}: snippet '{sid}' has no cirqua-source provenance block")
            continue

        if entry["path"] not in block:
            problems.append(f"{rel}:{i+1}: '{sid}' provenance quotes wrong path (want {entry['path']})")
        if entry["commit_short"] not in block:
            problems.append(f"{rel}:{i+1}: '{sid}' provenance missing commit {entry['commit_short']}")
        if COMMIT not in block:
            problems.append(f"{rel}:{i+1}: '{sid}' blob URL does not use the audited commit")

        rm = RANGE.search(block.split("</div>")[0])
        if rm:
            start = int(rm.group(1))
            end = int(rm.group(2)) if rm.group(2) else start
            if start != entry["start_line"] or end != entry["end_line"]:
                problems.append(
                    f"{rel}:{i+1}: '{sid}' line range {start}-{end} != index {entry['start_line']}-{entry['end_line']}"
                )

# unused snippets
used = set()
for md in sorted(DOCS.rglob("*.md")):
    used.update(EMBED.findall(md.read_text(encoding="utf-8")))
unused = sorted(set(by_id) - used)

print(f"provenance blocks checked : {checked}")
print(f"snippets available        : {len(by_id)}")
print(f"snippets referenced       : {len(used)}")
print(f"snippets never referenced : {len(unused)}")
for u in unused:
    print(f"    - {u}")

if problems:
    print(f"\nPROBLEMS ({len(problems)}):")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)

print("\nALL PROVENANCE BLOCKS MATCH THE SNIPPET INDEX")
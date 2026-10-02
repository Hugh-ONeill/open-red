#!/usr/bin/env python3
"""One stale line in plans/outline.upkeep costs that line, not the list.

Run 19's wording rung answered "every party member is at least level 35
(you added this when outlining, for: Defeat Sabrina ...)" with the note
rewritten and the objective untouched, and the note went into the outline
and outline.upkeep. At run 20's launch that one line no longer matched the
banked wording, the fresh block archived the WHOLE upkeep list without a
word, and every party leg of run 20 was fatal: the Flash leg could not be
left behind (2026-10-01; the user scrapped the run).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


td = Path(tempfile.mkdtemp())
(td / "authored").write_text("Reach Pewter City\nevery party member is at least level 35\n"
                             "a party Pokemon knows FLASH\n")
side = td / "upkeep"
side.write_text("every party member is at least level 35 (you added this when outlining, "
                "for: Defeat Erika for the Rainbow Badge)\na party Pokemon knows FLASH\n"
                "a party Pokemon knows SOMETHING NEVER BANKED\n")
arch = td / "archive" / "x-upkeep"
r = subprocess.run([sys.executable, str(ROOT / "planner/sidecar_keep.py"), str(side),
                    str(td / "authored"), str(arch)], capture_output=True, text=True)
lines = side.read_text().splitlines()
ck("the note is stripped and the line kept",
   "every party member is at least level 35" in lines, lines)
ck("a banked line stays", "a party Pokemon knows FLASH" in lines, lines)
ck("only the unbanked line goes", "a party Pokemon knows SOMETHING NEVER BANKED" not in lines
   and len(lines) == 2, lines)
ck("...and it is said out loud, by name", "SOMETHING NEVER BANKED" in r.stdout
   and "note stripped" in r.stdout, r.stdout)
ck("the original is archived, not lost", arch.exists()
   and "Defeat Erika" in arch.read_text())

st = td / "stages"
st.write_text("early\tReach Pewter City\nlate\ta party Pokemon knows FLASH\n")
r2 = subprocess.run([sys.executable, str(ROOT / "planner/sidecar_keep.py"), str(st),
                     str(td / "authored"), str(td / "archive" / "y")], capture_output=True, text=True)
ck("a sidecar that is all banked is kept as is",
   "every leg it names is the banked wording" in r2.stdout
   and not (td / "archive" / "y").exists(), r2.stdout)

src = (ROOT / "planner/author.py").read_text()
i = src.index("def check_wording(")
blk = src[i:src.index("\nLATER_SYS", i)]
ck("the wording rung strips the note from its answer",
   'new = _DOUBT_NOTE.sub("", new).strip()' in blk)
rw = (ROOT / "planner/reword_leg.py").read_text()
ck("reword_leg strips it too", "when outlining,).*$" in rw)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

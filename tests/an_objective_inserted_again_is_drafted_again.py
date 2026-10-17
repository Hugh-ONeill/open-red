#!/usr/bin/env python3
"""An objective the missing rung puts back into the outline is drafted again.

Run 57 (2026-10-16): "Exit Victory Road" closed as leg 56 by walking out
the door it came in by. The missing rung put the same objective in front of
leg 57, the chain found that leg's plan by its objective, kept it, walked out
the same door and closed it again. When the inserted text is already in the
outline, its old plans are archived so a fresh plan is written.

Runs the real missing_rung body from fresh_discovery.sh against stubs.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


sh = (ROOT / "fresh_discovery.sh").read_text()
body = sh[sh.index("  missing_rung() {"):]
body = body[:body.index("\n  }\n") + 4]


def run(outline, missing):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir(); (d / "planner").mkdir()
        (d / "plans/outline.txt").write_text("".join(l + "\n" for l in outline))
        (d / "run/outline_inserts").write_text("")
        (d / "plans/leg_56_exit_victory_road.json").write_text("{}")
        stub = d / "planner"
        (stub / "author.py").write_text(f"print({missing!r})\n")
        (stub / "state_text.py").write_text("print('here')\n")
        (stub / "insert_guard.py").write_text("")
        (stub / "insert_leg.py").write_text(
            "import sys\nfrom pathlib import Path\n"
            "i, t = int(sys.argv[1]), sys.argv[2]\n"
            "p = Path('plans/outline.txt'); L = p.read_text().splitlines()\n"
            "L.insert(i - 1, t); p.write_text('\\n'.join(L) + '\\n')\n")
        script = ("set -e\nleg='Defeat the rival after the Elite Four'; goal=\"$leg\"; i=3\n"
                  "AUTHOR_MODEL=m\ndisposed() { :; }\npushes_in_force() { echo 0; }\n"
                  "archive_plans_of() { echo \"ARCHIVED:$1\"; }\n"
                  + body + "\nmissing_rung; echo rc=$?\n")
        r = subprocess.run(["bash", "-c", script], cwd=d, capture_output=True, text=True)
        return r.stdout + r.stderr


VR = "Exit Victory Road"
out = run(["Defeat the Elite Four", VR, "Defeat the rival after the Elite Four"], VR)
ck("an insert repeating an objective behind it archives that objective's plans",
   f"ARCHIVED:{VR}" in out and "rc=0" in out, out)
out = run(["Defeat the Elite Four", "Defeat the rival after the Elite Four"], VR)
ck("a new objective archives nothing", "ARCHIVED" not in out and "rc=0" in out, out)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:500]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

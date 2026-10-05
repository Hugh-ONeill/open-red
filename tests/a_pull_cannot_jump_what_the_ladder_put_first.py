#!/usr/bin/env python3
"""A pulled leg cannot jump a leg the ladder inserted before it because it
is needed first.

Run 36, 2026-10-05: the missing rung inserted "Clear Victory Road" before
"Defeat the Elite Four"; eleven minutes later the momentum rung, the run
having wandered onto ROUTE_21, pulled the Elite Four to the front and slid
Victory Road behind it. push_leg already refused the mirror image.

Pinned: the pull is refused, exit 4, when a leg it would jump is in the
inserts ledger as needed before it, or needed before such a leg; a PULL
row counts; a pull that jumps only unrelated legs, or lands after the
insert, goes through; a rewording row is not a prerequisite. Synthetic."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


OUT = ["Clear Victory Road", "Reach Celadon City", "Defeat the Elite Four",
       "Obtain HM04 from the Warden", "Become the Champion"]


def pull(to, frm, inserts):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        for f in ("outline.authored", "outline.txt"):
            (d / "plans" / f).write_text("\n".join(OUT) + "\n")
        (d / "plans/outline.upkeep").write_text("")
        (d / "run/outline_leg").write_text("1")
        (d / "run/outline_inserts").write_text("\n".join(inserts) + "\n")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "planner"))
        r = subprocess.run([sys.executable, str(ROOT / "planner/pull_leg.py"),
                            "pull", str(to), str(frm)], cwd=d, env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr, \
            (d / "plans/outline.txt").read_text().splitlines()


rc, out, lines = pull(1, 3, ["LEG=Defeat the Elite Four|Clear Victory Road"])
ck("the Elite Four is not pulled ahead of the Victory Road put before it",
   rc == 4 and lines == OUT, (rc, out))
ck("...and says why", "'Clear Victory Road' was put before" in out, out)
rc, out, lines = pull(1, 5, ["LEG=Become the Champion|Defeat the Elite Four",
                             "LEG=Defeat the Elite Four|Clear Victory Road"])
ck("what the insert needs is needed too", rc == 4 and lines == OUT, (rc, out))
rc, out, lines = pull(1, 3, ["LEG=Defeat the Elite Four|PULL Clear Victory Road"])
ck("a leg pulled ahead of it by the missing rung counts", rc == 4, (rc, out))
rc, out, lines = pull(2, 3, ["LEG=Defeat the Elite Four|Clear Victory Road"])
ck("landing after the insert goes through",
   rc == 0 and lines[1] == "Defeat the Elite Four", (rc, out))
rc, out, lines = pull(1, 2, ["LEG=Defeat the Elite Four|Clear Victory Road"])
ck("a leg with no insert before it is pulled as before",
   rc == 0 and lines[0] == "Reach Celadon City", (rc, out))
rc, out, lines = pull(1, 3, ["LEG=Defeat the Elite Four|Defeat the Elite Four"])
ck("a row naming the leg itself is no prerequisite", rc == 0, (rc, out))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

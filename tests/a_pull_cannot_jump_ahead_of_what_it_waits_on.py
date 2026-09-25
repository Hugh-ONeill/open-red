#!/usr/bin/env python3
"""A pulled leg cannot jump ahead of the leg it was placed after, when that
leg is what gives it.

Run of record 4, 2026-09-25: stuck on "Retrieve the S.S. Ticket", the
blocker rung pulled "a party Pokemon knows CUT" five legs forward, ahead of
"Retrieve the HM01 from the S.S. Anne", which the party pass had placed it
after and which needs the ticket. The run had to teach CUT before it could
reach the HM, decided Bill gives it, and went back to him again and again
(user: "fix the pull so it can't jump ahead of its prerequisite").

Pinned: a party leg's anchor is the nearest story leg above it in the
banked outline, and counts only when the two share a name (HM01 is CUT);
the pull is refused, exit 4, while that anchor is still ahead and would
land after it; once the anchor is done, or for a leg with no such anchor,
or a story leg, the pull goes through; the refusal says why. Synthetic."""
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


STORY = ["Reach Cerulean City", "Retrieve the S.S. Ticket", "Reach Vermilion City",
         "Retrieve the HM01 from the S.S. Anne", "Defeat Lt. Surge for the Thunder Badge"]
UP = ["a party Pokemon knows CUT", "the party holds a FLYING type"]
BANKED = STORY[:4] + UP + STORY[4:]


def pull(to, frm, done=1, outline=None):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        (d / "plans/outline.authored").write_text("\n".join(BANKED) + "\n")
        (d / "plans/outline.upkeep").write_text("\n".join(UP) + "\n")
        (d / "plans/outline.txt").write_text("\n".join(outline or BANKED) + "\n")
        (d / "run/outline_leg").write_text(str(done))
        env = dict(os.environ, PYTHONPATH=str(ROOT / "planner"))
        r = subprocess.run([sys.executable, str(ROOT / "planner/pull_leg.py"),
                            "pull", str(to), str(frm)], cwd=d, env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr, \
            (d / "plans/outline.txt").read_text().splitlines()


rc, out, lines = pull(2, 5)          # CUT to 2, ahead of the HM01 leg at 4
ck("CUT is not pulled ahead of the HM01 leg it was placed after",
   rc == 4 and lines == BANKED, (rc, out))
ck("...and says why",
   "was placed after 'Retrieve the HM01 from the S.S. Anne'" in out, out)
rc, out, lines = pull(5, 6, done=4)  # HM01 done: CUT may move up
ck("once that leg is done the pull goes through", rc == 0, (rc, out))
rc, out, lines = pull(2, 6)          # FLYING shares no name with HM01
ck("a leg placed after it without sharing a name is pulled as before",
   rc == 0 and lines[1] == "the party holds a FLYING type", (rc, out))
rc, out, lines = pull(2, 7)          # a story leg
ck("a story leg is pulled as before", rc == 0, (rc, out))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A push never carries a leg past the banked outline's last leg.

Run 36, 2026-10-05: "Clear Victory Road" failed to author and was pushed
past "Defeat the rival in the final showdown", taking "Defeat the Elite
Four" with it; the chain went on to author the final fight in front of the
cave that leads to it.

Pinned: a push that would cross the last authored leg stops short of it,
riders and all; with no room left it is refused (exit 5) and the outline is
untouched; a push that does not reach it is as before; with no banked
outline nothing changes. Synthetic."""
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


END = "Defeat the rival in the final showdown"


def push(outline, frm, after, inserts=(), authored=True):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        (d / "plans/outline.txt").write_text("\n".join(outline) + "\n")
        if authored:
            (d / "plans/outline.authored").write_text(
                "Reach the Indigo Plateau\nDefeat the Elite Four\n" + END + "\n")
        (d / "run/outline_inserts").write_text("\n".join(inserts) + "\n")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "planner"))
        r = subprocess.run([sys.executable, str(ROOT / "planner/push_leg.py"),
                            str(frm), str(after)], cwd=d, env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr, \
            (d / "plans/outline.txt").read_text().splitlines()


O = ["Obtain HM04", "Clear Victory Road", "Defeat the Elite Four", END]
INS = ["LEG=Defeat the Elite Four|Clear Victory Road"]
rc, out, lines = push(O, 2, 4, INS)
ck("the cave and what waits on it are not carried past the final fight",
   rc == 5 and lines == O, (rc, out, lines))
ck("...and it says why", "nothing comes after the end of the game" in out, out)
rc, out, lines = push(O, 1, 4, INS)
ck("a push that would cross it stops short of it",
   rc == 0 and lines[-1] == END and lines.index("Obtain HM04") == 2, (rc, out, lines))
O2 = ["Obtain HM04", "Reach Celadon City", "Defeat Erika", END]
rc, out, lines = push(O2, 1, 3)
ck("a push that stops short anyway is as before",
   rc == 0 and lines == ["Reach Celadon City", "Defeat Erika", "Obtain HM04", END],
   (rc, out, lines))
rc, out, lines = push(O, 2, 4, INS, authored=False)
ck("with no banked outline nothing changes",
   rc == 0 and lines[-1] == "Defeat the Elite Four", (rc, out, lines))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

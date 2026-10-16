#!/usr/bin/env python3
"""The last leg that cannot be written goes to the ladder, and a chain that
runs past its last leg without a Hall of Fame does not call itself complete.

Run 57 (2026-10-16): leg 58 of 58 failed authoring once, "push_leg: 58 is
not after 58" refused, the step-over set the progress past the end, and
the chain printed "OUTLINE CHAIN COMPLETE: all 58 legs" and exited on
Victory Road with eight badges.

Source test.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(name, ok): checks.append((name, bool(ok)))
sh = (ROOT / "fresh_discovery.sh").read_text()
ck("the script parses", subprocess.run(["bash", "-n", str(ROOT / "fresh_discovery.sh")]).returncode == 0)
i = sh.index('if [ "$_arc" != 0 ]; then')
blk = sh[i:sh.index("could not push leg", i)]
cond = blk[blk.index('if [ "${_prior:-0}" -ge 1 ]'):]
cond = cond[:cond.index("\n")]
ck("the last leg's first authoring failure takes the no-plan branch",
   '[ "$i" -ge "${#LEGS[@]}" ]' in cond)
ck("...which sets the no-plan flag before any push is tried",
   blk.index("_no_plan=1") < blk.index("push_leg.py"))
end = sh[sh.index('if [ "$i" -gt "${#LEGS[@]}" ]; then'):]
end = end[:end.index("exit 0")]
ck("past the end asks whether the game is finished", "planner/finished.py" in end)
ck("...and says the Hall of Fame was not reached when it was not",
   "the Hall of Fame not reached" in end)
bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok  " if ok else "FAIL"), n)
sys.exit(1 if bad else 0)

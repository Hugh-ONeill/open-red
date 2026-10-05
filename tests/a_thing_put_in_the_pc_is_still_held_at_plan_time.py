#!/usr/bin/env python3
"""A thing the run put in the PC is in the start state every plan is
written from.

Run 36 stored the GOLD TEETH at Viridian's PC to make room for HM04
(2026-10-05). The rounds read the PC from the observation; the re-author's
start line came from last_state.json, which never carried it, and the next
HM04 drafts went looking for the teeth in the Safari Zone's Secret House.

Pinned: last_state.json carries pc_items; the start line names the key
items and machines in the PC, counts the rest, says where to take them
out, and says nothing when the PC is empty. Synthetic."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def line(state):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "run").mkdir()
        (Path(d) / "run/last_state.json").write_text(json.dumps(state))
        return subprocess.run([sys.executable, str(ROOT / "planner/state_text.py")],
                              cwd=d, capture_output=True, text=True).stdout


base = {"map": "VIRIDIAN_POKECENTER", "region": "3,7",
        "party": [{"species": "LAPRAS", "level": 50, "hp": 1, "max_hp": 1}],
        "badges": [], "bag": {"POTION": 2}, "money": 10}
w = line(dict(base, pc_items={"GOLD_TEETH": 1, "HM_CUT": 1, "TM_BIDE": 1,
                              "POTION": 3, "CARBOS": 2}))
ck("a key item in the PC is named", "GOLD_TEETH x1" in w, w)
ck("so is a machine, by its number too", "HM_CUT (HM01) x1" in w
   and "TM_BIDE x1" in w, w)
ck("the rest is counted, not listed",
   "and 2 other kind(s) of item" in w and "CARBOS" not in w, w)
ck("and it says where they come out", "WITHDRAW ITEM at any Pokemon Center" in w, w)
ck("it follows the bag", w.index("POTION x2") < w.index("in the PC"), w)
ck("an empty PC says nothing", "in the PC" not in line(dict(base, pc_items={})))
ck("an old snapshot with no PC says nothing", "in the PC" not in line(base))

src = (ROOT / "planner/executor.py").read_text()
ck("last_state.json carries the PC",
   '"pc_items": o.get("pc_items") or {},' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

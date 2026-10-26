#!/usr/bin/env python3
"""A middle step ending on a flag that already fired is refused.

Run 67, 2026-10-26, leg 29 "Reach Fuchsia City" v2: save_mr_fuji ended on
EVENT_GOT_POKEDEX (Oak's gift, the first hour) between the Tower climb and
the flute; the rescue read as done at entry and the plan went to an empty
house.

Pinned: such a middle step is refused; one on a flag not yet fired stands;
the last step's own rule is unchanged.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

d = Path(tempfile.mkdtemp(prefix="midflag_"))
(d / "run").mkdir()
(d / "run/obs.json").write_text(json.dumps({"flags": ["EVENT_GOT_POKEDEX"]}))
(d / "run/executor_log.jsonl").write_text(json.dumps(
    {"kind": "flag_fired", "flag": "EVENT_GOT_POKEDEX", "t": 1}) + "\n")
here = os.getcwd()
os.chdir(d)
try:
    def plan(mid):
        return {"goal": "Reach Fuchsia City", "subgoals": [
            {"id": "tower", "done_when": {"map": "POKEMON_TOWER_1F"}},
            {"id": "save_mr_fuji", "done_when": {"flag": mid}},
            {"id": "flute", "done_when": {"has_item": {"POKE_FLUTE": 1}}}]}
    p = " ".join(A.validate(plan("EVENT_GOT_POKEDEX")) or [])
    ck("a middle step on a fired flag is refused",
       "subgoal[1] (save_mr_fuji)" in p and "ALREADY FIRED" in p, p[:400])
    p = " ".join(A.validate(plan("EVENT_RESCUED_MR_FUJI")) or [])
    ck("one on a flag not yet fired is not refused for it",
       "subgoal[1] (save_mr_fuji) ends on flag" not in p, p[:400])
finally:
    os.chdir(here)

import executor as E  # noqa: E402
ex = E.Executor.__new__(E.Executor)
ex.plan = {"subgoals": [{"id": "tower", "done_when": {"map": "POKEMON_TOWER_1F"}},
                        {"id": "save_mr_fuji", "done_when": {"flag": "EVENT_GOT_POKEDEX"}},
                        {"id": "flute", "done_when": {"has_item": {"POKE_FLUTE": 1}}}]}
ex._flags_at_plan = {"EVENT_GOT_POKEDEX"}
O = {"mode": "overworld", "map": {"id": "ROUTE_16"}, "flags": ["EVENT_GOT_POKEDEX"], "bag": {}}
ck("a waypoint is not passed by a later flag set before the plan began",
   ex._waypoint_passed(ex.plan["subgoals"][0], O) is None)
ex._flags_at_plan = set()
ck("...but one set during the plan still passes it",
   ex._waypoint_passed(ex.plan["subgoals"][0], O) == "save_mr_fuji")

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

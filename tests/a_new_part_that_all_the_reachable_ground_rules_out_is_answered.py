#!/usr/bin/env python3
"""A "part of MAP you have not stood in" step is answered once everything a
walk reaches has been on screen and none of it is a part not stood in.

Run 29, 2026-10-02: the Mt Moon leg's rewrite asked for a third part of
ROUTE_3. The north strips it had not seen were on foot from the two parts it
had, so seeing them could never finish the step; after one sweep showed all
of Route 3 the run kept looking for fourteen rounds (user: "maybe something
like the done condition also getting fulfilled by proving that its
impossible by seeing all the reachable ground").

Pinned: answered on the map, in a ruled-out part, with no seen ground ending
at unseen ground and every unreached seen cell a person's own tile; not
answered while any of that is untrue; the words keep the limit (another
map's way in is not ruled out); the rewrite's journal says ANSWERED.
Synthetic: no game.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = object.__new__(E.Executor)
ex._where = lambda o: f"{o['map']['id']}|{o['map']['region']}"
SG = {"id": "explore_route_3_north",
      "done_when": {"map": "ROUTE_3", "not_area": ["ROUTE_3|18,8", "ROUTE_3|57,0"]}}

def obs(**kw):
    m = {"id": "ROUTE_3", "region": "57,0", "seen": {"frontier_n": 0},
         "frontier": [], "seen_unreached": {"n": 9, "beside_n": 9}}
    m.update(kw)
    return {"mode": "overworld", "map": m, "player": {"x": 61, "y": 0}}

why = ex._new_part_ruled_out(SG, obs())
ck("answered when all reachable ground is seen and only trainers' tiles are unreached",
   bool(why), why)
ck("...and the words keep the limit", why and "another map is not ruled out" in why, why)
ck("not while seen ground still ends at unseen ground",
   ex._new_part_ruled_out(SG, obs(frontier=[{"x": 37, "y": 4, "d": 20}])) is None)
ck("not while seen floor (not a person's tile) is unreached",
   ex._new_part_ruled_out(SG, obs(seen_unreached={"n": 12, "beside_n": 9})) is None)
ck("not on another map",
   ex._new_part_ruled_out(SG, obs(id="ROUTE_4", region="4,4")) is None)
ck("not in a part the step does not rule out",
   ex._new_part_ruled_out(SG, obs(region="40,5")) is None)
ck("not for a step that asks anything else",
   ex._new_part_ruled_out({"id": "x", "done_when": {"map": "ROUTE_3"}}, obs()) is None)

src = (ROOT / "planner/executor.py").read_text()
ck("checked at step entry, before a replay, and each escalation round",
   src.count("self._new_part_ruled_out(sg,") == 3)
au = (ROOT / "planner/author.py").read_text()
ck("the rewrite's journal says ANSWERED with the proof",
   'k == "subgoal_ruled_out"' in au and "ANSWERED" in au)
lua = (ROOT / "harness/shim.lua").read_text()
ck("the shim counts the unreached cells that are someone's own tile",
   "beside_n = beside_n" in lua)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A level step whose travel step was carried past is told its condition
names no place.

Run 65, 2026-10-25, leg 27 "every party member is at least level 35": the
plan went go_to_route_17 -> grind_fearow "Battle wild Pokemon on Route 17
until Fearow reaches level 35" -> grind_pikachu ... Route 17 lies behind
Route 16's Snorlax, so the travel step was carried, and the page said "the
steps after it, this one included, were written for someone standing in
ROUTE_17". The run spent three attempts re-cutting Route 16's bush for a road
south, with Route 16's own grass, and a list of fought-on ground, already on
the page (user: "maybe we should open up the idea of 'if i cant reach
location X for training, perhaps location Y will do'").

Pinned: a level-only step under a carried travel step is told where to train
was the plan-writer's choice and any wild ground counts; a catching step or a
place step is not told so.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

SAY = "names no place: where its words say to train was the plan-writer's choice"

def note(step_dw):
    plan = {"subgoals": [{"id": "go_to_route_17", "done_when": {"map": "ROUTE_17"}},
                         {"id": "train", "done_when": step_dw}]}
    fake = types.SimpleNamespace(plan=plan, _carried_ids=["go_to_route_17"],
                                 _where=lambda o: "ROUTE_16|27,10")
    return E.Executor._carried_premise_note(fake, plan["subgoals"][1],
                                            {"map": {"id": "ROUTE_16"}})

for dw in ({"slot_level": {"slot": 1, "min": 35}}, {"party_min_level": 35},
           {"lead_level": 30}):
    t = note(dw)
    ck(f"{list(dw)[0]}: the carried place is still said", "written for someone standing in ROUTE_17" in t, t)
    ck(f"{list(dw)[0]}: ...and that a level names no place", SAY in t
       and "a wild fought on any ground counts toward it" in t, t)
for dw in ({"party_type": "FLYING"}, {"map": "FUCHSIA_CITY"},
           {"party_min_level": 35, "map": "ROUTE_17"}):
    t = note(dw)
    ck(f"{sorted(dw)}: not told that where it stands does not matter", SAY not in t, t)
ck("...and nothing names another place to go",
   all(m not in note({"party_min_level": 35}) for m in ("ROUTE_16 ", "ROUTE_7", "CELADON")))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

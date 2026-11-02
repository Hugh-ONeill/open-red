#!/usr/bin/env python3
"""A waypoint is not passed by a later step that holds only by an absence.

Run 70, 2026-11-02, leg 40 "Retrieve the HM04 from the Safari Zone":
retrieve_gold_teeth failed in Celadon and the plan went on to
go_to_fuchsia_city and enter_safari_zone, both skipped at entry ("later
give_teeth_to_warden already holds") because that step's done_when was
{lacks_item: [GOLD_TEETH]}, true since the teeth were never held. An
absence that held before anything was done proves no passing.

Pinned: the two waypoints are not passed by the absence; a later map step
that holds still passes them. Synthetic, from the leg's plan file.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

subs = [{"id": "go_to_celadon_game_corner", "done_when": {"map": "GAME_CORNER"}},
        {"id": "retrieve_gold_teeth", "done_when": {"has_item": {"GOLD_TEETH": 1}}},
        {"id": "go_to_fuchsia_city", "done_when": {"map": "FUCHSIA_CITY"}},
        {"id": "enter_safari_zone", "done_when": {"map": "SAFARI_ZONE_CENTER"}},
        {"id": "give_teeth_to_warden", "done_when": {"lacks_item": ["GOLD_TEETH"]}},
        {"id": "receive_hm04", "done_when": {"has_item": {"HM_STRENGTH": 1}}}]
ex = E.Executor.__new__(E.Executor)
ex.plan = {"subgoals": subs}
ex._flags_at_plan = set()
O = {"mode": "overworld", "map": {"id": "CELADON_MART_3F"}, "flags": [],
     "bag": {"HM_CUT": 1, "POKE_FLUTE": 1}}
for i in (2, 3):
    got = ex._waypoint_passed(subs[i], O)
    ck(f"{subs[i]['id']} is not passed by the teeth never held", got is None, got)
O2 = dict(O, map={"id": "SAFARI_ZONE_CENTER"})
got = ex._waypoint_passed(subs[2], O2)
ck("...a later map step that holds still passes it", got == "enter_safari_zone", got)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

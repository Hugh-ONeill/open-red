#!/usr/bin/env python3
"""A cross struck out while the edge was out of reach is tried again once
the party stands on that edge.

Run 34, 2026-10-03: Viridian's north seam was struck three times while the
sleepy old man lay across the road ("cannot be reached over the ground you
have SEEN"). He woke, the run walked onto the seam at (18,0), and the gate
kept refusing the cross; the round did nothing, and the sweep walked the
party across town to press the gym's sign (user: "just tried to cross north
but was instead directed to the sign ... the gym sign").

Pinned: on the edge row with a road printed, the strike lifts; off it, it
stays (connections_reach alone is "not ruled out", true while unseen ground
is left); another side does not lift; a reason that is not a blocked walk
does not lift. Also: battle_menu_to survives a battle with no action menu.
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
WHY = ("the north seam of VIRIDIAN_CITY (to ROUTE_2) cannot be reached over "
       "the ground you have SEEN")
ex._dead_why = {"s": WHY}
def obs(x, y):
    return {"player": {"x": x, "y": y},
            "map": {"id": "VIRIDIAN_CITY", "width": 40, "height": 36,
                    "connections": {"north": "ROUTE_2", "south": "ROUTE_1"},
                    "connections_reach": {"north": True, "south": True}}}
ck("standing on the north row: the struck cross north is tried again",
   ex._strike_reason_lifted("s", "cross", {"dir": "north"}, obs(18, 0)))
ck("one row short of it: still refused (reach alone is not enough)",
   not ex._strike_reason_lifted("s", "cross", {"dir": "north"}, obs(18, 1)))
ck("on the north row, a cross south does not lift",
   not ex._strike_reason_lifted("s", "cross", {"dir": "south"}, obs(18, 0)))
ex._dead_why = {"s": "the game said: nothing happened"}
ck("a reason that is not a blocked walk never lifts",
   not ex._strike_reason_lifted("s", "cross", {"dir": "north"}, obs(18, 0)))
lua = (ROOT / "harness/shim.lua").read_text()
ck("battle_menu_to answers a battle with no action menu instead of crashing",
   "if battle.menuIndex == nil then return false end" in lua)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A door a bush you can walk to opens onto is not "across water".

Run 70, Vermilion (2026-11-01): the gym door (12,19) has the harbor's water
within a ride of its doorstep, so the shim flags it over_water; its yard is
also past the CUT tree at (15,18), which the same observation lists as
reachable with 12,19 behind it. The page said "DOORWAYS ACROSS WATER: 12,19
... nobody in the party knows SURF" beside the bush's own line. Probed on a
copy of the run's save with the shim: gym door over_water True, bush
reachable True, past.doors ['12,19'].

Pinned: such a door is kept out of the across-water set, a stored entry for
it is dropped, and a door with no bush in front stays. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def run(stored, bush_reachable=True):
    ex = E.Executor.__new__(E.Executor)
    ex._door_over_water = {"VERMILION_CITY": list(stored)}
    ex._knows_surf = False
    ex.shut_doors = {}
    ex._save_memory = lambda *a, **k: None
    ex.log = lambda *a, **k: None
    obs = {"mode": "overworld", "player": {"x": 39, "y": 15},
           "party": [{"species": "PIKACHU", "moves": [{"id": "THUNDERSHOCK"}]}],
           "map": {"id": "VERMILION_CITY", "region": "18,0",
                   "warps": [{"x": 12, "y": 19, "dest": "VERMILION_GYM",
                              "over_water": True, "reachable": False},
                             {"x": 19, "y": 31, "dest": "VERMILION_DOCK",
                              "over_water": True, "reachable": False}],
                   "objects": [{"x": 15, "y": 18, "kind": "cut_tree",
                                "reachable": bush_reachable, "opens": True,
                                "past": {"doors": ["12,19"], "unseen": True}}],
                   "seen": {"n": 1000, "frontier_n": 0}, "frontier": []}}
    for _ in range(120):
        try:
            ex.note_frontier(obs)
            break
        except AttributeError as e:
            name = str(e).split("'")[-2]
            setattr(ex, name, {})
        except TypeError:
            break
    return ex._over_water_doors("VERMILION_CITY")


got = run([])
ck("a door behind a reachable bush is not across water", "12,19" not in got, got)
ck("...and a door with no bush in front still is", "19,31" in got, got)
got = run(["12,19", "19,31"])
ck("a stored entry for the bush's door is dropped", got == {"19,31"}, got)
got = run([], bush_reachable=False)
ck("a bush no walk reaches does not lift it", "12,19" in got, got)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

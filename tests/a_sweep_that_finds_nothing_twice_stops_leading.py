#!/usr/bin/env python3
"""Two sweeps of the same place that show nothing, and explore stops
opening with a third.

The sweep aims at the nearest ground never on screen. If the way there
crosses a script — Viridian's "You can't go through here! This is private
property!" — the walk is interrupted one step in, so the cell is never
seen, so it is still the nearest unseen ground and still the aim. Run 32
swept five times in a row for one step and no new cells each time (user,
2026-09-22: "sweeps are repeating the same direction, after a sweep fails
it should sweep in a different direction or something"). Eighteen sweeps in
that city, six of them dry, six turned back by that one man.

The dry-walk ledger already counted them, but it only demotes a region as a
REMOTE destination; nothing stopped the LOCAL sweep being taken again the
next round. Now two dry sweeps here and explore goes to its other steps,
the doors on this floor and then ground elsewhere.

Pinned: the count is CONSECUTIVE and resets the moment a sweep here shows
something, so a floor with more to see is never starved; it is kept per
region, not per map; a model that asks for a sweep itself still gets one;
the tally survives a relaunch; and a failure to count never costs the
round. Synthetic."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("two is the number, and it is named once",
   E.Executor.SWEEPS_DRY_BEFORE_OTHER == 2
   and "SWEEPS_DRY_BEFORE_OTHER = 2" in SRC)
ck("the gate reads the count for the region underfoot",
   '_dry_here = int((getattr(self, "_sweep_dry", None) or {}).get(' in SRC
   and "and (_dry_here < self.SWEEPS_DRY_BEFORE_OTHER" in SRC)
ck("...and a sweep the MODEL asked for is never refused",
   'or _params.get("until") is not None)' in SRC)
ck("the count is kept where the sweep's own result is in hand",
   'self.log("sweep_dry", region=_k' in SRC
   and SRC.index("self._count_dry_walk(self._where(obs), tr)")
   < SRC.index('self.log("sweep_dry"'))
ck("a failure to count never costs the round",
   "pass            # a tally is never worth the round" in SRC)
ck("it survives a relaunch with the rest of the memory",
   '"sweep_dry": dict(getattr(self, "_sweep_dry", None) or {}),' in SRC
   and 'self._sweep_dry = dict(data.get("sweep_dry") or {})' in SRC)
ck("the reason is written where the gate is",
   "A SWEEP THAT KEEPS BEING TURNED BACK STOPS BEING THE FIRST MOVE" in SRC
   and "private property" in SRC)


# ---- the tally, worked the way the source works it ---------------------
def sweep(tally, region, trace):
    t = dict(tally)
    m = re.search(r"(\d+) cell\(s\) newly on screen", " ".join(trace))
    if m and int(m.group(1)) == 0:
        t[region] = int(t.get(region, 0) or 0) + 1
    else:
        t.pop(region, None)
    return t


def leads(tally, region, asked=False):
    return (int(tally.get(region, 0) or 0) < E.Executor.SWEEPS_DRY_BEFORE_OTHER
            or asked)


DRY = ["sweep(until=warp): the world did not change, but it SPOKE — swept "
       "1 step(s), 0 cell(s) newly on screen — it said: \"You can't go "
       "through here! This is private property!\""]
WET = ["sweep(until=warp): ok (moved, swept 25 step(s), 168 cell(s) newly "
       "on screen; came into view: a doorway at (18,5))"]
V = "VIRIDIAN_CITY|17,0"

t = {}
ck("a sweep still leads with nothing counted", leads(t, V))
t = sweep(t, V, DRY)
ck("one dry sweep is bad luck; it still leads", leads(t, V) and t[V] == 1)
t = sweep(t, V, DRY)
ck("two and it stops leading", not leads(t, V) and t[V] == 2)
ck("...but a sweep the model asked for still runs", leads(t, V, asked=True))
ck("...and run 32's five in a row become two",
   not leads(sweep(sweep(t, V, DRY), V, DRY), V))

t2 = sweep(t, V, WET)
ck("one productive sweep clears it entirely", V not in t2 and leads(t2, V))
ck("...and the next dry one starts again from one",
   sweep(t2, V, DRY)[V] == 1)

t3 = sweep({}, V, DRY)
t3 = sweep(t3, "PEWTER_CITY|4,2", DRY)
ck("the count is per region, not per map or run",
   t3[V] == 1 and t3["PEWTER_CITY|4,2"] == 1 and leads(t3, V))
ck("...so a different part of the same map is judged on its own",
   leads(sweep(sweep({}, V, DRY), V, DRY), "VIRIDIAN_CITY|3,9"))

ck("a sweep that moved but saw nothing new still counts as dry",
   sweep({}, V, ["sweep(until=warp): ok (moved, swept 8 step(s), 0 cell(s) "
                 "newly on screen; nothing new came into view)"])[V] == 1)
ck("a trace with no count at all is not counted either way",
   sweep({}, V, ["sweep(until=warp): FAILED — no path"]) == {})

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

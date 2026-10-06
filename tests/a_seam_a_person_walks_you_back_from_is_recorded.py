#!/usr/bin/env python3
"""A seam somebody walks the party back from is recorded as refused, and
stays refused until an event fires, not until the bag changes.

Run 37, 2026-10-05: Pewter's youngster meets the party at the east exit,
says "You're a trainer right? BROCK's looking for new challengers! Follow
me!" and walks it back toward the gym. The cross reported "the walk ended
short" and nothing was recorded, so the run crossed east, interacted with
him and walked round him for twenty rounds (user: "i dont think its
registering the scripted blocker from pewter to rt3 before brock is
faced"). Proven on a copy of the live save: the shim now adds "and while
it spoke you were walked back: from within 4 cell(s) of the gap to 34
away, at (9,13)".

Pinned: that phrase writes a seam proof; it is an events-only mark, never
geometry; it holds while badges and flags hold, through a bag change, and
lifts when they change; the plain "ended short" without it records nothing;
the shim tracks the closest approach and the walk-back during a cross.
Synthetic, with source pins over shim.lua."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def fresh():
    ex = E.Executor.__new__(E.Executor)
    ex.explored, ex.visits, ex.frontier = {}, {}, {"PEWTER_CITY|4,2": ["east", "south"]}
    ex._no_cross, ex._no_cross_at = {}, {}
    ex._save_memory = lambda: None
    ex.log = lambda *a, **k: None
    return ex


obs = {"map": {"id": "PEWTER_CITY", "region": "4,2"}, "badges": [],
       "flags": ["EVENT_GOT_POKEDEX"], "bag": {"POTION": 2}}
DET = ("couldn't reach east edge gap (39,17), stuck at (36,17) — 3 cell(s) of walking "
       "still to do — during this walk someone spoke and the walk ended short: "
       "\"You're a trainer right? BROCK's looking for new challengers! Follow me!\" — "
       "and while it spoke you were walked back: from within 4 cell(s) of the gap "
       "to 34 away, at (9,13)")
ex = fresh()
ex._seam_proof(obs, {"op": "cross", "dir": "east"}, DET)
m = (ex._no_cross_at.get("PEWTER_CITY|4,2") or {}).get("east")
ck("a walk-back writes a seam proof", "east" in ex._no_cross.get("PEWTER_CITY|4,2", set()))
ck("...an events-only mark, never geometry", isinstance(m, dict) and "events" in m, m)
ck("...and the way stops being sold as untried",
   "east" not in ex.frontier["PEWTER_CITY|4,2"], ex.frontier)
ex._mark_now = E.Executor._world_mark(obs)
ck("it holds as things stand", ex._sealed("PEWTER_CITY|4,2") == {"east"})
ex._mark_now = E.Executor._world_mark(dict(obs, bag={"POTION": 2, "ANTIDOTE": 1}))
ck("...through a change in the bag", ex._sealed("PEWTER_CITY|4,2") == {"east"})
ex._mark_now = E.Executor._world_mark(dict(obs, badges=["BOULDERBADGE"],
                                           flags=obs["flags"] + ["EVENT_BEAT_BROCK"]))
ck("...and lifts when an event fires", ex._sealed("PEWTER_CITY|4,2") == set())
ex = fresh()
ex._seam_proof(obs, {"op": "cross", "dir": "east"},
               DET.split(" — and while it spoke")[0])
ck("words alone, with no walk-back, record nothing", not ex._no_cross)

src = (ROOT / "harness/shim.lua").read_text()
ck("the shim tracks a cross's closest approach and walk-back",
   "if not gp.best or d < gp.best then gp.best = d end" in src
   and "gp.back, gp.from, gp.bx, gp.by = d - gp.best, gp.best, p.cellX, p.cellY" in src
   and "wd.steps.gap = { m = startMap, x = ex, y = ey," in src)
ck("...and says so", "and while it spoke you were walked back: " in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

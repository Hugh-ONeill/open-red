#!/usr/bin/env python3
"""Explore does not walk off a floor whose one unfinished thing is a switch
statue never pressed; it says what is left and stops.

Run 27, 2026-09-18, Pokemon Mansion B1F: explore never presses a switch
(it moves the whole building's walls; the model chooses), so with SWITCH
(20,3) the only thing untouched the floor read as done, and explore walked
the party to a pocket of 1F, where the run judged itself trapped and used
an ESCAPE_ROPE (user: "it was in the basement, it just didnt have the
curiosity to explore the whole way").

Pinned: an untouched, reachable switch statue stops explore before it
walks away, with the press op spelled out, the same as a boulder does. So
does a statue already pressed, while the floor still has unseen ground no
walk reaches in the current setting (B1F again, same day: both statues had
been pressed, 7 spots unseen, and explore walked the party up to 3F twice).
Source-anchored: the step runs the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
n = src.index("    def _explore_step")
blk = src[n:n + 60000]
ck("an untouched reachable switch statue stops explore",
   '_levers_here = [c for c in cands\n                        if "SWITCH" in str(c.key).upper()\n                        and c.status == "untouched" and c.reachable]' in blk)
ck("...saying what is left and spelling the press",
   "what is left on this floor is " in blk and '"answer":"yes"}}. ' in blk
   and "Walking off this floor leaves it exactly as it is." in blk)
ck("...after the boulder rule and before the walk to another area",
   blk.index("_rocks_here = [c for c in cands") < blk.index("_levers_here = [c for c in cands")
   < blk.index("# nowhere here: the nearest area over walked ground"))
ck("a pressed, reachable statue stops it too while the floor has ground no walk reaches",
   '_statues = [c for c in cands if getattr(c, "toggle", None)' in blk
   and "if _fn_here and _statues:" in blk
   and "no walk from here reaches them with the statues set to" in blk)
ck("...counting the whole floor's unseen ground, not only the walled-in part stood in",
   'int(_sn_here.get("frontier_map_n") or 0)' in blk)
ck("...and saying where the statue stands decides which side of the walls you are left on",
   "are left on is decided by where the statue you press" in blk)
_lsrc = (ROOT / "planner/ledger.py").read_text()
ck("the lever row no longer says a statue never pressed is not an untried thing",
   "is not an untried thing, and" not in _lsrc
   and "which side of them you are left on is decided by" in _lsrc)
ck("...after the unpressed-statue rule and before the walk to another area",
   blk.index("_levers_here = [c for c in cands") < blk.index("if _fn_here and _statues:")
   < blk.index("# nowhere here: the nearest area over walked ground"))
ck("explore still never presses a switch itself",
   'and "SWITCH" not in str(c.key).upper()' in blk)

sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
_ex = object.__new__(E.Executor)
ck("the room sweep does not press a switch statue either (B1F (20,3), pressed with no answer)",
   _ex._not_for_explore_to_press("SWITCH_POKEMON_MANSION_B1F_20_3", "fixture",
                                 "POKEMON_MANSION_B1F|10,9") != "")
ck("...while an ordinary fixture is still swept",
   _ex._not_for_explore_to_press("POKEMONMANSIONB1F_DIARY", "fixture",
                                 "POKEMON_MANSION_B1F|10,9") == "")

_rx = object.__new__(E.Executor)
_rx._where = lambda o: "POKEMON_MANSION_B1F|20,1"
for _step, _note in [({"name": "SWITCH_POKEMON_MANSION_B1F_18_25", "answer": "yes"}, "ok (moved)"),
                     ({"name": "SWITCH_POKEMON_MANSION_B1F_18_25", "answer": "yes"}, "ok — it said: x"),
                     ({"name": "SWITCH_POKEMON_MANSION_B1F_20_3"}, "ok — it said: x"),
                     ({"name": "SWITCH_POKEMON_MANSION_B1F_20_3", "answer": "yes"}, "FAILED — no path")]:
    try:
        _rx._record_outcome({}, "interact", _step, _note)
    except Exception:
        pass
ck("a statue pressed with a yes is counted per statue per map; a declined or failed press is not",
   getattr(_rx, "_lever_presses", {}) == {"POKEMON_MANSION_B1F": {"SWITCH_POKEMON_MANSION_B1F_18_25": 2}},
   getattr(_rx, "_lever_presses", None))
ck("the explore stop lists the least-pressed statue first, each with its count",
   "_statues.sort(key=lambda c: int(_lp.get(c.key) or 0))" in blk
   and '"never pressed with a yes"' in blk)
ck("the tally is kept with the ledger and backfilled once from the outcome rows",
   '"lever_presses": getattr(self, "_lever_presses", {}),' in src
   and "BACKFILL ONCE from the outcome rows" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

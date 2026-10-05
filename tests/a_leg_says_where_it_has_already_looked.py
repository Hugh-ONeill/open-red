#!/usr/bin/env python3
"""A hunt for a thing says where this leg's own attempts have already
looked, so a second attempt can see it is walking the same loop.

Run 28 spent eight attempts on the S.S. Ticket writing the same plan —
Vermilion, the dock, board the ship — while the page's own ways-out row
said ROUTE_24, one walk north, "still has 6 thing(s) never pressed and 10
spot(s) of ground in there never on screen" (user, 2026-09-19: "how has it
not done the bill stuff in 8 attempts of this leg? its not like theres many
places for it to go"). The lead was on the page. What was not was that the
run had already been round this loop.

Pinned: the maps this leg has stood on are counted and kept across its
attempts; the count is cleared when the leg changes; the line holds off
until a second attempt; the map underfoot is marked; a long list is cut; a
place goal does not carry the line; the record is saved with the rest of
the memory. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
ex._leg_tries = 1
ex._leg_looked = {"CERULEAN_CITY": 41}
ck("one attempt in, there is nothing to say yet",
   ex._looked_note({"map": {"id": "CERULEAN_CITY"}}) == "")

ex._leg_tries = 8
ex._leg_looked = {"CERULEAN_CITY": 41, "ROUTE_5": 12, "VERMILION_CITY": 3,
                  "CERULEAN_POKECENTER": 9}
w = ex._looked_note({"map": {"id": "CERULEAN_CITY"}})
ck("the attempts are counted", "across its 8 attempt(s)" in w, w)
ck("the maps are listed, most stood on first",
   "CERULEAN_CITY (41x)" in w
   and w.index("ROUTE_5 (12x)") < w.index("CERULEAN_POKECENTER (9x)")
   < w.index("VERMILION_CITY (3x)"), w)
ck("the one underfoot is marked",
   "CERULEAN_CITY (41x) — you are on it now" in w, w)
ck("and it says what that means, without saying where to go",
   w.rstrip().endswith("What it wants was not on any of them.")
   and "ROUTE_24" not in w and "should" not in w, w)

ex._leg_looked = {f"ROUTE_{i}": i for i in range(1, 14)}
ck("a long list is cut and says how many more",
   ", and 3 more" in ex._looked_note({"map": {}}))
ck("no record, no line",
   E.Executor._looked_note(E.Executor.__new__(E.Executor), {"map": {}}) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("every map the party stands on is counted",
   "self._leg_looked.setdefault(str(mid), 0)" in src)
# ...and since 2026-10-04 filed under its objective when the leg changes,
# and taken back out if that objective comes back (run 36's Secret Key)
ck("the record is kept across a leg's attempts and filed away when it changes",
   '_goal_now = str(plan.get("goal") or "")' in src
   and 'if _goal_now != getattr(self, "_leg_goal", None):' in src
   and 'self._leg_looked = _looked' in src)
ck("...and each attempt counts itself",
   'self._leg_tries = int(getattr(self, "_leg_tries", 0)) + 1' in src)
ck("it survives a relaunch with the rest of the memory",
   '"leg_looked": getattr(self, "_leg_looked", {}),' in src
   and 'self._leg_looked = data.get("leg_looked") or {}' in src)
ck("a hunt carries the line; a place goal keeps its own routing",
   'if not str(target or "").startswith(("map:", "area:")):\n'
   "            move_head += self._looked_note(obs)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

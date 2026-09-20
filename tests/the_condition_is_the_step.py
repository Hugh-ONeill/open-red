#!/usr/bin/env python3
"""The condition is the step (2026-09-04).

The rewrite wrote "Use the elevator to leave the Rocket Hideout B4F" over the
condition {"map":"ROCKET_HIDEOUT_ELEVATOR"}. Standing on B2F beside a lift door
listed as never taken, the run took the stairs down to hunt "the elevator at
(24,15)" on B4F, three rounds running (user: "the damn goal text messes it up
by telling it that the elevator is on b4f"). Both halves are the plan's own
words; when the words name a floor the condition does not, the page says which
half counts. It never says where a door leads.

Synthetic: no game, no model."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                   # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
e = object.__new__(E.Executor)
w = e._words_vs_condition("Use the elevator to leave the Rocket Hideout B4F", {"map": "ROCKET_HIDEOUT_ELEVATOR"})
ck("a floor in the words that the condition does not name is called out", "THE CONDITION IS THE STEP" in w and "(B4F)" in w, w)
ck("...saying any floor's door into the map counts", "whichever floor's door you take into it" in w, w)
ck("...and that the floor was the plan-writer's guess", "plan-writer's guess" in w, w)
ck("...without naming any door or where it leads", "24,19" not in w and "B2F" not in w, w)
w2 = e._words_vs_condition("Locate and enter the Secret House in the north area of the Safari Zone", {"map": "SAFARI_ZONE_SECRET_HOUSE"})
ck("an AREA in the words the condition does not name is called out too", "(NORTH)" in w2 and "THE CONDITION IS THE STEP" in w2, w2)
ck("...and it never says which area it really is", "WEST" not in w2, w2)
ck("an area the condition itself names is not stray",
   e._words_vs_condition("Cross the north area", {"map": "SAFARI_ZONE_NORTH"}) == "")
ck("a bare direction is not an area claim",
   e._words_vs_condition("Travel to the north exit of Route 5", {"map": "ROUTE_5"}) == "")
ck("a floor the condition itself names is not stray", e._words_vs_condition("Climb to B4F", {"map": "ROCKET_HIDEOUT_B4F"}) == "")
ck("a rooftop word against a mart floor is stray", "(ROOFTOP)" in e._words_vs_condition("Buy water on the rooftop", {"map": "CELADON_MART_5F"}))
ck("an area condition is read by its map", "(B4F)" in e._words_vs_condition("the lift on B4F", {"area": "ROCKET_HIDEOUT_ELEVATOR|0,1"}))
ck("no floor word, nothing said", e._words_vs_condition("Enter the Pokemon Tower", {"map": "POKEMON_TOWER_1F"}) == "")
w3 = e._words_vs_condition("Get the Scope on B4F", {"has_item": {"SILPH_SCOPE": 1}})
ck("a non-map condition with a floor in the words says the condition names no place",
   "names no place; it holds wherever it comes true" in w3 and "(B4F)" in w3, w3)
w4 = e._words_vs_condition("Buy Fresh Water from the clerk on the first floor", {"has_item": {"FRESH_WATER": 1}})
ck("...a spelled-out floor too (the Fresh Water step, 2026-09-17)", "(FIRST FLOOR)" in w4 and "plan-writer's guess" in w4, w4)
ck("...and nothing without a floor word", e._words_vs_condition("Buy Fresh Water from the clerk", {"has_item": {"FRESH_WATER": 1}}) == "")
ck("junk is tolerated", e._words_vs_condition(None, None) == "" and e._words_vs_condition("x", {"map": 7}) == "")
src = (ROOT / "planner" / "executor.py").read_text()
ck("it rides the step statement at the top of the prompt",
   'user = (f"SUBGOAL: {goal}\\nDONE_WHEN: {pred_text.dumps(done)}"\n                    f"{self._area_ids_note(done, obs)}"\n                    f"{self._words_vs_condition(goal, done, obs)}"' in src)   # obs: the flag translation counts what has fired
bad = [x for x in checks if not x[1]]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"\n      {str(d)[:300]}"))
print(f"{len(checks) - len(bad)}/{len(checks)} checks pass")
sys.exit(1 if bad else 0)

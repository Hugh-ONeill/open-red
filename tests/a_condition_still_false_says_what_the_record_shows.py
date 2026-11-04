#!/usr/bin/env python3
"""A DONE_WHEN still false says, for each condition, what the record shows.

User, 2026-11-04 (from the staleness pass, look-at "say why DONE_WHEN is
still false", first seen run 63): only new_map_from, not_maps and player_at
had words beside the bare JSON; build it for every kind. Facts off the
observation only, nothing about how to make the condition true.

Pinned: a false has_item, party_min_level, badge and flag each get a clause
with the record's own numbers; a condition that holds gets none; with every
condition true the line is empty; the escalation prompt carries it.
Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex._where = lambda o: f"{o['map']['id']}|20,0"
obs = {"mode": "overworld", "map": {"id": "CERULEAN_CITY"}, "player": {"x": 9, "y": 12},
       "bag": {"POTION": 3}, "badges": ["BOULDERBADGE"], "flags": [],
       "party": [{"species": "PIKACHU", "level": 18, "hp": 40, "max_hp": 47},
                 {"species": "IVYSAUR", "level": 21, "hp": 61, "max_hp": 61}]}
done = {"has_item": {"S_S_TICKET": 1}, "party_min_level": 20,
        "badge": "CASCADEBADGE", "flag": "EVENT_GOT_SS_TICKET", "map": "CERULEAN_CITY"}
t = ex._why_still_false(done, obs)
ck("the line is there", t.startswith("\nNOT YET TRUE: "), t)
ck("has_item says what the bag holds", "the bag holds S_S_TICKET x0" in t, t)
ck("party_min_level gives the levels", "PIKACHU L18, IVYSAUR L21" in t, t)
ck("badge names the badges held", "badges held: BOULDERBADGE" in t, t)
ck("flag says it has not fired", "that event has not fired" in t, t)
ck("a condition that holds gets no clause", "map " not in t.split("NOT YET TRUE: ")[1], t)
ck("all true, no line", ex._why_still_false({"map": "CERULEAN_CITY"}, obs) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("the escalation prompt carries it",
   'DONE_WHEN: {pred_text.dumps(done)}"\n                    f"{self._why_still_false(done, start)}"' in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

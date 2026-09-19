#!/usr/bin/env python3
"""The new-species question says which "every party member is at least
level N" leg the model's own outline asks next, and that a catch into the
party counts toward it; the level page names the deposit op even when the
box is empty.

The species question fired only in Victory Road in run 27 (seven times, two
yeses), where a new member was a L22 MACHOP beside a party at 50. A fresh
game asks it from Route 1 on, where a yes puts a L3 CATERPIE into a party
the outline next asks to be "at least level 12", every member of it (user,
2026-09-19: "it might be overtuned to be a catch-o-holic and that could be
negative unless the bot understands to deposit unhelpful pokemon").

Pinned: the first party-wide level leg after the high-water mark is named,
with its position; a catch "joins the party" with room and "goes to the PC
box" when full; the deposit op is said; no such leg ahead, no words; the
question carries the line; the level page says the deposit op with an empty
box and a member short, and not for a party of one. Synthetic."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp(prefix="levellegs_"))
plans, run = tmp / "plans", tmp / "run"
plans.mkdir()
run.mkdir()
(plans / "outline.txt").write_text("\n".join([
    "Choose a starter Pokemon", "Reach Viridian City",
    "every party member is at least level 12",
    "Defeat Brock for the Boulder Badge",
    "every party member is at least level 20"]) + "\n")
(run / "outline_leg").write_text("1")
E.PLANS, E.RUN = plans, run

ex = object.__new__(E.Executor)
three = [{"species": "BULBASAUR", "level": 8}, {"species": "PIDGEY", "level": 4},
         {"species": "RATTATA", "level": 3}]
w = ex._party_level_legs_words(three)
ck("the next party-wide level leg is named with its position",
   'leg 3: "every party member is at least level 12"' in w, w)
ck("...it counts every member, and the box counts for nothing",
   "counts EVERY Pokemon in the party" in w and "PC box counts for nothing" in w)
ck("...with room, a catch joins the party", "A catch now joins the party." in w)
ck("...and no deposit op is offered there", "pc_deposit" not in w)
full = three + [{"species": "CATERPIE", "level": 3}] * 3
ck("with six, a catch goes to the box",
   "Your party is full, so a catch now goes to the PC box." in
   ex._party_level_legs_words(full))
(run / "outline_leg").write_text("3")
ck("a leg already passed is not named; the next one is",
   'leg 5: "every party member is at least level 20"'
   in ex._party_level_legs_words(three))
(run / "outline_leg").write_text("5")
ck("no such leg ahead, no words", ex._party_level_legs_words(three) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("the species question carries it",
   "+ self._party_level_legs_words(party)\n                + \"Try to catch it?\")"
   in src)
ck("the level page does not invite a deposit with an empty box",
   "Your PC storage holds nothing. At any" not in src)

# ------------------------------------------ the floor on a party-wide leg
# (user: "as long as it doesnt 'solve' level legs by depositing all
# underleveled pokemon")
E.RUN = run
E.Executor.PARTY_FLOOR_PATH = run / "party_floor.json"
rows = []
ex.log = lambda k, **kw: rows.append((k, kw))
four = [{"species": s, "level": lv} for s, lv in
        (("IVYSAUR", 14), ("PIDGEY", 9), ("RATTATA", 8), ("CATERPIE", 7))]
LEG = {"goal": "every party member is at least level 12"}
STEP = [{"id": "t", "done_when": {"party_min_level": 12}}]
ck("a party-wide level leg takes the party's size as its floor",
   ex._party_floor(LEG, STEP, {"party": four}) == 4 and E.PARTY_FLOOR == 4)
ck("...a party of one at L14 does not meet it",
   not E.pred_holds({"party_min_level": 12}, {"party": four[:1]}))
ck("...four at L12 do",
   E.pred_holds({"party_min_level": 12}, {"party": [dict(m, level=12) for m in four]}))
ck("...and a swap that keeps the size does",
   E.pred_holds({"party_min_level": 12}, {"party": [dict(four[0]), {"species": "HITMONLEE", "level": 32},
                           {"species": "PIDGEOTTO", "level": 18},
                           {"species": "RATICATE", "level": 20}]}))
ck("the floor is kept per leg, so a plan written after a shrink keeps it",
   ex._party_floor(LEG, STEP, {"party": four[:1]}) == 4)
ck("a plan with no party-wide level step has no floor",
   ex._party_floor({"goal": "Reach Pewter City"},
                   [{"id": "w", "done_when": {"map": "PEWTER_CITY"}}],
                   {"party": four}) == 0 and E.PARTY_FLOOR == 0
   and E.pred_holds({"party_min_level": 12}, {"party": four[:1]}))
ex._party_floor(LEG, STEP, {"party": four})
ck("the level page says the floor",
   "It also needs at least {PARTY_FLOOR} in the " in src
   and "if PARTY_FLOOR > 1 else" in src)
ck("a fresh game clears the floors",
   "run/party_floor.json" in (ROOT / "fresh_discovery.sh").read_text())
ck("the floor is not written into the plan as party_size",
   '"party_size"' not in src[src.index("def _party_floor"):
                             src.index("def run_plan")])
E.PARTY_FLOOR = 0

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

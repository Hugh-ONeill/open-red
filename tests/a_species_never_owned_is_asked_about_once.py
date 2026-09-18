#!/usr/bin/env python3
"""A wild of a species never owned is asked about once, at any party size,
and a yes throws at it.

Run 27, 2026-09-18: catching only ever happened toward a later outline leg
or on a leg that asked for it, so a run whose outline named no sixth member
went on with five and walked past the Dojo's prize (user: "idk if theres
any more catch rungs and we only have 5"). The question is asked at any
party size — gated on a free slot it would catch everything early and
nothing once full (user: "itd be for any unowned species and all the time
instead of just when theres team space").

Pinned: the shim marks a wild foe owned or not from the POKéDEX; the
executor asks once per never-owned species with the roster, the box and
the balls, remembers the answer across attempts, and a yes becomes a catch
want for that species; owned species, trainers, ghosts, the Safari game,
an empty ball count and a species already asked about are not asked; it
yields to the outline's own catch. Synthetic (the model call is stubbed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim marks a wild foe owned or not from the POKeDEX",
   "o.battle.foe.owned = ((_dex.owned or {})[_sp] and true) or false" in shim
   and 'not top.ghost and top.kind ~= "trainer"' in shim)

calls = []


def fake(answer):
    ex = object.__new__(E.Executor)
    ex._new_species_asked = {}
    ex._save_memory = lambda: None
    ex.log = lambda *a, **k: None
    ex.model = "m"
    E.brock_probe.chat = lambda msgs, model: (calls.append(msgs[1]["content"]) or json.dumps(answer))
    return ex


def obs(**kw):
    b = {"kind": "wild", "foe": {"species": "HITMONLEE", "level": 30, "types": ["FIGHTING"], "owned": False}}
    b.update(kw.pop("battle", {}))
    o = {"mode": "battle", "battle": b, "bag": {"POKE_BALL": 5, "GREAT_BALL": 3},
         "party": [{"species": "LAPRAS", "nickname": "NESSIE", "level": 43, "types": ["WATER", "ICE"]}] * 5,
         "pc_mons": []}
    o.update(kw)
    return o


SG = {"id": "give_gold_teeth", "goal_text": "Give the teeth to the Warden."}
ex = fake({"why": "a fighting type fills a gap", "catch": True})
got = ex._ask_new_species(obs(), SG)
ck("a never-owned species is asked about, and a yes is a catch want for it",
   got == {"want": {"species": {"HITMONLEE"}, "types": set()}}, got)
ck("...the question carries the species, the roster and its size, the box and the balls",
   calls and "HITMONLEE L30 (FIGHTING)" in calls[-1] and "YOUR PARTY (5 of 6)" in calls[-1]
   and "IN THE PC BOX: nothing" in calls[-1] and "POKE BALLS IN THE BAG (POKE, GREAT, ULTRA): 8" in calls[-1], calls[-1:])
ck("...and the answer is kept", ex._new_species_asked.get("HITMONLEE", {}).get("catch") is True)
n = len(calls)
ck("the same species is not asked twice", ex._ask_new_species(obs(), SG) is None and len(calls) == n)

ex = fake({"why": "not needed", "catch": False})
ck("a no throws nothing", ex._ask_new_species(obs(), SG) is None and ex._new_species_asked["HITMONLEE"]["catch"] is False)
ex = fake({"catch": True})
six = obs(); six["party"] = six["party"] + [six["party"][0]]
ck("it is asked with a full party too", ex._ask_new_species(six, SG) is not None and "YOUR PARTY (6 of 6)" in calls[-1])
for why, o in (("an owned species", obs(battle={"foe": {"species": "PIDGEY", "level": 9, "owned": True}})),
               ("a trainer's Pokemon", obs(battle={"kind": "trainer"})),
               ("the ghost", obs(battle={"ghost": True})),
               ("the Safari game", obs(safari={"steps": 400, "balls": 30})),
               ("no balls", obs(bag={"POTION": 2})),
               ("only the Master Ball", obs(bag={"MASTER_BALL": 1, "POTION": 2})),
               ("a foe whose ownership is not known", obs(battle={"foe": {"species": "ODDISH", "level": 12}}))):
    ex = fake({"catch": True}); n = len(calls)
    ck(f"not asked for {why}", ex._ask_new_species(o, SG) is None and len(calls) == n)

src = (ROOT / "planner/executor.py").read_text()
ex = fake({"catch": True})
ex._ask_new_species(obs(bag={"MASTER_BALL": 1, "POKE_BALL": 2}), SG)
ck("with balls to throw, the Master Ball is named as not thrown unless named",
   "(POKE, GREAT, ULTRA): 2 — and a MASTER_BALL, which is not thrown unless you name it" in calls[-1], calls[-1:])
ck("it yields to the outline's own catch and to a leg already catching",
   "elif name != \"catch\":\n            _new = self._ask_new_species(obs, subgoal)" in src
   and src.index("_ahead = self._catch_ahead(obs, subgoal, name, _want0)") < src.index("_new = self._ask_new_species(obs, subgoal)"))
ck("the answers are saved and loaded",
   '"new_species_asked": getattr(self, "_new_species_asked", {}),' in src
   and 'self._new_species_asked = data.get("new_species_asked") or {}' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

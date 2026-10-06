#!/usr/bin/env python3
"""A party member with no PP left is brought to the heal questions the way
a fainted one is.

Run 37, 2026-10-05: VENUSAUR had every move at 0 PP and the run walked
into its next fight (user: "the way we have the model alerted to low
health drawing it back to the center we should do the same with PP, rare
but the PP was totally out on venu and it went for a new battle").

Pinned: every move at 0 asks the street question, naming the moves, and
the system prompt says the nurse restores PP; a move or two at 0 does not
ask on the street; at the counter any move at 0 is listed and asked about
even with full HP; a fainted member is not counted for PP; full PP and HP
asks nothing. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


class X(E.Executor):
    pass


def make(reply):
    ex = object.__new__(X)
    ex.model = "m"
    ex.logged, ex.sent, ex.asked = [], [], []
    ex.log = lambda k, **kw: ex.logged.append((k, kw))
    ex._save_memory = lambda: None
    ex.settle = lambda: None
    ex._send_safe = lambda op, **kw: (ex.sent.append(op) or {"result": {"ok": True}})
    E.brock_probe.chat = lambda msgs, model: (ex.asked.append(msgs) or reply)
    return ex


def mv(i, pp, mx):
    return {"id": i, "pp": pp, "max_pp": mx}


DRY = {"species": "VENUSAUR", "level": 36, "hp": 120, "max_hp": 120,
       "moves": [mv("TACKLE", 0, 35), mv("VINE_WHIP", 0, 10), mv("RAZOR_LEAF", 0, 25)]}
LOW = {"species": "VENUSAUR", "level": 36, "hp": 120, "max_hp": 120,
       "moves": [mv("TACKLE", 20, 35), mv("VINE_WHIP", 0, 10)]}
FULL = {"species": "PIDGEY", "level": 10, "hp": 30, "max_hp": 30,
        "moves": [mv("GUST", 35, 35)]}
DOWN = {"species": "RATTATA", "level": 8, "hp": 0, "max_hp": 22,
        "moves": [mv("TACKLE", 0, 35)]}


def street(party):
    return {"mode": "overworld", "party": party, "map": {
        "id": "CELADON_CITY", "outdoor": True, "warps": [
            {"x": 41, "y": 9, "dest": "CELADON_POKECENTER", "seen": True,
             "reachable": True}]}}


ex = make('{"why": "venusaur cannot attack", "heal": true}')
ex._ask_heal_street(street([DRY, FULL]), {"id": "x"})
u = ex.asked[0][-1]["content"] if ex.asked else ""
ck("every move at 0 asks the street question", ex.sent == ["heal"], ex.sent)
ck("...naming the moves", "NO PP LEFT FOR ANY MOVE: VENUSAUR (TACKLE 0/35, VINE_WHIP 0/10" in u, u)
ck("...with nothing said about fainting when nobody has", "FAINTED" not in u, u)
ck("...and the nurse is said to restore PP",
   "restores every move's PP" in ex.asked[0][0]["content"] if ex.asked else False)
ex = make('{"why": "x", "heal": true}')
ex._ask_heal_street(street([LOW, FULL]), {"id": "x"})
ck("a move or two at 0 does not stop the party on the street", not ex.asked)
ex = make('{"why": "x", "heal": true}')
ex._ask_heal_street(street([FULL, DOWN]), {"id": "x"})
ck("a fainted member still asks, as a faint, not as PP",
   ex.asked and "FAINTED: RATTATA" in ex.asked[0][-1]["content"]
   and "NO PP LEFT" not in ex.asked[0][-1]["content"])

ex = make('{"why": "restore vine whip", "heal": true}')
ex._nurse_here = lambda o: True
ex._where = lambda o: "CELADON_POKECENTER|3,7"
room = {"mode": "overworld", "party": [LOW, FULL], "map": {"id": "CELADON_POKECENTER"}}
ex._ask_heal(room, {"id": "x"})
u = ex.asked[0][-1]["content"] if ex.asked else ""
ck("at the counter, a move at 0 is asked about with full HP", bool(ex.asked), ex.logged)
ck("...listed by move", "VENUSAUR (VINE_WHIP 0/10) — moves at 0 PP" in u, u)
ck("...and the heal said to restore PP", "every move's PP with it" in u, u)
ex = make('{"why": "x", "heal": true}')
ex._nurse_here = lambda o: True
ex._where = lambda o: "CELADON_POKECENTER|3,7"
ex._ask_heal({"mode": "overworld", "party": [FULL], "map": {"id": "CELADON_POKECENTER"}}, {"id": "x"})
ck("full HP and PP asks nothing", not ex.asked)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

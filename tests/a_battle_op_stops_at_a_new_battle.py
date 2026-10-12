#!/usr/bin/env python3
"""A battle op stops at the door of a NEW battle, and the policy loop leaves,
so a trainer who engages as a fight closes gets a fight of its own.

Run 54 (2026-10-12): twice a wild fight (ZUBAT on MT_MOON, PIDGEY on
ROUTE_6) was fled, a trainer engaged as it closed, and the op's presses rode
in: the trainer was fought as the same "wild" battle, a flee was tried on
him, and no recap was written. in_battle() reports any battle frame, so the
600-press text loop (120 before next144) could not tell the old fight from
the new. None of run 53's 2486 battles; 2 of run 54's first 543.

Source checks (shim) + a stub bridge for the executor loop.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sh = (ROOT / "harness/shim.lua").read_text()


def body(name):
    s = sh[sh.index(f"function OPS.{name}(G"):]
    return s[:s.index("\nend\n") + 5]


for op in ("battle_move", "battle_run", "battle_switch"):
    b = body(op)
    ck(f"{op} returns at a battle frame that is not its own, before pressing",
       "nb ~= b then return true" in b and "a NEW battle has begun" in b
       and b.index("nb ~= b") < b.rindex('U.tap(G, "a")') if op != "battle_move"
       else ("nb ~= b then return true" in b
             and b.index("nb ~= b") < b.index("U.battle_advance(G, nb)")), op)

ex = (ROOT / "planner/executor.py").read_text()
ck("the policy loop leaves on the shim's words, only for an op it sent",
   '_NEW_BATTLE = "a NEW battle has begun"' in ex and "obs is not _obs_in and _NEW_BATTLE in" in ex)

turn = {"mode": "battle", "party": [{"species": "KADABRA", "hp": 50, "max_hp": 54,
                                     "types": ["PSYCHIC"], "level": 22}],
        "battle": {"kind": "wild", "foe": {"species": "PIDGEY", "level": 15, "hp": 40,
                                           "maxhp": 40, "types": ["NORMAL", "FLYING"]},
                   "me": {"species": "KADABRA", "hp": 50, "maxhp": 54,
                          "moves": [{"index": 1, "id": "CONFUSION", "type": "PSYCHIC",
                                     "power": 50, "pp": 20}]}}}
trainer = {"mode": "battle", "party": turn["party"],
           "battle": {"kind": "trainer", "trainer": "BUG CATCHER",
                      "foe": {"species": "BUTTERFREE", "level": 20, "hp": 57, "maxhp": 57,
                              "types": ["BUG", "FLYING"]}, "me": turn["battle"]["me"]}}
sent, logged = [], []


class Stub:
    def send(self, op, **kw):
        sent.append(op)
        return dict(trainer, result={"ok": True, "detail": "fled — and a NEW battle has "
                                     "begun (someone engaged you as it closed); nothing "
                                     "in it has been pressed"})

    def obs(self):
        return trainer


out = E._run_policy(E.ACTIVE_SPEC or {}, Stub(), turn,
                    lambda k, **kw: logged.append((k, kw)), max_turns=10,
                    intent="traversal")
ck("one op, then the loop hands the new battle back", len(sent) == 1, sent)
ck("...saying why", any(k == "battle_loop_left" and kw.get("why") == "a new battle began"
                        for k, kw in logged), logged[-3:])
ck("...with the trainer's battle up for the caller to open",
   (out or {}).get("battle", {}).get("kind") == "trainer")

# handed an observation that already carries those words (the op that left
# the last fight), the loop still plays the new fight
sent.clear(); logged.clear()
seed = dict(trainer, result={"ok": True, "detail": "battle ended — and a NEW battle has begun"})


class Stub2(Stub):
    def send(self, op, **kw):
        sent.append(op)
        return {"mode": "overworld", "party": turn["party"], "result": {"ok": True}}


E._run_policy(E.ACTIVE_SPEC or {}, Stub2(), seed, lambda k, **kw: logged.append((k, kw)),
              max_turns=10, intent="fight")
ck("the observation it was handed does not end the loop before a turn", len(sent) >= 1, sent)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

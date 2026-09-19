#!/usr/bin/env python3
"""When the policy's train rule says `lead`, the trainee is moved to the
front before a grind in the step that is raising it, and the party goes
back as it stood once that step is over.

The trainee used to reach its battles by a switch on turn one of every
wild, the weak member taking the free hit; in the overworld the same thing
costs nothing. But left in front, a member that has only just reached its
level starts every battle after the step: a rival on a cell, the league.

Pinned: no rule or lead false, no swap; the trainee named by the step's
condition is swapped to slot 1 and the trace says why; a fainted trainee is
not led; a grind marked for catching is left alone; a trainee already in
front is not touched; the swap is undone at the first overworld op of a
LATER step and the trace says so; not while the same step goes on; and not
if the model has moved the trainee itself since. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def party0():
    return [{"species": "LAPRAS", "level": 55, "hp": 250, "max_hp": 250,
             "dvs": {"hp": 15}, "otId": 1},
            {"species": "PIDGEOT", "level": 50, "hp": 170, "max_hp": 170,
             "dvs": {"hp": 15}, "otId": 1},
            {"species": "MACHOP", "level": 24, "hp": 70, "max_hp": 74,
             "dvs": {"hp": 8}, "otId": 1}]


class Ex(E.Executor):
    def __init__(self, party):
        self.party, self.sent, self.rows = party, [], []
        self._train_led = None

    def __getattr__(self, n):
        return {}

    def _send_safe(self, op, **kw):
        self.sent.append((op, kw))
        if op == "party_swap":
            a, b = kw["a"] - 1, kw["b"] - 1
            self.party[a], self.party[b] = self.party[b], self.party[a]
        return {"result": {"ok": True}}

    def settle(self):
        return self.obs()

    def obs(self):
        return {"mode": "overworld", "party": [dict(m) for m in self.party]}

    def log(self, kind, **kw):
        self.rows.append((kind, kw))


TRAIN = {"id": "train_machop", "goal_text": "Raise Machop to 30",
         "done_when": {"slot_level": {
             "slot": 3, "min": 30,
             "who": {"species": "MACHOP", "dvs": {"hp": 8}, "otId": 1}}}}
NEXT = {"id": "go_to_league", "goal_text": "Walk to the Indigo Plateau",
        "done_when": {"map": "INDIGO_PLATEAU"}}
GRIND = {"op": "grind"}

E.ACTIVE_SPEC = {"flee_wild": {"hp_below": 0.3}}
ex = Ex(party0())
ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, [])
ck("a policy with no train rule moves nobody", ex.sent == [])
E.ACTIVE_SPEC = {"train": {"lead": False}}
ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, [])
ck("...nor one whose rule says lead false", ex.sent == [])

E.ACTIVE_SPEC = {"train": {"lead": True}}
trace = []
o = ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, trace)
ck("the trainee the step names is swapped to the front",
   ex.sent == [("party_swap", {"a": 1, "b": 3})]
   and o["party"][0]["species"] == "MACHOP", ex.sent)
ck("...and the trace says why",
   trace and "MACHOP L24 leads" in trace[0] and "train rule" in trace[0], trace)
ck("...logged", any(k == "train_lead" for k, _ in ex.rows))
ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, [])
ck("a trainee already in front is not touched", len(ex.sent) == 1)

trace = []
ex._unlead_the_trainee(ex.obs(), TRAIN, trace)
ck("the order stays while the same step goes on", len(ex.sent) == 1 and not trace)
ex._unlead_the_trainee(dict(ex.obs(), mode="battle"), NEXT, trace)
ck("...and is not touched from inside a battle", len(ex.sent) == 1)
o = ex._unlead_the_trainee(ex.obs(), NEXT, trace)
ck("a later step puts the party back as it stood",
   ex.sent[-1] == ("party_swap", {"a": 1, "b": 3})
   and [m["species"] for m in o["party"]] == ["LAPRAS", "PIDGEOT", "MACHOP"],
   [m["species"] for m in o["party"]])
ck("...and the trace says so",
   trace and "goes back to slot 3" in trace[-1], trace)
n = len(ex.sent)
ex._unlead_the_trainee(ex.obs(), NEXT, [])
ck("...once", len(ex.sent) == n)

# the model moved it
ex = Ex(party0())
ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, [])
ex._send_safe("party_swap", a=1, b=2)      # the model's own swap
n = len(ex.sent)
ex._unlead_the_trainee(ex.obs(), NEXT, [])
ck("if the model has moved the trainee since, its order stands",
   len(ex.sent) == n and ex._train_led is None)

# an evolved trainee is still the one that was led
ex = Ex(party0())
ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, [])
ex.party[0]["species"] = "MACHOKE"
o = ex._unlead_the_trainee(ex.obs(), NEXT, [])
ck("a trainee that evolved in front is still put back",
   o["party"][2]["species"] == "MACHOKE")

ex = Ex(party0())
ex.party[2]["hp"] = 0
ex._lead_the_trainee(ex.obs(), GRIND, TRAIN, [])
ck("a fainted trainee is not led", ex.sent == [])
ex = Ex(party0())
ex._lead_the_trainee(ex.obs(), {"op": "grind", "intent": "catch"}, TRAIN, [])
ck("a grind marked for catching is left alone", ex.sent == [])
ex = Ex(party0())
ex._lead_the_trainee(ex.obs(), GRIND, NEXT, [])
ck("a step with no trainee moves nobody", ex.sent == [])
ex = Ex(party0())
ex._lead_the_trainee(ex.obs(), GRIND,
                     {"id": "all50", "goal_text": "everyone to 53",
                      "done_when": {"party_min_level": 53}}, [])
ck("every-member-at-least leads the lowest still short",
   ex.sent == [("party_swap", {"a": 1, "b": 3})], ex.sent)

src = (ROOT / "planner/executor.py").read_text()
ck("the op loop undoes before any op and leads before a grind",
   "obs = self._unlead_the_trainee(obs, sg, trace)\n            if op == \"grind\":\n"
   "                obs = self._lead_the_trainee(obs, step, sg, trace)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

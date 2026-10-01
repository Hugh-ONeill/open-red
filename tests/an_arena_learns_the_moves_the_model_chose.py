#!/usr/bin/env python3
"""A savepoint arena answers a learn-move offer from the model's own answer,
asked once (plans/arena_learn.json), instead of asking a model it does not have.

Every such offer used to go to the server as {"model": ""}, come back 400
"model is required" and fall back to keeping the old moves, every trial
(2026-10-01). User: "we can do what the model pre-chooses as that table".
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tools"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import executor as E  # noqa: E402
import arena_learn_table as T  # noqa: E402


class FakeBridge:
    def __init__(self):
        self.sent = []

    def send(self, op, **kw):
        self.sent.append((op, kw))
        return {}


x = object.__new__(E.Executor)
x.model = ""
x.b = FakeBridge()
x._logged = []
x.log = lambda kind, **kw: x._logged.append((kind, kw))
x.settle = lambda: None
x._is_question = lambda o: False
obs = {"mode": "ui", "party": [{"species": "LAPRAS", "types": ["WATER", "ICE"]}],
       "ui": {"screenId": "MoveLearnMenu", "selecting": True,
              "learn": {"learner": "LAPRAS", "learner_slot": 1,
                        "new_move": {"id": "HYDRO_PUMP", "type": "WATER", "power": 120},
                        "moves": [{"id": "SURF"}, {"id": "ICE_BEAM"}, {"id": "BODY_SLAM"},
                                  {"id": "CONFUSE_RAY"}]}}}
E.Executor.LEARN_TABLE = {"LAPRAS|HYDRO_PUMP": {"forget": "SURF", "why": "stronger water move"}}
x._maybe_forget(obs, {"id": "room"})
ck("a room with no model forgets what its table says",
   x.b.sent[:1] == [("menu", {"index": 1})], x.b.sent)
ck("...and says where the answer came from",
   any(k == "move_forget" and kw.get("forget") == "SURF" and "table" in kw.get("why", "")
       for k, kw in x._logged), x._logged)

x.b = FakeBridge(); x._logged = []
E.Executor.LEARN_TABLE = {}
x._maybe_forget(obs, {"id": "room"})
ck("no row keeps the old moves (CANCEL), without a model call",
   x.b.sent[:1] == [("menu", {"index": 5})]
   and not any(k == "forget_chat_error" for k, _ in x._logged), (x.b.sent, x._logged))

src = inspect.getsource(E.Executor._maybe_forget)
ck("the live run still asks the model the same question",
   "Executor._forget_user(" in src and "if not self.model:" in src)
pa = (ROOT / "planner/policy_author.py").read_text()
ck("each arena room loads its own rows before it boots",
   'ex_mod.Executor.LEARN_TABLE = (json.loads(' in pa
   and pa.index("ex_mod.Executor.LEARN_TABLE") < pa.index("g = Gym(args.plan"))

data = T.game_data()
offers = T.offers({"party": [{"species": "LAPRAS", "level": 45,
                              "moves": ["SURF", "ICE_BEAM", "BODY_SLAM", "CONFUSE_RAY"]},
                             {"species": "BULBASAUR", "level": 10,
                              "moves": ["TACKLE", "GROWL", "LEECH_SEED"]}]}, data, 5)
ck("the tool finds each member's next moves in level order",
   [(m["species"], mv) for m, mv, _at in offers]
   == [("LAPRAS", "HYDRO_PUMP"), ("BULBASAUR", "VINE_WHIP")], offers)
bulba = [o for o in offers if o[0]["species"] == "BULBASAUR"]
asked = []
walk = T.walk_member(bulba[0][0], bulba, lambda k, mv, at: (asked.append(mv), (None, ""))[1])
ck("...a free slot learns without a question", not asked and walk[0][4] is False)
kad = {"species": "KADABRA", "level": 37, "moves": ["CONFUSION", "THUNDER_WAVE", "PSYBEAM", "RECOVER"]}
seen = []


def _ans(known, mv, at):
    seen.append((mv, tuple(known)))
    return ({"PSYCHIC_M": "CONFUSION", "REFLECT": "PSYBEAM"}[mv], "")


walk = T.walk_member(kad, [(kad, "PSYCHIC_M", 38), (kad, "REFLECT", 42)], _ans)
ck("each answer is applied before the next offer is asked (PSYCHIC known at REFLECT)",
   seen == [("PSYCHIC_M", ("CONFUSION", "THUNDER_WAVE", "PSYBEAM", "RECOVER")),
            ("REFLECT", ("PSYCHIC_M", "THUNDER_WAVE", "PSYBEAM", "RECOVER"))], seen)
ck("...and the second row forgets from that moveset",
   [(mv, f) for mv, _at, f, _w, _a in walk] == [("PSYCHIC_M", "CONFUSION"), ("REFLECT", "PSYBEAM")], walk)
ck("...shown as the summary screen shows them",
   T.shown("HYDRO_PUMP", data["moves"]) == "HYDRO_PUMP (WATER, power 120, PP 5)"
   and T.shown("SURF", data["moves"], 15) == "SURF (WATER, power 95, PP 15/15)")
ck("...with the room's own aim as the goal",
   T.room_goal("catch_abra", "catch", {"catch": {"want_species": ["ABRA"]}}) == "Catch a ABRA Pokemon"
   and T.room_goal("e4_real", "e4", {}) == "Defeat the Elite Four and the Champion")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

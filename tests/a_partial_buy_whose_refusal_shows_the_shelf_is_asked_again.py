#!/usr/bin/env python3
"""A buy list cut short by a refusal that shows the shelf is asked once more,
even when part of it was already bought.

The Plateau lobby's first visit: shelf unknown, MAX_POTION x10 bought,
MAX_REVIVE refused ("not on the shelf, which holds: ... REVIVE ..."), and the
re-ask was gated on nothing having been bought yet, so the run walked into
Lorelei with no revive (run 19, 2026-09-30).

Synthetic, on the counter test's fixture shape.
"""
from __future__ import annotations

import copy
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import brock_probe  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


E.set_active_spec({"battle_items": [{"item": "HYPER_POTION", "hp_below": 0.3}]})
LOBBY = {"mode": "overworld", "money": 61540,
         "map": {"id": "INDIGO_PLATEAU_LOBBY", "region": "8,0",
                 "objects": [{"name": "INDIGOPLATEAULOBBY_CLERK", "kind": "person",
                              "reachable": True, "x": 0, "y": 5}]},
         "bag": {"ULTRA_BALL": 3},
         "party": [{"species": "GRAVELER", "level": 63, "hp": 150, "max_hp": 180}]}
SHELF_TXT = ("MAX_REVIVE is not on INDIGOPLATEAULOBBY_CLERK's shelf, which holds: "
             "ULTRA_BALL, GREAT_BALL, FULL_RESTORE, MAX_POTION, FULL_HEAL, REVIVE, MAX_REPEL")
answers = ['{"why":"heal up","buy":[{"item":"MAX_POTION","count":10},{"item":"MAX_REVIVE","count":5}]}',
           '{"why":"revives for the league","buy":[{"item":"REVIVE","count":4}]}']
asked, sent = [], []


def send(op, **kw):
    sent.append((op, kw))
    it = kw.get("item")
    if it == "MAX_REVIVE":
        return {"result": {"ok": False, "detail": SHELF_TXT}}
    return {"result": {"ok": True, "detail": f"bought: {it}"}}


o = types.SimpleNamespace(model="stub", logged=[])
o._send_safe = send
o.settle = lambda: copy.deepcopy(LOBBY)
o.log = lambda kind, **kw: o.logged.append((kind, kw))
for name in ("_where", "_clerk_here", "_policy_unmet"):
    setattr(o, name, getattr(E.Executor, name))
for name in ("_policy_heal_line", "_shop_street", "_ball_lines", "_heal_upgrade", "_heal_lines"):
    setattr(o, name, types.MethodType(getattr(E.Executor, name), o))
for name in ("BUY_SYS", "BUY_STREET_SYS", "SHOP_COUNTER_FLOOR", "BUY_MAX_ENTRIES", "BAG_SLOTS"):
    setattr(o, name, getattr(E.Executor, name))
o._shelves, o._shelf_reads, o._cant_afford = {}, {}, {}
o._save_memory = lambda: None
o._ball_need = lambda obs, shop_map="": None
o._ask_buy = types.MethodType(E.Executor._ask_buy, o)
brock_probe.chat = lambda msgs, model, **kw: (asked.append(msgs) or answers[min(len(asked) - 1, 1)])

o._ask_buy(copy.deepcopy(LOBBY), {"id": "heal_before_elite_four", "goal_text": "Heal"})
ck("asked twice: the refusal showed the shelf", len(asked) == 2, len(asked))
second = asked[-1][-1]["content"] if len(asked) > 1 else ""
ck("...and the second question knows what this visit already bought",
   "ALREADY BOUGHT AT THIS COUNTER THIS VISIT: MAX_POTION x10" in second, second[-600:])
ck("...and shows the shelf the refusal named", "REVIVE" in second and "FULL_RESTORE" in second)
ck("the revive is bought on the second answer",
   any(op == "buy" and kw.get("item") == "REVIVE" for op, kw in sent), sent)
ck("the re-ask happens once, not in a loop", len(asked) <= 2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

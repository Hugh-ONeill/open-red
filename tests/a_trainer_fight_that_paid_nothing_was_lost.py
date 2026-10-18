#!/usr/bin/env python3
"""A trainer fight that paid nothing was lost (runs 54 and 56, 2026-10-14).

The lab rival's loss has no blackout: no "blacked out!", no Center, no money
taken. The recap read none of its loss signs and called it won (BULBASAUR
fainted, CHARMANDER at 2 hp, money still 3000; user: "the events say beat
rival even when it loses"). Every trainer beaten pays "got ¥N for winning!",
so out of the fight with the money not up is a loss.

Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def recap(m0, m1, party, said="", mode="overworld", dialog=None):
    x = object.__new__(E.Executor)
    f = Path(tempfile.mkdtemp()) / "log.jsonl"
    f.write_text(json.dumps({"kind": "battle_turn", "op": "battle_move",
                             "why": "TACKLE score=35.0 eff=1.0", "foe_hp": 2}) + "\n")
    x.logf = open(f)
    x._last_overworld_map = "OAKS_LAB"
    x.log = lambda *a, **k: None
    before = {"money": m0, "party": [{"species": "BULBASAUR", "hp": 19, "max_hp": 19}],
              "battle": {"trainer": "MILO", "foe": {"species": "CHARMANDER", "level": 5}}}
    after = {"money": m1, "party": party, "map": {"id": "OAKS_LAB"},
             "mode": mode, "recent_text": said}
    if dialog is not None:
        after["dialog"] = dialog
    x._note_fight(before, after, 0)
    return getattr(x, "_last_fight", {}) or {}


healed = [{"species": "BULBASAUR", "hp": 19, "max_hp": 19}]
hurt = [{"species": "BULBASAUR", "hp": 7, "max_hp": 19}]
ck("the lab loss: healed, money unchanged, nothing said of winning: lost",
   recap(3000, 3000, healed).get("lost") is True)
ck("a win that paid: not lost", recap(3000, 3175, hurt).get("lost") is False)
ck("the prize line on screen with the money unread as up: not lost",
   recap(3000, 3000, hurt, said="RED got ¥175 for winning!").get("lost") is False)
ck("money unread on either side: this rule says nothing",
   recap(None, 3000, hurt).get("lost") is False)
ck("still in the fight when read: this rule says nothing",
   recap(3000, 3000, hurt, mode="battle").get("lost") is False)

# Run 58, 2026-10-18: "VENUSAUR grew to level 43!" over a live fight with a
# Silph Scientist; the recap was written then and read as a loss.
ck("a text box over a fight still on screen: this rule says nothing",
   recap(3000, 3000, hurt, mode="dialog",
         dialog={"text": "VENUSAUR grew to level 43!", "over_fight": True}
         ).get("lost") is not True)
ck("...and a text box with no fight under it, money not up: still lost",
   recap(3000, 3000, healed, mode="dialog",
         dialog={"text": "MILO: Yeah! Am I great or what?"}).get("lost") is True)
lua = (ROOT / "harness/shim.lua").read_text()
ck("the shim marks a text box with a battle frame under it",
   "if battle_frame(G) then o.dialog.over_fight = true end" in lua)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

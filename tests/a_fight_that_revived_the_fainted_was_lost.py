#!/usr/bin/env python3
"""A fight that revived the fainted was lost (run 18, 2026-09-28).

Mt. Moon's Super Nerd was fought by a lone PIDGEY with three fainted behind
it; the party blacked out, the blackout healed everyone before the recap read
the party, and the recap said "lost": false. No won fight revives anyone and
a blackout heals to full: fainted going in, none fainted and all at full HP
coming out, is a loss.

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


def mon(sp, hp, mx):
    return {"species": sp, "hp": hp, "max_hp": mx}


def recap(before_party, after_party, after_map="MT_MOON_B2F"):
    x = object.__new__(E.Executor)
    f = Path(tempfile.mkdtemp()) / "log.jsonl"
    f.write_text(json.dumps({"kind": "battle_turn", "op": "battle_move",
                             "why": "QUICK_ATTACK score=60.0 eff=1.0", "foe_hp": 11}) + "\n")
    x.logf = open(f)
    x._last_overworld_map = "MT_MOON_B2F"
    x.log = lambda *a, **k: None
    before = {"party": before_party, "battle": {"trainer": "SUPER NERD",
                                                  "foe": {"species": "GRIMER", "level": 12}}}
    after = {"party": after_party, "map": {"id": after_map}}
    try:
        x._note_fight(before, after, 0)
    except Exception:
        pass
    return getattr(x, "_last_fight", {}) or {}


went_in = [mon("PIDGEY", 23, 47), mon("IVYSAUR", 0, 58), mon("PIKACHU", 0, 31), mon("GEODUDE", 0, 25)]
healed = [mon("PIDGEY", 47, 47), mon("IVYSAUR", 58, 58), mon("PIKACHU", 31, 31), mon("GEODUDE", 25, 25)]
ck("fainted going in, everyone full coming out: lost",
   recap(went_in, healed).get("lost") is True, recap(went_in, healed))
won = [mon("PIDGEY", 8, 47), mon("IVYSAUR", 0, 58), mon("PIKACHU", 0, 31), mon("GEODUDE", 0, 25)]
ck("a win with the fainted still fainted: not lost", recap(went_in, won).get("lost") is False)
revive = [mon("PIDGEY", 8, 47), mon("IVYSAUR", 29, 58), mon("PIKACHU", 0, 31), mon("GEODUDE", 0, 25)]
ck("a Revive used mid-fight is not a blackout",
   recap([mon("PIDGEY", 23, 47), mon("IVYSAUR", 0, 58)], [mon("PIDGEY", 8, 47), mon("IVYSAUR", 29, 58)]).get("lost") is False)
ck("nobody fainted going in, everyone full after: not read as a blackout by this rule",
   recap([mon("PIDGEY", 47, 47)], [mon("PIDGEY", 47, 47)]).get("lost") is False)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

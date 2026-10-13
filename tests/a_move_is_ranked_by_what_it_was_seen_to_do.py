#!/usr/bin/env python3
"""A move is ranked by what the HP bar has shown it do, not by the move
table's power and accuracy, which no Gen 1 screen prints.

The engine scored every move power x chart x STAB x accuracy off the
table (user, 2026-10-13: "this is a serious breach"). Now each use of a
damaging move is filed per member: the share of the foe's bar it took,
over the chart and the level gap; a miss files 0; a 0x hit is not filed.
A move never seen gets this member's best seen move as its guess, so it is
tried once and its record takes over.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as bp                                      # noqa: E402
import executor as E                                            # noqa: E402

fails = []


def ck(name, cond, det=""):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {str(det)[:300]}"))
    if not cond:
        fails.append(name)


ME = {"species": "PIDGEOT", "level": 39, "hp": 120, "maxhp": 126, "types": ["NORMAL", "FLYING"],
      "status": None,
      "moves": [{"index": 1, "id": "RAZOR_WIND", "type": "NORMAL", "power": 80, "accuracy": 75, "pp": 10},
                {"index": 2, "id": "WING_ATTACK", "type": "FLYING", "power": 35, "accuracy": 100, "pp": 35}]}
FOE = {"species": "RATTATA", "level": 39, "hp": 100, "maxhp": 100, "types": ["NORMAL"], "status": None}


def battle(me, foe):
    return {"mode": "battle", "bag": {}, "party": [dict(me, max_hp=me["maxhp"])],
            "battle": {"kind": "wild", "partyIndex": 0, "enemyIndex": 0, "me": me, "foe": foe}}


spec = dict(bp.DEFAULT_SPEC, name="t", battle_items=[], setup=[])
bp.MOVE_SEEN.clear()
s1 = bp.score_move(ME["moves"][0], ME, FOE, spec)["score"]
s2 = bp.score_move(ME["moves"][1], ME, FOE, spec)["score"]
ck("with nothing seen, the table's 80 against 35 decides nothing (both guessed alike)",
   s1 == s2, (s1, s2))

# what the bar showed: RAZOR_WIND charges a turn (0) then hits 40%; WING_ATTACK 28% every turn
before = {"me": ME, "foe": FOE, "_text_seq": 0}


def turn(hp, line):
    return {"mode": "battle", "battle_text": line, "battle_text_seq": len(line.split(" / ")),
            "battle": {"me": ME, "foe": dict(FOE, hp=hp)}}


E._journal_damage(before, turn(100, "PIDGEOT used RAZOR WIND! / PIDGEOT made a whirlwind!"), "RAZOR_WIND")
E._journal_damage(before, turn(60, "PIDGEOT used RAZOR WIND!"), "RAZOR_WIND")
for _ in range(2):
    E._journal_damage(before, turn(72, "PIDGEOT used WING ATTACK!"), "WING_ATTACK")
# WRAPPED: the turn goes by and PIDGEOT never uses its move; nothing is filed
E._journal_damage(before, turn(100, "Enemy BELLSPROUT's attack continues! / PIDGEOT can't move!"), "WING_ATTACK")
ck("a turn the move was never used (wrapped) is not filed, and each use is filed per member, the charging turn as 0",
   bp.MOVE_SEEN.get("RAZOR_WIND|PIDGEOT") == [2, 0.4, 1], bp.MOVE_SEEN)
ck("...and the steady hit as what it took",
   bp.MOVE_SEEN.get("WING_ATTACK|PIDGEOT") == [2, 0.56, 2], bp.MOVE_SEEN)
r = bp.choose(battle(ME, FOE), spec, {"turn": 1, "intent": "traversal"})
ck("the move that takes more per turn is the pick", r.get("index") == 2, r)

# a 0x hit says nothing about the move; a turn spent asleep is not the move's
n0 = dict(bp.MOVE_SEEN)
GHOST = dict(FOE, species="GASTLY", types=["GHOST", "POISON"])
E._journal_damage({"me": ME, "foe": GHOST, "_text_seq": 0}, dict(turn(100, "PIDGEOT used RAZOR WIND! / It doesn't affect enemy GASTLY!"), battle={"me": ME, "foe": GHOST}), "RAZOR_WIND")
E._journal_damage({"me": dict(ME, status="SLP"), "foe": FOE, "_text_seq": 0},
                  turn(100, "PIDGEOT used WING ATTACK!"), "WING_ATTACK")
ck("a 0x hit and an asleep turn are not filed", bp.MOVE_SEEN == n0, bp.MOVE_SEEN)
# a member that fainted before its move landed is not the move's either
E._journal_damage(before, dict(turn(100, "PIDGEOT used WING ATTACK!"), battle={"me": dict(ME, hp=0), "foe": FOE}), "WING_ATTACK")
ck("...nor a turn it fainted in", bp.MOVE_SEEN == n0, bp.MOVE_SEEN)

ck("the hit rate is what landed", abs(bp.seen_hit_rate("RAZOR_WIND", "PIDGEOT") - 2 / 3) < 1e-9)
ck("the scorer reads no table power",
   bp.score_move(dict(ME["moves"][1], power=999), ME, FOE, spec)["score"]
   == bp.score_move(ME["moves"][1], ME, FOE, spec)["score"])
ck("...nor table accuracy",
   bp.score_move(dict(ME["moves"][1], accuracy=10), ME, FOE, spec)["score"]
   == bp.score_move(ME["moves"][1], ME, FOE, spec)["score"])
ck("a status move is still told from an attack",
   not bp.damaging({"id": "SAND_ATTACK", "power": 0}) and bp.damaging(ME["moves"][0]))

# A FEW USES ARE NOT A VERDICT (run 55: THUNDERBOLT, one use at 0, never tried
# again under SWIFT's twenty-nine): a barely tried move gets room to be wrong.
bp.MOVE_SEEN.clear()
PK = {"species": "PIKACHU", "types": ["ELECTRIC"],
      "moves": [{"id": "THUNDERBOLT", "type": "ELECTRIC", "power": 95},
                {"id": "SWIFT", "type": "NORMAL", "power": 60}]}
for _ in range(29):
    bp.note_move_use("SWIFT", "PIKACHU", 1.0, 1.0, 0.33)
bp.note_move_use("THUNDERBOLT", "PIKACHU", 1.0, 1.0, 0.0)
ck("one unlucky use does not bury a move under one with a long record",
   bp.move_strength(PK["moves"][0], PK) > bp.move_strength(PK["moves"][1], PK))
for _ in range(6):
    bp.note_move_use("THUNDERBOLT", "PIKACHU", 1.0, 1.0, 0.05)
ck("...but a move seen to hit weakly again and again stays under it",
   bp.move_strength(PK["moves"][0], PK) < bp.move_strength(PK["moves"][1], PK))
# A KNOCKOUT IS NOT FILED AS STRENGTH: it shows only what the foe had left
bp.MOVE_SEEN.clear()
ko_before = {"me": ME, "foe": dict(FOE, hp=5), "_text_seq": 0}
E._journal_damage(ko_before, {"mode": "overworld", "battle_text": "PIDGEOT used WING ATTACK!",
                              "battle_text_seq": 1, "party": [dict(ME, exp=10)]},
                  "WING_ATTACK", exp_before=0)
ck("a knockout hit is not filed as the move's strength", bp.MOVE_SEEN == {}, bp.MOVE_SEEN)

# kept with the run's memory
src = (ROOT / "planner/executor.py").read_text()
ck("the record is saved and loaded with explored.json",
   '"move_seen": battle_policy.MOVE_SEEN' in src
   and 'battle_policy.MOVE_SEEN.update(data.get("move_seen") or {})' in src)
bp.MOVE_SEEN.clear()

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all ok'}")
sys.exit(1 if fails else 0)

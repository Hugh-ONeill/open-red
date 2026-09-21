#!/usr/bin/env python3
"""A setup rule can be counted per foe, can see what the foe already
carries, and can be kept for a foe or a fight worth the turn.

Run 29's BULBASAUR (L12: TACKLE, GROWL, LEECH_SEED) met BROCK with no rule
naming LEECH_SEED, so it was never used: a 0-power move scores 0 and is
never picked while a damaging move has PP. It lost to an ONIX its TACKLE
could not dent and won the rematch (user, 2026-09-21: "its preventing good
ol bulba from leeching and winning first thing without a rematch"; and on
2026-09-20: "it doesnt price in status effects or anything gained from a
non-damaging move ... sleep is a deadly status in gen1").

A rule naming it would still have failed the ace. max_uses and first_turns
were counted from the start of the BATTLE, so the seed went on GEODUDE and
ONIX came out after the window had shut. And the rule could not see the
foe at all: not its status box, not "was seeded!", not its level, not whose
fight it was.

Pinned: per_foe counts uses and turns from when each foe comes out; without
it the old behaviour stands; only_if_foe_clear reads the status box for a
sleep/poison/paralysis move, the seed for LEECH_SEED and confusion for a
confusing move, and never how many confused turns are left; with it a
second use is a retry after a miss; min_foe_level_ratio and only_if_leader
hold the turn back; the same species sent out twice is two foes; the words
validate, and bad values are refused; the author's document says them and
names no move worth using. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


MOVES = [
    {"index": 1, "id": "TACKLE", "pp": 35, "type": "NORMAL", "power": 35,
     "accuracy": 95, "effect": "NO_ADDITIONAL_EFFECT", "category": "physical"},
    {"index": 2, "id": "GROWL", "pp": 40, "type": "NORMAL", "power": 0,
     "accuracy": 100, "effect": "ATTACK_DOWN1_EFFECT", "category": "physical"},
    {"index": 3, "id": "LEECH_SEED", "pp": 10, "type": "GRASS", "power": 0,
     "accuracy": 90, "effect": "LEECH_SEED_EFFECT", "category": "special"},
    {"index": 4, "id": "SLEEP_POWDER", "pp": 15, "type": "GRASS", "power": 0,
     "accuracy": 75, "effect": "SLEEP_EFFECT", "category": "special"},
]


def obs(foe, level=10, hp=30, maxhp=30, leader=True, kind="trainer", **foe_kw):
    return {"battle": {
        "kind": kind, "leader": leader,
        "me": {"species": "BULBASAUR", "level": 12, "hp": 35, "maxhp": 35,
               "types": ["GRASS", "POISON"], "moves": MOVES, "slot": 1},
        "foe": dict({"species": foe, "level": level, "hp": hp, "maxhp": maxhp,
                     "types": ["ROCK", "GROUND"]}, **foe_kw)},
        "party": [{"species": "BULBASAUR", "level": 12, "hp": 35,
                   "max_hp": 35}]}


def spec(**rule):
    r = dict({"move": "LEECH_SEED", "max_uses": 1, "first_turns": 2,
              "min_hp_frac": 0.0, "vs": "any"}, **rule)
    return dict(B.DEFAULT_SPEC, setup=[r], avoid_status_moves=False)


def play(sp, script):
    """script: [(obs, ...)] one per turn -> the move chosen each turn."""
    ctx, out = {"turn": 0, "used": {}, "intent": "fight"}, []
    for t, o in enumerate(script, 1):
        ctx["turn"] = t
        d = B.choose(o, sp, ctx)
        m = next((x["id"] for x in MOVES if x["index"] == d.get("index")), d.get("op"))
        out.append(m)
    return out


BROCK = ([obs("GEODUDE", 12)] * 3
         + [obs("ONIX", 14, 40, 40)]
         + [obs("ONIX", 14, 38, 40, leechSeeded=True)] * 2)

got = play(spec(), BROCK)
ck("counted per battle, the seed goes on the first foe and never the ace",
   got[0] == "LEECH_SEED" and "LEECH_SEED" not in got[1:], got)
got = play(spec(per_foe=True), BROCK)
ck("counted per foe, the ace is seeded on the turn it comes out",
   got[0] == "LEECH_SEED" and got[3] == "LEECH_SEED", got)
ck("...once each, and the rest of the turns are the ordinary pick",
   got.count("LEECH_SEED") == 2 and got[1] == got[2] == got[4] == "TACKLE", got)

MISS = [obs("ONIX", 14, 40, 40)] * 3
got = play(spec(per_foe=True, max_uses=2, first_turns=3,
                only_if_foe_clear=True), MISS)
ck("with the foe still clear, a second use is the retry after a miss",
   got[:2] == ["LEECH_SEED", "LEECH_SEED"] and got[2] == "TACKLE", got)
LANDED = [obs("ONIX", 14, 40, 40), obs("ONIX", 14, 38, 40, leechSeeded=True),
          obs("ONIX", 14, 35, 40, leechSeeded=True)]
got = play(spec(per_foe=True, max_uses=2, first_turns=3,
                only_if_foe_clear=True), LANDED)
ck("...and once it has landed the turn is not spent on it again",
   got == ["LEECH_SEED", "TACKLE", "TACKLE"], got)

SLP = spec(move="SLEEP_POWDER", per_foe=True, max_uses=3, first_turns=8,
           only_if_foe_clear=True)
got = play(SLP, [obs("ONIX", 14, 40, 40), obs("ONIX", 14, 40, 40, status="SLP"),
                 obs("ONIX", 14, 30, 40, status="SLP"), obs("ONIX", 14, 20, 40)])
ck("a sleep is held while the status box is full and used again when it empties",
   got == ["SLEEP_POWDER", "TACKLE", "TACKLE", "SLEEP_POWDER"], got)
ck("a box that holds PAR stops a sleep too: the game takes one status",
   play(SLP, [obs("ONIX", 14, 40, 40, status="PAR")]) == ["TACKLE"])
ck("...but a seed does not care what is in the box",
   play(spec(per_foe=True, only_if_foe_clear=True),
        [obs("ONIX", 14, 40, 40, status="PAR")]) == ["LEECH_SEED"])

ck("what a foe carries is read as present or absent",
   B.foe_carries({"effect": "CONFUSION_EFFECT", "power": 0}, {"confusedTurns": 3})
   and not B.foe_carries({"effect": "CONFUSION_EFFECT", "power": 0}, {}))
ck("...a damaging move is never already done",
   not B.foe_carries({"effect": "POISON_SIDE_EFFECT1", "power": 15},
                     {"status": "PSN"}))
ck("...nor a move that lowers a stat",
   not B.foe_carries({"effect": "ATTACK_DOWN1_EFFECT", "power": 0},
                     {"status": "SLP", "leechSeeded": True}))
_src = (ROOT / "planner/battle_policy.py").read_text()
ck("how many confused turns are left is never compared with anything",
   _src.count("confusedTurns") == 1
   and '.get("confusedTurns") is not None' in _src)

ck("a foe far below the party is not worth the turn",
   play(spec(per_foe=True, min_foe_level_ratio=0.9), [obs("GEODUDE", 7)])
   == ["TACKLE"]
   and play(spec(per_foe=True, min_foe_level_ratio=0.9), [obs("GEODUDE", 11)])
   == ["LEECH_SEED"])
ck("a rule kept for a leader waits for one",
   play(spec(per_foe=True, only_if_leader=True),
        [obs("GEODUDE", 12, leader=False)]) == ["TACKLE"]
   and play(spec(per_foe=True, only_if_leader=True), [obs("GEODUDE", 12)])
   == ["LEECH_SEED"])

TWINS = [obs("GEODUDE", 12, 30, 30), obs("GEODUDE", 12, 9, 30, leechSeeded=True),
         obs("GEODUDE", 12, 30, 30), obs("GEODUDE", 12, 28, 30, leechSeeded=True)]
got = play(spec(per_foe=True), TWINS)
ck("the same species sent out twice is two foes",
   got == ["LEECH_SEED", "TACKLE", "LEECH_SEED", "TACKLE"], got)
POTION = [obs("ONIX", 14, 40, 40), obs("ONIX", 14, 12, 40, leechSeeded=True),
          obs("ONIX", 14, 32, 40, leechSeeded=True)]
ck("...but a foe healed by its trainer is the foe it was",
   play(spec(per_foe=True, first_turns=1), POTION)
   == ["LEECH_SEED", "TACKLE", "TACKLE"])

ck("the words validate",
   B.validate_spec(spec(per_foe=True, only_if_foe_clear=True,
                        only_if_leader=False, min_foe_level_ratio=0.8)) == [])
_bad = B.validate_spec(spec(per_foe="yes", only_if_foe_clear=1,
                            min_foe_level_ratio=9))
ck("...and values that are not what they say are refused",
   sum("per_foe" in p or "only_if_foe_clear" in p or "min_foe_level_ratio" in p
       for p in _bad) == 3, _bad)

import policy_author as PA  # noqa: E402
D = " ".join(PA.DSL_DOC.split())
ck("the author is told every word",
   all(w in D for w in ('"per_foe": true/false', '"only_if_foe_clear": true/false',
                        '"min_foe_level_ratio": 0.0-3.0',
                        '"only_if_leader": true/false')))
ck("...and that a move with no power is only ever used by a rule that names it",
   "NEVER PICKED BY SCORE" in D and "a rule here that NAMES it" in D)
_new = D[D.index("A MOVE WITH NO POWER"):D.index("switch: list of mid-battle")]
ck("...without being told which move is worth a turn",
   not any(w in _new.upper() for w in ("LEECH", "SLEEP_POWDER", "HYPNOSIS",
                                       "THUNDER_WAVE", "DEADLY", "STRONGEST")),
   _new[:200])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

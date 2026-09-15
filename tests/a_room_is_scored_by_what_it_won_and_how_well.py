"""A room's score is what it WON, plus a bonus worth less than one fight.

THE OBJECTIVE WAS THE ONLY THING THAT COUNTED, and most rooms are swept by
any competent spec. Four candidates tied 32/32 at Celadon across three
separate runs while one left 1831 damage on the table and another 3299,
and the sum could not tell them apart (user, 2026-09-15: "is there a way
we can incorporate the tiebreak values into the total score? like bonuses
for the top scorers if they all tied").

The bonus reads the two things the arena knows about HOW a room was taken:
the party still standing at the end, and agreement with the move oracle,
which is the only per-turn measure of play it has. It is bounded by one
fight in that room, so:

    winning one more fight ALWAYS beats playing the same fights better,

and two specs that won exactly the same fights are ordered by what they
had left. A bonus that could outrank a room would be a different metric
wearing this one's clothes.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import policy_author as A                                  # noqa: E402

checks = []
def ck(name, cond): checks.append((name, bool(cond)))


def room(beaten, standing=8, trials=4, bodies=0.0, agree=0, scored=1,
         blackouts=0):
    return dict(arena="gym", beaten=beaten, standing=standing,
                gauntlet_trials=trials, blackouts=blackouts, bodies=bodies,
                agree=agree, scored=scored, dmg_gap=0.0, rival_trials=0,
                rival_wins=0, pewter=0, badge=0, gauntlet_detail=[])


SWEPT_WELL = room(32, bodies=3.2, agree=222, scored=271)
SWEPT_BADLY = room(32, bodies=1.0, agree=100, scored=271)
ONE_SHORT_PERFECT = room(31, bodies=4.0, agree=271, scored=271)

ck("two sweeps score the same on the objective alone",
   A.arena_fraction(SWEPT_WELL) == A.arena_fraction(SWEPT_BADLY) == 1.0)
ck("...and are told apart once quality counts",
   A.arena_points(SWEPT_WELL) > A.arena_points(SWEPT_BADLY))
ck("an extra fight beats better play, always",
   A.arena_points(SWEPT_BADLY) > A.arena_points(ONE_SHORT_PERFECT))
ck("the bonus never reaches one fight's worth",
   A.arena_points(SWEPT_WELL) - A.arena_fraction(SWEPT_WELL) < 1 / 32)
ck("a room won with nobody left and no agreement gets no bonus",
   A.arena_points(room(32)) == A.arena_fraction(room(32)))
ck("quality stays inside [0,1)",
   0.0 <= A.arena_quality(SWEPT_WELL) < 1.0
   and A.arena_quality(room(0)) == 0.0)

# ---- it applies to the league too, which counts rooms not fights ------
E4 = dict(arena="e4", rooms=16, gauntlet_trials=4, blackouts=0, bodies=4.0,
          agree=242, scored=307, dmg_gap=0.0, rival_trials=0, rival_wins=0,
          pewter=0, badge=0, gauntlet_detail=[])
ck("the league is scored the same way",
   A.arena_fraction(E4) == 0.8 and A.arena_points(E4) > 0.8)
ck("...and its bonus is under one room of five",
   A.arena_points(E4) - A.arena_fraction(E4) < 1 / 20)

# ---- and the total is the sum of those, not of bare fractions --------
PA = (ROOT / "planner" / "policy_author.py").read_text()
ck("cross_key sums the points, not the fractions",
   "sum(arena_points(r) for _, r in rows)" in PA)
ck("a tie on the objective is broken inside the total",
   A.cross_key([("a", SWEPT_WELL)]) > A.cross_key([("a", SWEPT_BADLY)]))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

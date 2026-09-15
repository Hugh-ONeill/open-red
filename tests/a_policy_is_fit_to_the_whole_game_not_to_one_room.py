"""A spec is judged by every arena it will have to play, and they add up.

Each arena measures its own thing: rooms cleared, trainers beaten, a badge
at the end of a walk, six rival fights. Ranked on one tuple, any gauntlet
spec beats any Brock spec for free, which is why pick_policy split them by
stage and drew a line at eight badges. The line is a workaround. Run 17
crossed no line at all — three badges is the Brock side — and played v1's
`POTION below 30%` into Erika with three SUPER_POTIONs in the bag
(2026-09-15, user: "it didnt use the three super potions").

The design the user asked for is ONE POLICY ACROSS STAGES (2026-08-24:
"not one per stage ... score a candidate as the SUM across arenas ... so
one spec is fit to the whole game"). Each arena's result becomes the
FRACTION of that arena's own objective the spec reached, and fractions
add. A spec that sweeps the league by dying fast everywhere else cannot
hide behind a number only the league produces.

What stays the model's: the spec. The arenas only say what happened.
"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import policy_author as A                                  # noqa: E402
import pick_policy as P                                    # noqa: E402

PA = (ROOT / "planner" / "policy_author.py").read_text()

checks = []
def ck(name, cond): checks.append((name, bool(cond)))


# every arena fills the same dict; the keys its own measure does not use
# stay zero, which is exactly how the real results come back
BLANK = {"rival_wins": 0, "rival_trials": 0, "pewter": 0, "badge": 0,
         "gauntlet_trials": 0, "blackouts": 0, "agree": 0, "scored": 0,
         "dmg_gap": 0.0, "rival_detail": [], "gauntlet_detail": []}


def gymr(beaten, standing=8, trials=2, blackouts=0):
    return dict(BLANK, arena="gym", beaten=beaten, standing=standing,
                gauntlet_trials=trials, blackouts=blackouts)


def e4r(rooms, trials=3, blackouts=0):
    return dict(BLANK, arena="e4", rooms=rooms, gauntlet_trials=trials,
                blackouts=blackouts)


def brockr(badge, rival, trials=3, rtrials=6, blackouts=0):
    return dict(BLANK, arena="brock", badge=badge, rival_wins=rival,
                rival_trials=rtrials, gauntlet_trials=trials,
                blackouts=blackouts)


# ---- each arena reports a fraction of its OWN objective ----------------
ck("a swept gym room is the whole of that arena",
   A.arena_fraction(gymr(16)) == 1.0)
ck("half the room is half of it", A.arena_fraction(gymr(8)) == 0.5)
ck("eight of fifteen league rooms is just over half",
   0.53 < A.arena_fraction(e4r(8)) < 0.54)
ck("the Brock arena weighs the badge and the rival the same",
   A.arena_fraction(brockr(3, 6)) == 1.0
   and A.arena_fraction(brockr(3, 0)) == 0.5)
ck("an older result with no arena recorded still reads",
   A.arena_fraction({k: v for k, v in e4r(15).items()
                     if k != "arena"}) == 1.0)

# ---- and the fractions add --------------------------------------------
SWEEPER = [("brock", brockr(0, 0)), ("erika", gymr(0)), ("e4", e4r(15))]
STEADY = [("brock", brockr(3, 6)), ("erika", gymr(12)), ("e4", e4r(6))]
ck("a league sweeper that dies everywhere else scores 1.00 of 3",
   abs(A.cross_key(SWEEPER)[0] - 1.0) < 1e-6)
ck("a spec that holds up in all three beats it",
   A.cross_key(STEADY) > A.cross_key(SWEEPER))
ck("...and could not have, on the one number the league produces",
   A.rank_key(dict(e4r(15))) > A.rank_key(dict(e4r(6))))
ck("blackouts break a tie between equal totals",
   A.cross_key([("erika", gymr(8))])
   > A.cross_key([("erika", gymr(8, blackouts=2))]))
ck("the report says the total out of the arenas that produced it",
   "of 3.00" in A.cross_text("x", STEADY)
   and "erika: 75% of that arena" in A.cross_text("x", STEADY))

# ---- the arenas are the ones the README built -------------------------
ck("all four arenas are named", set(A.ARENAS) == {"brock", "erika", "koga",
                                                  "e4"})
ck("brock is the one that replays a plan, the rest are savepoints",
   A.ARENAS["brock"][1] is None
   and all(v[1] is not None for k, v in A.ARENAS.items() if k != "brock"))
ck("every savepoint arena is a save that exists on disk",
   all(v[1].exists() for k, v in A.ARENAS.items() if v[1]))
ck("a gym room is scored by the flags that flipped, not by sprites",
   "_beaten(obs)" in (ROOT / "planner" / "policy_author.py").read_text()
   and 'startswith("EVENT_BEAT_")' in
   (ROOT / "planner" / "policy_author.py").read_text())

# ---- who is in the room, and what a win in it is worth ----------------
ROSTER = A.room_roster("CELADON_GYM")
ck("the room's roster comes from the engine's own map table",
   len(ROSTER) == 8 and ("CELADONGYM_ERIKA", 4, 3) in ROSTER)
ck("...and not from the observation, which a restored save has none of",
   "room_roster(self.arena_map)" in PA)
ORDER = [n for n, _x, _y in sorted(ROSTER, key=lambda t: -t[2])]
ck("the trainer nearest the door is pressed first",
   ORDER[0] == "CELADONGYM_COOLTRAINER_F1")
ck("...and the leader is in the last row, behind all seven",
   ORDER.index("CELADONGYM_ERIKA") >= 4
   and min(y for n, _x, y in ROSTER) == 3)
ck("a bed with a bush in it is cut, not treated as a wall",
   'move="CUT"' in PA and 'o.get("kind") != "cut_tree"' in PA)
ck("bodies left break a tie the objective cannot see",
   A.cross_key([("erika", dict(gymr(16), bodies=1.6))])
   > A.cross_key([("erika", dict(gymr(16), bodies=0.8))]))
ck("...but never outrank the objective itself",
   A.cross_key([("erika", dict(gymr(16), bodies=0.0))])
   > A.cross_key([("erika", dict(gymr(8), bodies=2.0))]))
ck("a blackout leaves nobody standing in the arena it left",
   "0.0 if end != self.arena_map" in PA)

# ---- the picker takes the spec fit to the whole game ------------------
def spec_file(d: Path, name: str, ev: dict) -> Path:
    f = d / name
    f.write_text(json.dumps({"name": name, "provenance": {"eval": ev}}))
    return f


with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    early = spec_file(d, "policy_model_v1.json",
                      dict(brockr(3, 6), arena="brock"))
    league = spec_file(d, "policy_model_v3.json", dict(e4r(8), arena="e4"))
    whole = spec_file(d, "policy_model_v7.json",
                      dict(brockr(3, 6), arena="brock+erika+e4",
                           arenas={"brock": brockr(3, 6), "erika": gymr(12),
                                   "e4": e4r(6)},
                           cross_total=A.cross_key(STEADY)[0]))
    paths = [early, league, whole]
    ck("a cross-arena spec wins at three badges, where the line said Brock",
       P.rank(paths, badges=3)[0] == whole)
    ck("...and at eight, where the line said the league",
       P.rank(paths, badges=8)[0] == whole)
    ck("...and with no badges asked at all",
       P.rank(paths, badges=None)[0] == whole)
    ck("the stage line still decides when nothing was fit across",
       P.rank([early, league], badges=3)[0] == early
       and P.rank([early, league], badges=8)[0] == league)
    ck("a cross-arena spec that blacked out every trial is still refused",
       P.failed_its_own_trial(
           dict(e4r(0, trials=3, blackouts=3), arena="brock+e4",
                arenas={"e4": e4r(0)}, cross_total=0.0)) != "")
    ck("one arena is not 'across' anything",
       not P.fit_across({"arenas": {"e4": e4r(8)}}))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

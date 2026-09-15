"""The ledger is written continuously and the save is not.

Kill the executor between one save and the next — stop_all has SIGKILLed it
on every stop this week, the executor never answering inside its 90 seconds
— and the game reloads a world that is BEHIND its own ledger. Nothing put
the two back in step.

Run 17 walked into the Game Corner and the page told it, in the block of
what people have said:

    POSTER: Hey! A switch behind the poster!? Let's push it!

It had never touched the poster in this world. The Rocket who guards it was
still standing in front of it, unfought. Thirteen minutes of play had been
written to the ledger and lost from the save. The model reasoned correctly
from a page that lied, concluded the switch was thrown, and spent its
rounds pressing slot machines looking for a staircase nothing had opened
(user, 2026-09-15: "it has not interacted with the poster yet, the rocket
is still in front of it"). Wrong FACTS are the model's; a page that
licensed one is ours.

Event flags in gen 1 only ever go UP within one world, so a flag count that
has gone DOWN is not an event — it is an earlier world. Records made at a
count this world has not reached are records of a future thrown away.

What is NOT dropped: everything recorded at or below the count this world
actually holds. A rollback is not a reason to forget the run.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                       # noqa: E402

checks = []
def ck(name, cond): checks.append((name, bool(cond)))

REG = "GAME_CORNER|8,5"
LINE = "Hey! A switch behind the poster!? Let's push it!"
KEY = "map:ROCKET_HIDEOUT_B1F|GAME_CORNER|8,5"


def rig(flags_now):
    """An executor carrying the real ledger run 17 was handed, and an
    observation from the world that actually loaded."""
    ex = E.Executor.__new__(E.Executor)
    ex._touch_mark = {REG: {"POSTER": {"then": [4, 121, 14], "n": 1,
                                       "at": [4, 120, 14]},
                            "GAMECORNER_CLERK1": {"then": [4, 118, 14],
                                                  "n": 1, "at": None}}}
    ex.hints_at = {REG: {f"POSTER: {LINE}": {"flags": 121, "keys": []},
                         "GAMECORNER_MIDDLE_AGED_MAN1: run by TEAM ROCKET.":
                             {"flags": 117, "keys": []}}}
    ex._outcomes = {KEY: {"POSTER": {"n": 1, "kind": "fixture",
                                     "last": f'ok (moved) — it said: "{LINE}"'},
                          "GAMECORNER_CLERK1": {"n": 1, "kind": "npc"}}}
    ex._tried_objs = {REG: {"POSTER", "GAMECORNER_CLERK1"}}
    ex._logged = []
    ex.log = lambda kind, **kw: ex._logged.append((kind, kw))
    obs = {"flags": ["f%d" % i for i in range(flags_now)],
           "badges": [1, 2, 3, 4], "bag": {}}
    return ex, obs


# ---- the world that loaded is one flag behind the one in the ledger ----
ex, obs = rig(120)
ex._drop_what_a_thrown_away_world_did(obs)
ck("the press that happened in the thrown-away world is gone",
   "POSTER" not in ex._touch_mark[REG])
ck("...and so is the line the page quoted from it",
   f"POSTER: {LINE}" not in ex.hints_at[REG])
ck("...and the outcome the same press wrote, which carries no mark",
   "POSTER" not in ex._outcomes[KEY])
ck("...and the poster is a thing to press again, not one already pressed",
   "POSTER" not in ex._tried_objs[REG])
ck("the drop is said out loud, with the count that proved it",
   any(k == "world_rolled_back" and kw.get("flags_now") == 120
       and kw.get("presses") == 1 and kw.get("hints") == 1
       for k, kw in ex._logged))

# ---- and the run is not forgotten along with it ------------------------
ck("a press from this world's own past is kept",
   "GAMECORNER_CLERK1" in ex._touch_mark[REG]
   and "GAMECORNER_CLERK1" in ex._outcomes[KEY]
   and "GAMECORNER_CLERK1" in ex._tried_objs[REG])
ck("...and so is what a man in the corner actually said",
   "GAMECORNER_MIDDLE_AGED_MAN1: run by TEAM ROCKET." in ex.hints_at[REG])

# ---- a world that is level with its ledger loses nothing ---------------
ex2, obs2 = rig(121)
ex2._drop_what_a_thrown_away_world_did(obs2)
ck("nothing is dropped when the world is level with the ledger",
   "POSTER" in ex2._touch_mark[REG] and len(ex2.hints_at[REG]) == 2
   and not ex2._logged)
ex3, obs3 = rig(200)
ex3._drop_what_a_thrown_away_world_did(obs3)
ck("...nor when the world has run far ahead of it",
   "POSTER" in ex3._touch_mark[REG] and not ex3._logged)

# ---- and no claim is made without the evidence to make it --------------
ex4, obs4 = rig(0)
ex4._drop_what_a_thrown_away_world_did(obs4)
ck("an observation with no flag list drops nothing at all",
   "POSTER" in ex4._touch_mark[REG] and not ex4._logged)
ex5, obs5 = rig(120)
ex5._drop_what_a_thrown_away_world_did(obs5)
n_after_first = len(ex5._logged)
ex5._drop_what_a_thrown_away_world_did(obs5)
ck("the check runs once per process, not once a round",
   len(ex5._logged) == n_after_first)

# ---- it is wired into the per-round note, where the mark is taken ------
SRC = (ROOT / "planner" / "executor.py").read_text()
ck("the detector runs where the world mark is read each round",
   "self._mark_now = self._world_mark(obs)\n"
   "        self._drop_what_a_thrown_away_world_did(obs)" in SRC)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

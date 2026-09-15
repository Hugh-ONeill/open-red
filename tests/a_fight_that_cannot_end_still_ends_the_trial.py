"""A battle the policy cannot finish must not eat the whole sweep.

Gen 1 holds positions nothing can resolve. AGATHA's GENGAR against a
VAPOREON whose four moves were every one of them at 0 PP is one: Struggle
is Normal, Normal does nothing at all to a Ghost, and the enemy stopped
taking turns. Neither side took a point off the other for fifty minutes
while the eight gym rooms behind it had each finished in two, foe HP
frozen at 74/151 and the turn counter past 19000 (2026-09-15). The ride
loop was `while mode == battle`, with nothing in it that could ever stop.

A fight that has stopped changing is over, whoever the scoreboard says
won. Give up on it and hand the caller an observation with no map in it,
which every caller already reads as "stopped here" — the score a policy
that cannot finish its fight has earned.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "planner"))
import policy_author as P

checks = []


def ck(name, ok):
    checks.append((name, bool(ok)))
    print(("  ok   " if ok else "  FAIL ") + name)


def obs_at(foe_hp, my_hp, enemy=1, party=(100,)):
    return {"mode": "battle", "party": [{"hp": h} for h in party],
            "battle": {"enemyIndex": enemy, "partyIndex": 0,
                       "foe": {"hp": foe_hp,
                               "moves": [{"pp": 10}, {"pp": 10}]},
                       "me": {"hp": my_hp}}}


class Ex:
    """A fight that plays out however the script says."""

    def __init__(self, script):
        self.script = list(script)
        self.turns = 0

    def handle_battle(self, sg, obs):
        self.turns += 1
        return obs

    def settle(self):
        return self.script.pop(0) if self.script else self.script_last

    script_last = None


class Stub:
    """Only the two things _ride reaches for."""
    _battle_mark = staticmethod(P.Gym._battle_mark)


def ride(script, **kw):
    g = Stub()
    g.ex = Ex(script[1:])
    g.ex.script_last = script[-1]
    out = P.Gym._ride(g, script[0], **kw)
    return out, g.ex.turns


# ---- a fight that ends still ends ------------------------------------------
won = [obs_at(50, 80), obs_at(20, 80), obs_at(0, 80), {"mode": "overworld",
                                                       "map": {"id": "GYM"}}]
out, turns = ride(won)
ck("a fight that resolves is ridden to the overworld",
   out.get("mode") == "overworld" and out.get("map", {}).get("id") == "GYM")
ck("...and costs only the turns it took", turns == 3)

# ---- a frozen fight is given up on -----------------------------------------
stuck = [obs_at(74, 12) for _ in range(500)]
out, turns = ride(stuck, still=50)
ck("a fight that stops changing is given up on", turns < 60)
ck("...and the observation handed back is still the battle",
   out.get("mode") == "battle")
ck("...which carries no map, so the caller scores it as stopped here",
   out.get("map") is None)

# ---- slow but real progress is not mistaken for a stall --------------------
slow = []
for i in range(120):
    slow.append(obs_at(200 - i, 90))          # one point of damage a turn
slow.append({"mode": "overworld", "map": {"id": "GYM"}})
out, turns = ride(slow, still=50)
ck("a long fight that is still moving is not cut short",
   out.get("mode") == "overworld" and turns == 120)

# ---- what counts as movement ------------------------------------------------
m = P.Gym._battle_mark
ck("a foe losing HP counts", m(obs_at(74, 12)) != m(obs_at(70, 12)))
ck("taking damage counts", m(obs_at(74, 12)) != m(obs_at(74, 8)))
ck("the next enemy coming out counts",
   m(obs_at(74, 12, enemy=1)) != m(obs_at(74, 12, enemy=2)))
ck("a party member falling counts",
   m(obs_at(74, 12, party=(100, 30))) != m(obs_at(74, 12, party=(100, 0))))
ck("the foe spending PP counts",
   m(obs_at(74, 12)) != m({"mode": "battle", "party": [{"hp": 100}],
                           "battle": {"enemyIndex": 1, "partyIndex": 0,
                                      "foe": {"hp": 74,
                                              "moves": [{"pp": 9},
                                                        {"pp": 10}]},
                                      "me": {"hp": 12}}}))
ck("nothing moving does not count", m(obs_at(74, 12)) == m(obs_at(74, 12)))

# ---- the outer bound --------------------------------------------------------
churn = [obs_at(74 + (i % 7), 12 + (i % 5)) for i in range(2000)]
out, turns = ride(churn, cap=400, still=50)
ck("a fight that churns forever still stops at the cap", turns <= 400)
ck("...and it is not an exception, it is a score",
   out.get("mode") == "battle")

bad = [n for n, ok in checks if not ok]
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

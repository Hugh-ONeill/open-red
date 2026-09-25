#!/usr/bin/env python3
"""A catch weakens with a hit whose bite on that species' bar it has seen,
and throws at once at a species it has seen leave.

Run of record 4, 2026-09-25: every ball went at a wild at full HP — three
at a PIDGEY, two at a GEODUDE the model had said "Ivysaur can easily
weaken" — because weakening needed a damage seen at our EXACT level, which
one level-up silences (and the record did not outlive an attempt). Its
twenty-one ABRA were also filed as knocked out by whatever move was
pressed, since a teleport ends a battle the way a faint does (user: "fix
the full-HP throwing too, as long as that wont prevent abra").

Pinned: a hit is kept as the fraction of the bar it took and the level
gap it took it at; a battle our move ended is a faint only if experience
came, and then it is 1.0; a wild that ends a battle with no ball, no flee
and no experience is recorded as having left, on its turn; a catch against
a species seen to leave by this turn throws; the fraction seen at a gap at
least as wide as now bounds a hit from above and lets it weaken; one seen
at a narrower gap, or a knockout, does not; both records ride in the
executor's memory. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E        # noqa: E402
import battle_policy as bp  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def mon(sp, lv, hp, mx, types, moves=None):
    return {"species": sp, "level": lv, "hp": hp, "maxhp": mx, "types": types,
            "status": None, "moves": moves or []}


TACKLE = {"index": 1, "id": "TACKLE", "type": "NORMAL", "power": 35, "accuracy": 95, "pp": 30}
VINE = {"index": 2, "id": "VINE_WHIP", "type": "GRASS", "power": 35, "accuracy": 100, "pp": 10}
IVY = mon("IVYSAUR", 20, 60, 62, ["GRASS", "POISON"], [TACKLE, VINE])
PARTY = [{"species": "IVYSAUR", "level": 20, "hp": 60, "max_hp": 62, "exp": 5000}]

# ---------------------------------------------------------------- the records
E.DAMAGE_FRAC.clear(); E.DAMAGE_JOURNAL.clear()
before = {"kind": "wild", "me": IVY, "foe": mon("GEODUDE", 10, 30, 30, ["ROCK", "GROUND"])}
after = {"mode": "battle", "party": PARTY,
         "battle": {"foe": mon("GEODUDE", 10, 24, 30, ["ROCK", "GROUND"])}}
E._journal_damage(before, after, "TACKLE", exp_before=5000)
ck("a hit is kept as the fraction of the bar and the level gap",
   E.DAMAGE_FRAC.get("TACKLE|GEODUDE") == [[2.0, 0.2]], E.DAMAGE_FRAC)
E._journal_damage(before, {"mode": "overworld", "party": [dict(PARTY[0], exp=5100)]},
                  "VINE_WHIP", exp_before=5000)
ck("a battle our move ended with experience is a faint, filed as 1.0",
   E.DAMAGE_FRAC.get("VINE_WHIP|GEODUDE") == [[2.0, 1.0]], E.DAMAGE_FRAC)
abra = {"kind": "wild", "me": IVY, "foe": mon("ABRA", 10, 25, 25, ["PSYCHIC"])}
E._journal_damage(abra, {"mode": "overworld", "party": PARTY}, "TACKLE", exp_before=5000)
ck("...with no experience it is not: nothing is filed for the ABRA that left",
   "TACKLE|ABRA" not in E.DAMAGE_FRAC
   and not any(k[1] == "ABRA" for k in E.DAMAGE_JOURNAL), (E.DAMAGE_FRAC, E.DAMAGE_JOURNAL))

# ------------------------------------------- the departure, off the battle loop
E.WILD_LEFT.clear()


class Bridge:
    def __init__(self):
        self.sent = []

    def send(self, op, **kw):
        self.sent.append(op)
        return {"mode": "overworld", "party": PARTY, "result": {"ok": True}}

    def obs(self):
        return None


start = {"mode": "battle", "bag": {}, "party": PARTY,
         "battle": dict(abra, partyIndex=0, enemyIndex=0)}
log = []
spec = dict(bp.DEFAULT_SPEC, name="t", battle_items=[], setup=[])
E._run_policy(spec, Bridge(), start, lambda k, **kw: log.append((k, kw)), 5,
              intent="fight")
ck("a wild that ends the battle with no ball, flee or experience has left, on its turn",
   E.WILD_LEFT.get("ABRA") == [1] and any(k == "wild_left" for k, _ in log),
   (E.WILD_LEFT, [k for k, _ in log]))

# --------------------------------------------------------------- the policy
CATCH = dict(spec, catch={"ball": "POKE_BALL", "throw_at_hp_frac": 0.3,
                          "max_balls": 5, "first_ball": False,
                          "probe_hit": {"min_level_ratio": 0.8}})


def pick(foe, frac=None, left=None, turn=1):
    bp.reset_run_budget()
    o = {"mode": "battle", "bag": {"POKE_BALL": 5}, "party": PARTY,
         "battle": {"kind": "wild", "partyIndex": 0, "enemyIndex": 0,
                    "me": IVY, "foe": foe}}
    return bp.choose(o, CATCH, {"turn": turn, "intent": "catch",
                                "want": {"species": [foe["species"]]},
                                "journal": {}, "frac_journal": frac or {},
                                "wild_left": left or {}})


GEO = mon("GEODUDE", 10, 30, 30, ["ROCK", "GROUND"])
r0 = pick(GEO)
ck("with nothing seen, the old way: a throw at full HP", r0.get("op") == "throw_ball", r0)
r1 = pick(GEO, frac={"TACKLE|GEODUDE": [[2.0, 0.2]]})
ck("a hit seen taking a fifth of its bar at a gap as wide as now weakens",
   r1.get("op") == "battle_move" and r1.get("index") == 1, r1)
r2 = pick(GEO, frac={"TACKLE|GEODUDE": [[1.5, 0.2]]})
ck("...but not one seen at a narrower gap: it bounds nothing now",
   r2.get("op") == "throw_ball", r2)
r3 = pick(GEO, frac={"VINE_WHIP|GEODUDE": [[2.5, 1.0]]})
ck("...nor a knockout", r3.get("op") == "throw_ball", r3)
AB = mon("ABRA", 10, 25, 25, ["PSYCHIC"])
r4 = pick(AB, frac={"TACKLE|ABRA": [[2.0, 0.1]]}, left={"ABRA": [1]})
ck("a species seen to leave on turn one gets a ball on turn one, weakening or not",
   r4.get("op") == "throw_ball" and "seen to leave" in str(r4.get("_why")), r4)
r5 = pick(AB, frac={"TACKLE|ABRA": [[2.0, 0.1]]})
ck("...never seen leaving, the spec decides as before", r5.get("op") == "battle_move", r5)

src = (ROOT / "planner/executor.py").read_text()
ck("both records ride in the run's memory",
   '"damage_frac": DAMAGE_FRAC, "wild_left": WILD_LEFT,' in src
   and 'DAMAGE_FRAC.update(data.get("damage_frac") or {})' in src
   and 'WILD_LEFT.update(data.get("wild_left") or {})' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

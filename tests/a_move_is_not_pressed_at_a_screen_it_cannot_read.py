#!/usr/bin/env python3
"""No move is pressed at a battle screen the harness cannot read, and the
blind press that remains says it is blind.

When the observation carries no battle sides the policy is handed an empty
move list, reads it as "nothing is legal" — true for DISABLE, which is the
case that branch was written for — and presses slot 1. Run 33: 52 moves
played with NO reason recorded, every one of them slot 1, and all 52 on an
observation with no battle state at all (own and foe HP both null), against
0 of 1,126 scored moves. Slot 1 on a GEODUDE past L21 is SELFDESTRUCT, and
one of those presses killed it at full HP in Surge's gym (user, 2026-09-22:
"it chose selfdestruct after just one dig", and on the PP being untouched,
"it cant be because of pp alone").

The screen is usually mid-something — the faint-and-replace prompt, an
animation frame, a two-turn move's underground turn — so the loop waits and
looks again before asking the policy at all, and leaves the battle alone if
it has ended meanwhile. The self-KO demotion could not have saved it: that
rule is in the SCORING path and this return skips it. A guard that lives on
the happy path is not a guard.

Pinned: the loop re-reads before asking; it gives up if the fight ended; it
journals whether the screen came back; the policy's own fallback now says
which case it is and prefers a slot the run has not watched faint its user;
and the DISABLE case it was written for still answers Struggle. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402

SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def decide(moves, dis=0, ko=None):
    obs = {"battle": {"kind": "wild", "me": {
        "species": "GEODUDE", "level": 22, "hp": 40, "maxhp": 40,
        "types": ["ROCK"], "moves": moves, "disabledSlot": dis},
        "foe": {"species": "X", "level": 10, "hp": 20, "maxhp": 20,
                "types": []}}, "party": [], "bag": {}}
    return B.choose(obs, dict(B.DEFAULT_SPEC), {"turn": 1, "self_ko": ko or {}})


d = decide([])
ck("a screen with no move list gets a press that admits it is blind",
   d["op"] == "battle_move" and "blind press" in d["_why"]
   and "could not be read" in d["_why"], d)
ck("...so it can never again be read as a policy decision",
   d.get("_why") is not None)

DRY = [{"index": 1, "id": "SELFDESTRUCT", "pp": 0, "power": 130,
        "type": "NORMAL", "accuracy": 100},
       {"index": 2, "id": "TACKLE", "pp": 0, "power": 35,
        "type": "NORMAL", "accuracy": 95},
       {"index": 3, "id": "GROWL", "pp": 0, "power": 0,
        "type": "NORMAL", "accuracy": 100}]
d = decide(DRY, dis=3, ko={"SELFDESTRUCT": 28})
ck("with everything dry and slot 3 disabled, it Struggles and says so",
   "Struggle" in d["_why"] and "disabled" in d["_why"], d)
ck("...and it does NOT open with the move it has watched faint its user",
   d["index"] == 2, d)
d = decide(DRY, dis=1, ko={})
ck("the DISABLE case it was written for still avoids the disabled slot",
   d["index"] == 2, d)
ck("...and with no alternative at all, the self-KO move is still played",
   decide(DRY[:1] + DRY[2:], dis=3,
          ko={"SELFDESTRUCT": 28})["index"] == 1)
d = decide([{"index": 1, "id": "SELFDESTRUCT", "pp": 0, "power": 130,
             "type": "NORMAL", "accuracy": 100}], ko={"SELFDESTRUCT": 28})
ck("...and when the only move left is that one, it is still played",
   d["index"] == 1, d)

ck("the loop looks again before it asks the policy anything",
   "DO NOT PRESS A MOVE AT A SCREEN YOU CANNOT READ" in SRC
   and 'if not (_sides.get("me") or {}).get("moves"):' in SRC
   and SRC.index('if not (_sides.get("me") or {}).get("moves"):')
   < SRC.index("op = battle_policy.choose(obs, spec, ctx)"))
ck("...a bounded number of times, with a wait between",
   "for _try in range(3):" in SRC and 'bridge.send("wait", frames=12)' in SRC)
ck("...and gives up on the turn if the fight ended while it looked",
   'if (obs or {}).get("mode") != "battle":\n                continue' in SRC)
ck("whether the screen came back is journalled",
   'log("battle_unreadable", turn=turns,' in SRC and "readable=bool(" in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d2 in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d2 else f"  {str(d2)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

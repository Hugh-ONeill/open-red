#!/usr/bin/env python3
"""The missing rung's reason checkers read what a sentence claims, not
every name in it.

Run 66, 2026-10-25, stuck at Sabrina's gym with SAFFRONCITY_ROCKET3 in the
door, the missing rung named "Defeat Giovanni" three ways and all three were
turned down. Two were misreads:

  "...only leave the Saffron Gym once the player has defeated the boss of
  Silph Co. and obtained the Master Ball" -> "your reason says you hold
  MASTER_BALL" (a condition, not a holding);
  "...block the entrance to the Saffron City Gym until..." -> "the way into
  SAFFRON_CITY is barred" (the name goes on: it is the gym).

Pinned: both pass; the cases each checker was written for still refuse.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

BAG = "BAG: CARD_KEY, LIFT_KEY, POKE_BALL x9"
w = ("The run has defeated the rival in Silph Co., but the Team Rocket members "
     "only leave the Saffron Gym once the player has defeated the boss of Silph "
     "Co. and obtained the Master Ball.")
ck("a holding said under 'once' is not a claim", A._premise_item_not_held(w, BAG) is None,
   A._premise_item_not_held(w, BAG))
for u in ("until you have obtained the Master Ball", "if the player has the Master Ball"):
    ck(f"...nor under {u.split()[0]!r}", A._premise_item_not_held(u, BAG) is None)
w2 = "The player has obtained the Silph Scope and reached the top of the tower"
ck("a plain claim of holding is still refused",
   A._premise_item_not_held(w2, BAG) == "SILPH_SCOPE", A._premise_item_not_held(w2, BAG))

d = Path(tempfile.mkdtemp(prefix="blocked_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps(
    {"visits": {"SAFFRON_CITY|12,0": 5, "ROCK_TUNNEL_1F|15,0": 2}}))
here = os.getcwd()
os.chdir(d)
try:
    g = ("The Team Rocket members block the entrance to the Saffron City Gym until "
         "the player defeats Giovanni at the top of Silph Co.")
    r = A._blocks_a_place_you_have_walked(g, "run/explored.json")
    ck("a gym of a walked city is not the city", r is None, r)
    g2 = ("the guards at the gates of Route 5 and 6 block access to the Rock Tunnel "
          "until they are given a drink")
    r = A._blocks_a_place_you_have_walked(g2, "run/explored.json")
    ck("a walked place barred is still refused", r == "ROCK_TUNNEL", r)
finally:
    os.chdir(here)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

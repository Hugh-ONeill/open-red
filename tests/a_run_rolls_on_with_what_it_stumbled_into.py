#!/usr/bin/env python3
"""An attempt that failed its own objective but walked partway into a later
one can roll on with that one.

Run 20, the Flash leg (2026-10-01): heading for Fuchsia, the attempt went
into the Game Corner, down the Rocket Hideout to B4F and took the LIFT_KEY,
its own leg 26; the rewrite, bound to Flash, planned "exit_rocket_hideout".
User: "accidentally stumbling into doing the right thing, we want them to
keep trying to do that ... it would be better if the model could just roll
with it".
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


gained = ("WHAT CHANGED WHILE THIS LEG RAN — events that fired: EVENT_BEAT_ROCKET_HIDEOUT_1_TRAINER_0; "
          "items gained: LIFT_KEY x1; 4 place(s) entered for the first time — by map: GAME_CORNER x1, "
          "ROCKET_HIDEOUT_B1F x1, ROCKET_HIDEOUT_B2F x1, ROCKET_HIDEOUT_B3F x1; "
          "4 map(s) never stood on before: GAME_CORNER, ROCKET_HIDEOUT_B1F, ROCKET_HIDEOUT_B2F, "
          "ROCKET_HIDEOUT_B3F")
ahead = [(17, "Exit Rock Tunnel"), (26, "Infiltrate the Team Rocket secret base in Celadon City"),
         (27, "Retrieve the Secret Key from the Game Corner")]
asked = []


def answer(reply):
    def chat(msgs, model):
        asked.append(msgs[-1]["content"])
        return json.dumps(reply)
    return chat


A.chat_json = answer({"why": "I am inside the hideout with its key", "leg": 26, "from": "ROCKET_HIDEOUT_B2F"})
got = A.check_momentum("a party Pokemon knows FLASH", 16, ahead, "in ROCKET_HIDEOUT_B3F", gained, "m")
ck("a leg on the list, resting on a place the attempt reached, is taken", got and got[0] == 26, got)
ck("...and the page holds what the attempt did and the list, in order",
   "WHAT THE ATTEMPT DID: " + gained in asked[-1] and asked[-1].index("26") < asked[-1].index("27"))

A.chat_json = answer({"why": "x", "leg": 26, "from": "SILPH_CO_1F"})
ck("a pick resting on ground the attempt never reached is refused",
   A.check_momentum("g", 16, ahead, "", gained, "m") is None)
A.chat_json = answer({"why": "x", "leg": 40, "from": "GAME_CORNER"})
ck("a number not on the list after this leg is refused",
   A.check_momentum("g", 16, ahead, "", gained, "m") is None)
A.chat_json = answer({"why": "nothing to carry on", "leg": None})
ck("null keeps the leg where it is", A.check_momentum("g", 16, ahead, "", gained, "m") is None)
ck("nothing gained, nothing asked", A.check_momentum("g", 16, ahead, "", "", "m") is None)
n0 = len(asked)
small = ("WHAT CHANGED WHILE THIS LEG RAN — events that fired: EVENT_BEAT_ROUTE_8_TRAINER_0, "
         "EVENT_BEAT_ROUTE_8_TRAINER_1; 1 place(s) entered for the first time — by map: ROUTE_8 x1")
A.chat_json = answer({"why": "the path toward Celadon", "leg": 26, "from": "ROUTE_8"})
ck("one new route and trainers beaten is not asked (a road toward a place is not partway in)",
   A.check_momentum("g", 16, ahead, "", small, "m") is None and len(asked) == n0)
ck("...an item, a badge, a story event or three new places is",
   A.momentum_worth_asking(gained)
   and A.momentum_worth_asking("events that fired: EVENT_BEAT_ERIKA; badges earned: RAINBOWBADGE")
   and A.momentum_worth_asking("events that fired: EVENT_GOT_EEVEE")
   and A.momentum_worth_asking("3 place(s) entered for the first time — by map: A x1, B x1, C x1"))

camp = (ROOT / "campaign.sh").read_text()
ck("campaign.sh asks only when the attempt fired events or entered new places",
   'grep -qE "events that fired|entered for the first time"' in camp and "--check-momentum" in camp)
ck("...per attempt, from its own snapshot", "snap run/attempt_start_one.json" in camp
   and "diff run/attempt_start_one.json" in camp)
ck("...and before a blocked step goes to the ladder",
   camp.index("--check-momentum") < camp.index('grep -qE "RESULT: STEP BLOCKED"'))
ck("...handing the chain the leg by exit 7", "exit 7" in camp and "run/momentum_pick" in camp)
fd = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain passes the leg index", 'RED_LEG_INDEX="$i"' in fd)
ck("...pulls the named leg to this position, the current one behind it",
   'python planner/pull_leg.py pull "$i" "$_k"' in fd and "momentum_take" in fd)
ck("...on both campaign calls", fd.count('= 7') >= 2 or ('"$crc" = 7' in fd and '"$_crc2" = 7' in fd))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

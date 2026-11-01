#!/usr/bin/env python3
"""What was said last is shown, with its box closed, as closed.

Run 63, 2026-10-24: last_text outlives its box, and a question in it was
read as still asked six times (a nickname box four rounds after it closed,
the Pewter guide, a Link receptionist, a trade offer), each answered with a
menu op that failed "no list menu on top" (user: "yeah add it").

Pinned: text_on_screen false relabels the words and says the box closed;
a box still up keeps last_text; no last_text adds nothing; the sketch is
still dropped; the caveat line is not printed for a closed box.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

Q = "Do you want to give a nickname to RATTATA?"
o = E._obs_nosketch({"mode": "overworld", "text_on_screen": False, "last_text": Q,
                     "map": {"id": "ROUTE_2", "sketch": {"rows": ["..."]}}})
ck("a closed box's words are relabeled as closed",
   "last_text" not in o and o.get("said_last_box_closed", "").startswith(Q)
   and "that box has closed" in o["said_last_box_closed"], o)
ck("...and the sketch is still dropped", "sketch" not in o["map"], o)
up = E._obs_nosketch({"mode": "ui", "text_on_screen": True, "last_text": Q, "map": {}})
ck("a box still up keeps last_text", up.get("last_text") == Q and "said_last_box_closed" not in up, up)
none = E._obs_nosketch({"mode": "overworld", "text_on_screen": False, "map": {}})
ck("no last_text adds nothing", "said_last_box_closed" not in none, none)
src = (ROOT / "planner" / "executor.py").read_text()
# run 70, 2026-11-01: "WEEDLE was caught!" read as a catch still waiting on a
# nickname, beside a party of two already holding that WEEDLE
BT = "Wild WEEDLE appeared! / All right! WEEDLE was caught!"
road = E._obs_nosketch({"mode": "overworld", "text_on_screen": False, "battle_text": BT, "map": {}})
ck("outside a battle its lines are said as over",
   "battle_text" not in road and road.get("last_battle_over", "").startswith(BT)
   and "that battle is over" in road["last_battle_over"], road)
fight = E._obs_nosketch({"mode": "battle", "battle_text": BT, "map": {}})
ck("...inside one they stand as they are",
   fight.get("battle_text") == BT and "last_battle_over" not in fight, fight)
ck("the caveat line is not printed for a closed box",
   'and (obs or {}).get("text_on_screen") is not False else "")' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

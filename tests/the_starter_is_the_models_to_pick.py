#!/usr/bin/env python3
"""No sweep presses a starter's Poke Ball: the choice of starter is the model's.

Run 26 (2026-10-02): after Oak's escort the room sweep pressed two of the
balls on his table and left the last question open ("So! You want the water
POKeMON, SQUIRTLE?"); the model, shown only that one, said yes, never having
read the other two. User: "did it see all the mons the way its supposed to?"
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


x = object.__new__(E.Executor)
x._flags_now = ["EVENT_FOLLOWED_OAK_INTO_LAB"]
why = x._not_for_explore_to_press("ITEM_OAKS_LAB_7_3", "item", "OAKS_LAB|4,1")
ck("before the starter is chosen, a ball on Oak's table is not explore's to press",
   "choice of starter" in why, why)
ck("...but the people in the lab still are",
   x._not_for_explore_to_press("OAKSLAB_GIRL", "npc", "OAKS_LAB|4,1") == "")
x._flags_now.append("EVENT_GOT_STARTER")
ck("once a starter is chosen, the last ball is an ordinary thing again",
   x._not_for_explore_to_press("ITEM_OAKS_LAB_8_3", "item", "OAKS_LAB|4,1") == "")
x._flags_now = []
ck("a ball anywhere else is pressed as before",
   x._not_for_explore_to_press("ITEM_ROUTE_2_13_9", "item", "ROUTE_2|1,1") == "")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

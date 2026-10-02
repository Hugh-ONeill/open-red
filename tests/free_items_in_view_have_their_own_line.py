#!/usr/bin/env python3
"""Items lying on the floor get their own line near the top of the page.

Run 19 took most of its deliberate pickups only when stuck (round 7+); run
20 crossed Mt Moon in fifteen minutes, took 1 of 7 balls and walked past
TM01 (user, 2026-10-01: "it should pick up the balls it sees because theyre
free and useful ... only picking up items when its soft stuck").
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import ledger as L  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


C = L.Candidate
cands = [C(key="ITEM_MT_MOON_B2F_1", kind="item", status="untouched", x=10, y=5),
         C(key="ITEM_MT_MOON_B2F_2", kind="item", status="untouched", x=3, y=4),
         C(key="ITEM_MT_MOON_B2F_3", kind="item", status="untouched", x=30, y=30, reachable=False),
         C(key="ITEM_MT_MOON_B2F_4", kind="item", status="touched", x=1, y=1),
         C(key="MTMOONB2F_SUPER_NERD", kind="npc", status="unspoken")]
obs = {"player": {"x": 2, "y": 4}, "bag": {"POKE_BALL": 3}}
t = L._items_lying_text(cands, obs)
ck("the count of items it can walk to", "never taken: 2 you can walk to" in t, t)
ck("...the nearest by steps", "nearest: ITEM_MT_MOON_B2F_2 at (3,4), about 1 steps" in t, t)
ck("...the ones it cannot reach, counted apart", "1 you cannot walk to from here" in t, t)
ck("...and a taken one is not counted", "B2F_4" not in t)
ck("it says how to take one, not to take one", "takes one" in t and "should" not in t.lower())
full = {"player": {"x": 2, "y": 4}, "bag": {f"K{i}": 1 for i in range(20)}}
ck("a full bag says a new kind will not fit", "will not fit" in L._items_lying_text(cands, full))
ck("no items, no line", L._items_lying_text(cands[4:], obs) == "")
src = (ROOT / "planner/ledger.py").read_text()
ck("it sits right under the head line", 'lines = [head + "."]\n    _items = _items_lying_text(cands, obs)' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

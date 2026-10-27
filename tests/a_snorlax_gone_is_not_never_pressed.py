#!/usr/bin/env python3
"""Someone the ledger saw gone or beaten is not "seen and never pressed".

Run 67, 2026-10-27: ROUTE16_SNORLAX was sighted from ROUTE_16|24,2, woken
by the POKE FLUTE from (27,10), EVENT_BEAT_ROUTE16_SNORLAX fired, and the
ledger wrote it gone in ROUTE_16|27,10. "Wake the Snorlax blocking the path
to Saffron City" was then refused by every rung as "names ROUTE16_SNORLAX,
seen in ROUTE_16|24,2 and never spoken to or pressed", passed over, and
gone back to.

Pinned: a name gone in another region, or beaten on screen, is not
untouched; someone merely unpressed still is.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

d = Path(tempfile.mkdtemp(prefix="gone_"))
led = d / "explored.json"
GOAL = "Wake the Snorlax blocking the path to Saffron City using the POKE FLUTE"

led.write_text(json.dumps({"sightings": {"ROUTE_16|24,2": ["CUT_TREE", "ROUTE16_SNORLAX"]},
                           "touched": {}}))
r = A.untouched_named(GOAL, str(led))
ck("before it is gone, the Snorlax reads never pressed", r and r[0][1] == "ROUTE16_SNORLAX", r)

led.write_text(json.dumps({"sightings": {"ROUTE_16|24,2": ["CUT_TREE", "ROUTE16_SNORLAX"]},
                           "touched": {}, "gone": {"ROUTE_16|27,10": ["ROUTE16_SNORLAX"]}}))
r = A.untouched_named(GOAL, str(led))
ck("gone in another part of the map, it is not never pressed", r == [], r)

led.write_text(json.dumps({"sightings": {"SILPH_CO_4F|20,0": ["SILPHCO4F_ROCKET1"]},
                           "touched": {}, "beaten_seen": ["SILPHCO4F_ROCKET1"]}))
r = A.untouched_named("Defeat the Rocket on Silph 4F", str(led))
ck("a trainer beaten on screen is not never pressed", r == [], r)

led.write_text(json.dumps({"sightings": {"BILLS_HOUSE|0,0": ["BILLSHOUSE_BILL1"]},
                           "touched": {}, "gone": {"ROUTE_16|27,10": ["ROUTE16_SNORLAX"]}}))
r = A.untouched_named("Talk to Bill", str(led))
ck("someone simply unpressed still is", r and r[0][1] == "BILLSHOUSE_BILL1", r)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

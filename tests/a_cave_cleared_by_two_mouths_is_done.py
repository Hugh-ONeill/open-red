#!/usr/bin/env python3
""""Clear <place>" is done when the record shows two of its mouths used.

Run 72, 2026-11-03: "Clear Mt. Moon" ended in Cerulean City with the far
mouth walked (MT_MOON_B1F --(27,3)--> ROUTE_4|36,2 beside MT_MOON_1F
--(14,35)--> ROUTE_4|4,4). _through_by_record only read through / across /
traverse / navigate, so the judge was asked instead; its "Cerulean is only
possible after exiting Mt. Moon" was refused as one fact reasoned from
another, and the chain walked the party back to the mountain's door to do
the leg again.

Pinned: "Clear X" with two mouths used is done by the record; a one-door
place ("Clear the Pokemon Tower") is not credited by it; and the refusal
side (_not_through_yet) still ignores "clear", so a one-door place is not
refused for ever. Synthetic.
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

obs = Path(tempfile.mkdtemp()) / "explored.json"
obs.write_text(json.dumps({
    "explored": {
        "ROUTE_4|4,4": {"18,5": {"n": 1, "to": "MT_MOON_1F|3,2"}},
        "MT_MOON_1F|3,2": {"14,35": {"n": 1, "to": "ROUTE_4|4,4"},
                           "5,5": {"n": 1, "to": "MT_MOON_B1F|20,2"}},
        "MT_MOON_B1F|20,2": {"27,3": {"n": 1, "to": "ROUTE_4|36,2"}},
        "LAVENDER_TOWN|6,0": {"14,5": {"n": 2, "to": "POKEMON_TOWER_1F|9,1"}},
        "POKEMON_TOWER_1F|9,1": {"10,17": {"n": 2, "to": "LAVENDER_TOWN|6,0"}}},
    "visits": {"ROUTE_4|4,4": 2, "MT_MOON_1F|3,2": 3, "MT_MOON_B1F|20,2": 1,
               "ROUTE_4|36,2": 1, "POKEMON_TOWER_1F|9,1": 2}}))

got = A._through_by_record("Clear Mt. Moon", obs)
ck("clearing a cave left by two mouths is done by the record",
   got and "ROUTE_4|36,2" in got and "ROUTE_4|4,4" in got, got)
ck("...in any tense", A._through_by_record("Mt. Moon cleared", obs))
ck("the old verbs still answer", A._through_by_record("Traverse Mt. Moon", obs))
ck("a one-door place is not credited by its door",
   A._through_by_record("Clear the Pokemon Tower", obs) is None)
ck("the refusal side does not read clear, so a one-door place is not "
   "refused for ever",
   A._not_through_yet("Clear the Pokemon Tower", obs) is None)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

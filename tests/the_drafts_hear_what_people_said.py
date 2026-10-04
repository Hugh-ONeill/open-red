#!/usr/bin/env python3
"""The drafts get WHAT PEOPLE HAVE SAID whole, including what was heard last,
and the ideas weigh each memory against what was heard.

Run 36, 2026-10-03: late in a run observed_text is over its evidence budget
and drops WHAT PEOPLE HAVE SAID entirely; people_said_text sliced that page,
so every draft and ideas call got NOTHING people said, and the section kept
only the 14 most-stood-in places anyway, leaving out the Diner ("basement
under the GAME CORNER") and the Chief's house ("no secret switch behind it")
while leg 27 drafted coin plans. Hand test on the run's record after the fix:
the ideas reach the hideout and the picked plan's first step hunts the key
there. Source pins plus the section's own content on a synthetic record."""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
src = (ROOT / "planner/author.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ck("the section is kept as built, before the budget trims it",
   "_PEOPLE_SECTION[str(path)] = _people" in src and "_whole = _PEOPLE_SECTION.get(" in src)
ck("places heard from lately join the most-stood-in ones",
   "keep = sorted(set(ranked[:14]) | set(recent))" in src)
ck("the ideas ask what was heard about each memory",
   '\\"heard\\"' in A.PREMISE_NOTE or '"heard"' in A.PREMISE_NOTE)
with tempfile.TemporaryDirectory() as td:
    rec = {"explored": {"R0|0,0": {"north": {"to": "R1|0,0", "n": 1}}},
           "visits": {f"R{i}|0,0": 50 for i in range(20)} | {"DINER|1,1": 1},
           "hints": {f"R{i}|0,0": [f"P{i}: line number {i} said here"] for i in range(20)}
                    | {"DINER|1,1": ["MAN: Psst! There's a basement under the GAME CORNER."]},
           "hints_at": {f"R{i}|0,0": {f"P{i}: line number {i} said here": {"seq": 10}} for i in range(20)}
                       | {"DINER|1,1": {"MAN: Psst! There's a basement under the GAME CORNER.": {"seq": 40}}}}
    p = Path(td) / "explored.json"; p.write_text(json.dumps(rec))
    t = A.people_said_text(str(p))
    ck("a place stood in once but heard from last is in the section",
       "basement under the GAME CORNER" in t, t[:200])
failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if failed else 0)

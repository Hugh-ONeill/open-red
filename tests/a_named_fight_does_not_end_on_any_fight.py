#!/usr/bin/env python3
"""A step about one opponent does not end on any fight; a leg whose drafts
all end already true asks check-done first; a VOID whose reason is a done
verdict leaves as done; the suite has a no-game runner.

Run of record 9, 2026-09-26: "Walk along Route 1 until the rival initiates a
battle" ended on {"mode": "battle"}, and the model, knowing the rival had
already been fought, wrote "I will enter the tall grass on Route 1 to
trigger a wild battle to satisfy the condition" (user: "put it on the next
stop list, then fix it along with the rest"). The rest: the 2026-09-07
next-stop items, checked against the code of 2026-09-26.

Pinned: a step whose done_when is only mode:battle is refused when it names
an opponent (the rival, a leader, a Rocket, someone defeated by name), not
when it is about a wild Pokemon; authoring that fails mostly on ALREADY
HOLDS/FIRED exits 6 and the chain asks check-done before any push; the
wording rung's done verdict exits 4, not 5; tests/run_suite.sh runs the
no-game tests and leaves the game-booting ones out. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def plan(goal_text, dw, sid="encounter_rival"):
    return {"subgoals": [{"id": sid, "goal_text": goal_text, "done_when": dw}]}


RIVAL = plan("Walk along Route 1 until the rival initiates a battle", {"mode": "battle"})
p = A.validate(RIVAL)
ck("a step about the rival cannot end on any fight",
   any("which ANY wild encounter makes true" in x for x in p), p)
ck("...nor a step that defeats someone by name",
   any("ANY wild encounter" in x for x in A.validate(plan("Defeat Brock", {"mode": "battle"}, "defeat_brock"))))
ck("...but a step about a wild Pokemon may",
   not any("ANY wild encounter" in x
           for x in A.validate(plan("Find a wild Pokemon in the grass", {"mode": "battle"}, "find_wild"))))
ck("...and a named fight ending on its badge is fine",
   not any("ANY wild encounter" in x
           for x in A.validate(plan("Defeat Brock", {"badge": "BOULDERBADGE"}, "defeat_brock"))))

au = (ROOT / "planner/author.py").read_text()
ck("authoring that fails mostly on ALREADY-true conditions exits 6",
   "if INVALID_ROUNDS[0] and ALREADY_ROUNDS[0] * 2 >= INVALID_ROUNDS[0]:" in au
   and "sys.exit(6)" in au
   and 'if "ALREADY HOLDS" in fb or "ALREADY FIRED" in fb:' in au)
sh = (ROOT / "fresh_discovery.sh").read_text()
ck("...and the chain asks check-done before pushing it",
   'if [ "$_arc" = 6 ] && python planner/author.py --check-done' in sh
   and sh.index('if [ "$_arc" = 6 ]') < sh.index('authoring failed for leg $i ($goal) — pushing it later'))
ck("the wording rung's done verdict leaves as done (exit 4), not VOID",
   "if _as_done:\n            WORDING_SAYS_DONE[0] = True" in au)
rs = (ROOT / "tests/run_suite.sh").read_text()
ck("the no-game runner leaves out the tests that boot a game",
   "pc_box" in rs and "contract" in rs and "grep -Ev" in rs)
ck("...and the README points at it", "tests/run_suite.sh" in (ROOT / "README.md").read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

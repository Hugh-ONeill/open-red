#!/usr/bin/env python3
"""A hunt that was still finding new ground when its rounds ran out is not
handed to the next step's walk back.

Run 34, 2026-09-23, leg 14. The plan was: get FRESH_WATER (a hunt, no
steps), reach Route 5, cross the Route 5 gate, cross the Route 6 gate,
reach Celadon, enter the store. The hunt took the Rock Tunnel door on
Route 10, the ladder down, and was exploring B1F when its budget ended
(dt 459 the door, 519 the ladder, 549 the floor, 553.7 the end). The step
after it — reach_route_5 — proposed the ladder up and a walk to the gate
that had already refused the run, the gate refused it again, the plan
failed there, and the rewrite was made from Cerulean and hunted the west
again. Six such walk-backs, fourteen plan versions, two hours.

The missed-hop rule already ends a plan when a PLACE step fails in front
of a PLACE step this run has never walked ("the honest state to plan
from"). This is its sibling: a THING step that ran out of rounds with its
last round or the one before it still finding something new, in front of
a PLACE step, ends the plan where the party stands. Nothing is pointed at.

Pinned: the reading, round by round; a place step or a deed after it is
not the case; no news is not the case; the branch sits after the
missed-hop rule and before the plain carry, writes its row and falls
through to the plan's failure like the missed-hop rule does; every site
that finds news marks the round, and every round is counted. Synthetic."""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ex_at(news_at, rounds):
    ex = E.Executor.__new__(E.Executor)
    ex.logf = io.StringIO()
    ex.t0 = time.time()
    ex._esc_news_at, ex._esc_rounds = news_at, rounds
    return ex


HUNT = {"id": "get_fresh_water", "done_when": {"has_item": {"FRESH_WATER": 1}}}
WALK = {"id": "reach_route_5", "done_when": {"map": "ROUTE_5"}}
AREA = {"id": "reach_route_5", "done_when": {"area": "ROUTE_5|6,0"}}
DEED = {"id": "beat_surge", "done_when": {"badge": "THUNDERBADGE"}}
HOP = {"id": "reach_route_10", "done_when": {"map": "ROUTE_10"}}

ck("a hunt whose last round found something, before a walk, ends the plan",
   ex_at(18, 18)._hunt_still_finding(HUNT, WALK))
ck("...or whose round before last did (the last may have been a fight)",
   ex_at(17, 18)._hunt_still_finding(HUNT, WALK))
ck("...but not one that had found nothing for two rounds",
   not ex_at(16, 18)._hunt_still_finding(HUNT, WALK))
ck("...nor one that never found anything",
   not ex_at(0, 18)._hunt_still_finding(HUNT, WALK))
ck("a walk to an area counts as a walk",
   ex_at(18, 18)._hunt_still_finding(HUNT, AREA))
ck("a deed after it is not a walk back",
   not ex_at(18, 18)._hunt_still_finding(HUNT, DEED))
ck("nothing after it is nothing to walk to",
   not ex_at(18, 18)._hunt_still_finding(HUNT, None))
ck("a place step that failed is the missed-hop rule's, not this one's",
   not ex_at(18, 18)._hunt_still_finding(HOP, WALK))
ck("a step with no condition is not a hunt",
   not ex_at(18, 18)._hunt_still_finding({"id": "x"}, WALK))
ck("the counters start empty, so a step that never ran cannot fire it",
   not E.Executor.__new__(E.Executor)._hunt_still_finding(HUNT, WALK))

SRC = (ROOT / "planner/executor.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
i_chain = _code.index('self.log("chain_subgoal_failed"')
i_hunt = _code.index("elif self._hunt_still_finding(sg, _nxt) and not last:")
i_carry = _code.index("elif fails < 3 and not last:")
ck("the branch sits after the missed-hop rule and before the plain carry",
   i_chain < i_hunt < i_carry)
_branch = _code[i_hunt:i_carry]
ck("it writes its own row", 'self.log("hunt_ends_in_new_ground"' in _branch)
ck("...and falls through to the plan's failure, as the missed-hop rule does",
   "continue" not in _branch
   and _code.index('self.log("plan_failed_at"') > i_carry)
ck("every site that finds news marks the round",
   _code.count("self._esc_news_at = rnd") == 3
   and _code.count('self.log("round_for_news"') == 2
   and _code.count('self.log("round_for_new_ground"') == 1)
ck("...and every round is counted",
   'rnd += 1\n            _wipes_at_start = getattr(self, "_wipes_logged", 0)\n'
   '            self._esc_rounds = rnd' in _code)
ck("both start at zero when a step's escalation begins",
   "self._esc_news_at = 0\n        self._esc_rounds = 0" in _code
   and _code.index("self._esc_news_at = 0") > _code.index("spent, rnd, chat_fails = 0, 0, 0"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

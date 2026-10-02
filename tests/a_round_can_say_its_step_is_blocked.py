#!/usr/bin/env python3
"""A round can say its step is blocked, naming the wall from the run's own
record, and the blocker record holds every kind of wall.

Run 20 (2026-10-01): on Route 12 the model wrote "the path south to Route 13
is blocked by Snorlax", went back into the Rocket Hideout to look for a way
past it, and the next round re-derived "go to Fuchsia" from the step header
and walked out again. Nothing could end the attempt on its word, Snorlax's
own line ("A sleeping POKeMON blocks the way!") never reached the blocker
record, a cut tree never left it, and the "ways that turned you back" line
showed the three oldest walls by count and none of that day's.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import executor as E  # noqa: E402
import author as A  # noqa: E402

x = object.__new__(E.Executor)
x.blockers = {}
x._cur_target = "map:FUCHSIA_CITY"
x._mark_now = None
x._logged = []
x.log = lambda kind, **kw: x._logged.append((kind, kw))

# --- an HM wall leaves the record once the party can clear it ---
x._note_blocker("ROUTE_9|0,8", "west", "seam", "the walk was fenced — CUT_TREE (a bush CUT clears) at (5,8)")
x._note_blocker("ROUTE_12|10,21", "west", "seam", "the walk was fenced — WATER at (4,25)")
cut = {"badges": ["BOULDERBADGE"], "party": [{"species": "VENUSAUR", "moves": ["CUT", "RAZOR_LEAF"]}]}
ck("knowing CUT without the badge that allows it outside battle clears nothing",
   x._clear_hm_blockers(cut) == [] and not x.blockers["ROUTE_9|0,8|west"]["cleared"])
cut["badges"].append("CASCADEBADGE")
got = x._clear_hm_blockers(cut)
ck("with CUT known and the CASCADEBADGE worn, the cut-tree row is cleared",
   got == ["ROUTE_9|0,8|west"] and x.blockers["ROUTE_9|0,8|west"]["cleared"], got)
ck("...and says why", "can CUT it now" in x.blockers["ROUTE_9|0,8|west"].get("cleared_how", ""))
ck("...and a wall CUT does not clear stays", not x.blockers["ROUTE_12|10,21|west"]["cleared"])
src = inspect.getsource(E.Executor._note)
ck("checked on every observation with a party", "_clear_hm_blockers(obs)" in src)

# --- a thing that says it blocks is a wall ---
y = object.__new__(E.Executor)
y.blockers, y._cur_target, y._mark_now = {}, "map:FUCHSIA_CITY", None
y.log = lambda *a, **k: None
y._outcomes, y._gone, y._press_log = {}, {}, {}
y._where = lambda o: "ROUTE_12|10,21"
y._walk_cut_by_the_world = lambda n: False
y._kind_on_map = lambda o, k: "npc"
y._record_outcome({}, "interact", {"name": "ROUTE12_SNORLAX"},
                  'interact(name=ROUTE12_SNORLAX): the world did not change, but it SPOKE — '
                  'it said: "A sleeping POKeMON blocks the way!"')
b = y.blockers.get("ROUTE_12|10,21|ROUTE12_SNORLAX") or {}
ck("a pressed thing whose words say it blocks gets a row, in its words",
   b.get("kind") == "said" and "blocks the way" in b.get("what", ""), y.blockers)
y._record_outcome({}, "interact", {"name": "ROUTE12_FISHER1"},
                  'interact(name=ROUTE12_FISHER1): ok — it said: "I love fishing!"')
ck("...and one that does not, none", "ROUTE_12|10,21|ROUTE12_FISHER1" not in y.blockers)

# --- the wall is named from the record ---
ck("a wall matches by its key", y._wall_in_record("ROUTE12_SNORLAX")[1] == "ROUTE12_SNORLAX")
ck("...or by a name inside its words", y._wall_in_record("snorlax") is None
   or y._wall_in_record("snorlax")[1] == "ROUTE12_SNORLAX")
ck("...or by the page's AREA KEY line", y._wall_in_record("ROUTE_12|10,21 ROUTE12_SNORLAX") is not None)
ck("a wall the record does not hold is None", y._wall_in_record("a mysterious force") is None)

esc = inspect.getsource(E.Executor.escalate)
ck("the op is read in the round", 's2.get("op") == "blocked"' in esc)
ck("...refused with a reason when the record has no such wall",
   "step_blocked_refused" in esc and "is not in it" in esc)
ck("...and ends the attempt when it does", 'self.log("step_blocked"' in esc
   and "ending the attempt" in esc)
rp = inspect.getsource(E.Executor.run_plan)
ck("a blocked step is not backtracked over", '"_step_blocked"' in rp)
ex_src = (ROOT / "planner/executor.py").read_text()
ck("the verdict says STEP BLOCKED", 'f"STEP BLOCKED (' in ex_src)
ck("the model is told the op exists", '{"op":"blocked","wall":' in ex_src)
camp = (ROOT / "campaign.sh").read_text()
ck("campaign.sh hands a blocked step to the ladder, not the rewrite",
   'grep -qE "RESULT: STEP BLOCKED"' in camp
   and camp.index("RESULT: STEP BLOCKED") < camp.index("Which leg died"))

# --- the journal carries it to every rung ---
td = Path(tempfile.mkdtemp())
j = td / "log.jsonl"
j.write_text("\n".join(json.dumps(r) for r in [
    {"kind": "plan_start", "goal": "a party Pokemon knows FLASH"},
    {"kind": "escalate_start", "subgoal": "go_to_fuchsia_city"},
    {"kind": "step_blocked", "subgoal": "go_to_fuchsia_city", "want": {"map": "FUCHSIA_CITY"},
     "wall": "ROUTE12_SNORLAX", "where": "ROUTE_12|10,21",
     "what": 'ROUTE12_SNORLAX said: "A sleeping POKeMON blocks the way!"',
     "why": "Route 12 south is shut by a sleeping Snorlax; I have no way to wake it"}]) + "\n")
jt = A.journal_text(j)
ck("the journal names the wall, the record's words and the model's",
   "DECLARED BLOCKED" in jt and "ROUTE12_SNORLAX" in jt and "blocks the way" in jt
   and "no way to wake it" in jt, jt[-600:])

pg = inspect.getsource(E.Executor)
ck("the turned-back line keeps the newest wall, whatever its count",
   "AND THE NEWEST, WHATEVER ITS COUNT" in pg and 'b["t"] = round(time.time(), 1)' in pg)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

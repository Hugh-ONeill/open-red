#!/usr/bin/env python3
"""A sweep a script turns back is written down as a way that turned the
run back, and every sweep on that floor afterwards aims elsewhere.

The sweep aims at the nearest spot where seen ground ends. A script that
stops the walk one step in leaves the spot unseen, so it is still the
nearest, and the next sweep aims at it again. Run 32 walked five sweeps
in a row into Viridian's sleeping old man; the run of record on
2026-09-24 did it five more times on leg 4, each "swept 1 step(s), 0
cell(s) newly on screen ... it said: 'You can't go through here! This is
private property!'", three attempts spent in place with the mart's door
on the page the whole time (user: "repeated sweeps into the cranky old
man cost two attempts"). A crossing a script turns back already became a
blocker row; a sweep's did not, and nothing learned from the refusal.

Now the shim says which spot the sweep was walking toward when a script
stopped it and takes a list of spots to skip; the executor writes the
spot down beside the words that stopped it, with a journal row, and hands
the floor's refused spots to every sweep it sends there. The page lists
the row like any other way that turned the run back. Nothing is pointed
at: the sweep aims at the next spot, and the model reads what refused it.

Pinned: the row is written from the sweep's own words, cell and speaker
and line; a sweep that saw something is not a refusal; a sweep stopped
without a named spot writes nothing; the skip list is the floor's live
cell rows and nothing else; every sweep the executor builds carries it;
the shim honors it and names the spot; the page words the row. Synthetic."""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ex():
    e = E.Executor.__new__(E.Executor)
    e.logf = io.StringIO()
    e.t0 = time.time()
    e.blockers = {}
    e._cur_target = "map:PEWTER_CITY"
    return e


HERE = "VIRIDIAN_CITY|17,0"
STOPPED = ('explore (sweeping unseen ground): sweep(until=map_change): the world '
           'did not change, but it SPOKE — swept 1 step(s), 0 cell(s) newly on '
           'screen; nothing new came into view — stopped: interrupted (battle or '
           'script) by VIRIDIANCITY_OLD_MAN_SLEEPY on the way to (18,7) — it said: '
           '"You can\'t go through here! This is private property!"')
e = ex()
ck("the spot a script stopped the sweep from is written down",
   e._note_sweep_refusal(HERE, [STOPPED]) == "18,7"
   and e.blockers.get(f"{HERE}|18,7", {}).get("kind") == "cell", e.blockers)
b = e.blockers[f"{HERE}|18,7"]
ck("...with the speaker and the words that stopped it",
   "VIRIDIANCITY_OLD_MAN_SLEEPY" in b["what"] and "private property" in b["what"], b["what"])
ck("...and a journal row",
   any(json.loads(l)["kind"] == "sweep_refused" and json.loads(l)["cell"] == "18,7"
       for l in e.logf.getvalue().splitlines()))
ck("a second refusal bumps the same row",
   e._note_sweep_refusal(HERE, [STOPPED]) == "18,7" and b["n"] == 2, b)
ck("a sweep that saw something on the way is not a refusal",
   ex()._note_sweep_refusal(HERE, [STOPPED.replace("0 cell(s)", "150 cell(s)")]) == "")
ck("a sweep stopped with no named spot writes nothing",
   ex()._note_sweep_refusal(HERE, [STOPPED.replace(" on the way to (18,7)", "")]) == "")
ck("a sweep that ended for another reason writes nothing",
   ex()._note_sweep_refusal(HERE, ["sweep: ok (swept 40 step(s), 9 cell(s) newly on screen — stopped: something new came into view)"]) == "")

ck("the floor's refused spots are what the next sweep skips",
   e._sweep_skip(HERE) == ["18,7"] and e._sweep_step(HERE) == {"op": "sweep", "skip": ["18,7"]})
ck("...and nothing else's: another floor's rows, a door, a cleared row",
   e._sweep_skip("PEWTER_CITY|4,2") == [])
e._note_blocker(HERE, "9,29", "door", "it was shut")
e.blockers[f"{HERE}|18,7"]["cleared"] = True
ck("...a door row is not a spot, and a cleared spot is aimed at again",
   e._sweep_step(HERE) == {"op": "sweep"})
ck("the extra words of a sweep ride along",
   ex()._sweep_step(HERE, until="map_change", steps=None) == {"op": "sweep", "until": "map_change"})

SRC = (ROOT / "planner/executor.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
ck("every sweep the executor builds carries the floor's skips",
   '{"op": "sweep"}' not in _code.replace('st = {"op": "sweep"}', "")
   and _code.count("self._sweep_step(") >= 4, _code.count("self._sweep_step("))
ck("the local sweep's own result is read for a refusal",
   "self._note_sweep_refusal(_reg_here, tr)" in _code)
ck("the page words the row",
   'else "the ground" if b.get("kind") == "cell"' in _code
   and 'f"the walk toward ({k})" if b.get("kind") == "cell"' in _code)

LUA = (ROOT / "harness/shim.lua").read_text()
ck("the shim takes spots to skip and never aims at one",
   "for _, k in ipairs(type(c.skip) == \"table\" and c.skip or {}) do" in LUA
   and "if not tried[k] and not skip[k] and not (f.x == p.cellX and f.y == p.cellY) then" in LUA)
ck("...and names the spot it was walking toward when a script stops it",
   '(" on the way to (%d,%d)"):format(last_target.x, last_target.y)' in LUA
   and "last_target = target" in LUA)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

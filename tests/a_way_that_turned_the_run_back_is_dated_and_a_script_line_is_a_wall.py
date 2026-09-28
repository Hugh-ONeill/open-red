#!/usr/bin/env python3
"""A script that stops a sweep is a wall for later sweeps, and every way that
turned the run back says what has happened since, only walling while nothing
has.

Run 16 (2026-09-28): Viridian's sleeping old man turned each sweep back, and
only the TARGET spot was skipped, so the next sweep aimed at a neighbour
behind the same line (user: "becoming an issue literally every run"). Then,
after the parcel, the Pokedex and his catch demo, the page still listed his
"private property" rows under "Nothing about you changed since", and the run
went west into the rival twice (user: "despite literally talking to the now
calm old man").

Checked on the game from run 16's pre-parcel Viridian checkpoint: the sweep
stopped "standing on (19,9)", a wall 19,9 was recorded, and the two sweeps
after it went east to the gym and the mart instead of into him.

Pinned: the shim says where a script stopped it and takes `wall`; the
executor records a wall only when words were said; a blocker keeps the world
mark it was recorded in; skips and walls apply only while that mark holds;
the row says what has happened since once it moves; the author's rows too.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


sh = (ROOT / "harness/shim.lua").read_text()
ck("the shim says where a script stopped the sweep",
   '(" standing on (%d,%d)"):format(_p.cellX, _p.cellY)' in sh)
ck("...and takes walls no sweep walks through",
   "for k in pairs(wall) do avoid[k] = true end" in sh
   and "local _walled = next(wall) ~= nil" in sh)

ex = object.__new__(E.Executor)
ex.blockers, ex._cur_target, ex.logged = {}, "map:VIRIDIAN_FOREST", []
ex.log = lambda kind, **kw: ex.logged.append((kind, kw))
ex._mark_now, ex._flags_now = [0, 10, 3], ["EVENT_A"]
R = "VIRIDIAN_CITY|17,0"
trace = ["sweep(): ok (swept 1 step(s), 0 cell(s) newly on screen; nothing new came "
         "into view — stopped: interrupted (battle or script) on the way to (19,5) "
         "standing on (19,9)) — it said: \"You can't go through here! This is "
         "private property!\""]
ck("a script's stop records the target and a wall where it stood",
   ex._note_sweep_refusal(R, trace) == "19,5"
   and ex._sweep_skip(R) == ["19,5"] and ex._sweep_skip(R, kind="wall") == ["19,9"])
battle = [trace[0].split(" — it said")[0].replace("0 cell", "0 cell")]
ex2 = object.__new__(E.Executor)
ex2.blockers, ex2._cur_target, ex2.log = {}, "", (lambda *a, **k: None)
ex2._mark_now, ex2._flags_now = [0, 10, 3], []
ex2._note_sweep_refusal(R, battle)
ck("...a stop with no words (a battle) is no wall",
   ex2._sweep_skip(R, kind="wall") == [])
st = E.Executor._sweep_step(ex, R)
ck("sweeps here carry the wall", st.get("wall") == ["19,9"] and st.get("skip") == ["19,5"])
b = next(iter(ex.blockers.values()))
ck("a blocker keeps the world it was recorded in",
   b.get("mark") == [0, 10, 3] and b.get("flags_then") == ["EVENT_A"])
ck("...and says nothing while that world holds", ex._since_words(b) == "")

ex._mark_now = [0, 13, 4]
ex._flags_now = ["EVENT_A", "EVENT_GOT_OAKS_PARCEL", "EVENT_GOT_POKEDEX",
                 "EVENT_OAK_GOT_PARCEL"]
w = ex._since_words(b)
ck("once it moves, the row says what has happened since",
   "SINCE IT TURNED YOU BACK: 3 event(s) have fired" in w
   and "EVENT_GOT_POKEDEX" in w and "may answer differently now" in w, w)
ck("...and the walls and skips no longer apply",
   ex._sweep_skip(R) == [] and ex._sweep_skip(R, kind="wall") == []
   and "wall" not in E.Executor._sweep_step(ex, R))
ck("the page's rows carry it", "line += self._since_words(b)" in
   (ROOT / "planner/executor.py").read_text())
ck("the author's rows too", "SINCE IT TURNED YOU BACK {len(_new)} event(s)" in
   (ROOT / "planner/author.py").read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

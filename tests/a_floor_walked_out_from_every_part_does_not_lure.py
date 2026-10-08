#!/usr/bin/env python3
"""A floor whose every part the run has stood in was walked to its edge does
not offer its unseen ground as the way anywhere.

The floor's count of spots where the seen ground ends (frontier_map_n) is
the whole map's, so ground no walk from any walked part reaches still
counts. Mt Moon B2F, run 38 (2026-10-08): all three parts had
frontier_here 0, each part's own page said everything reachable was done,
and the floor line on the same page said "This floor still has ground never
on screen (31 spot(s) ...), and the way to them may run through it". The
model quoted the 31 back ("the only remaining places the Moon Stone could
be") and hunted the floor across two legs (user: "it should know that
theres no item balls left in b2f since its explored all the reachable
ground"). Executor._floor_walked_out(map) is true only when every part of
the map the run stood in is _unseen_there's "done"; both floor lines then
say no walk from any of them reaches that ground.
"""
from __future__ import annotations
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                      # noqa: E402

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

N, M, S = "MT_MOON_B2F|20,5", "MT_MOON_B2F|27,5", "MT_MOON_B2F|23,21"
def ex(fh=None, visits=None, mark_now=(1, 3, 9)):
    fh = {N: 0, M: 0, S: 0} if fh is None else fh
    visits = {N: 9, M: 4, S: 6, "MT_MOON_B1F|20,2": 3} if visits is None else visits
    o = types.SimpleNamespace(
        region_seen={N: 10, M: 6, S: 6}, frontier_here=fh, visits=visits,
        _region_mark={r: [1, 3, 9] for r in (N, M, S)}, _mark_now=list(mark_now))
    o._unseen_there = types.MethodType(E.Executor._unseen_there, o)
    o._water_unseen = lambda r: 0
    o._floor_walked_out = types.MethodType(E.Executor._floor_walked_out, o)
    return o

ck("every part stood in and walked to its edge: the floor is walked out",
   ex()._floor_walked_out("MT_MOON_B2F"))
ck("...not when one part still had reachable frontier",
   not ex(fh={N: 0, M: 2, S: 0})._floor_walked_out("MT_MOON_B2F"))
ck("...not when the world mark moved since (one more look is allowed)",
   not ex(mark_now=(2, 3, 9))._floor_walked_out("MT_MOON_B2F"))
ck("...a part never stood in does not count against it, nor for it",
   ex(visits={N: 9, M: 4})._floor_walked_out("MT_MOON_B2F"))
ck("...a map never stood on is not walked out",
   not ex()._floor_walked_out("MT_MOON_1F"))
ck("...nor a map with no id", not ex()._floor_walked_out(None))

lsrc = (ROOT / "planner/ledger.py").read_text()
esrc = (ROOT / "planner/executor.py").read_text()
ck("the ledger floor line reads it before offering the unseen ground",
   'ex._floor_walked_out(m.get("id"))' in lsrc
   and '"walked to its edge: no walk from any of them "' in lsrc)
ck("the executor doorway line reads it too",
   "self._floor_walked_out(" in esrc
   and '"part of it you have stood in was walked to its edge: no "' in esrc)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

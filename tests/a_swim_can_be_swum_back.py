#!/usr/bin/env python3
"""The reverse of a walk made on the water is offered as an inference.

A walk inside a map is not reversed: a ledge hopped down is not hopped
up. Water has no ledges. Seafoam B3F's row-11 swim was walked once, west to
east, on the way to Cinnabar; with no way back on record `go` could not
reach Fuchsia from the island side, the HM04 leg was passed over, and the
run came round to the same water for it again (run 36, 2026-10-05). On that
run's memory the route from Route 20's west landing to Fuchsia is 11 legs
with the swim back; before, none. Behavioural on a small graph.
"""
import os, sys, tempfile
os.environ["RED_BRIDGE_DIR"] = tempfile.mkdtemp()
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

ex = E.Executor.__new__(E.Executor)
ex.log = lambda *a, **k: None
ex._bad_seam = set()
W, X = "SEAFOAM_ISLANDS_B3F|1,0", "SEAFOAM_ISLANDS_B3F|21,6"
ex.explored = {W: {f"walk:{X}": {"n": 1, "to": X, "intra": True, "surf": True}},
               X: {"25,14": {"n": 1, "to": "SEAFOAM_ISLANDS_B2F|23,10"}}}
checks = []
def ck(n, ok): checks.append((n, bool(ok)))
back = ex._edges_of(X).get(f"walk:{W}")
ck("a swim's reverse is offered", bool(back) and back.get("to") == W)
ck("...as an inference, ridden on replay",
   bool(back) and back.get("inferred") and back.get("surf"))
ex.explored[W][f"walk:{X}"].pop("surf")
ck("a walk on foot (a ledge may be in it) is still not reversed",
   f"walk:{W}" not in ex._edges_of(X))
ex.explored[W][f"walk:{X}"]["surf"] = True
ex._bad_seam = {(X, f"walk:{W}", W)}
ck("a swim back the world refused (a current) is not offered again",
   f"walk:{W}" not in ex._edges_of(X))
src = (ROOT / "planner/executor.py").read_text()
ck("a replayed hop reads the inferred edge's surf flag too",
   "or self._edges_of(self._where(_now)).get(str(key)))" in src)
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)

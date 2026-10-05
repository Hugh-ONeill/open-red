#!/usr/bin/env python3
"""A door a sweep stepped through, with no op naming it, is recorded.

Run 36 (2026-10-05): explore's sweep walked onto Route 2's doorway into
the Viridian Forest south gate; no op named the door, the executor logged
crossed_door_unnamed, the gate's way back was inferred on arrival and
Route 2's way in was never written, so `go` had no road north out of
Viridian. The shim's steps.log had the door cell (3,43). Behavioural, on
that log's real lines; a scripted ride (no door under the last cell) is
still not recorded.
"""
import os, sys, tempfile
from pathlib import Path
d = tempfile.mkdtemp(); os.environ["RED_BRIDGE_DIR"] = d
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

def run(lines, warps):
    (Path(d) / "steps.log").write_text("".join(l + "\n" for l in lines))
    ex = E.Executor.__new__(E.Executor)
    ex.log = lambda *a, **k: None
    ex._save_memory = lambda: None
    before = {"mode": "overworld", "player": {"x": 3, "y": 44},
              "map": {"id": "ROUTE_2", "region": "3,43", "warps": warps}}
    after = {"mode": "overworld", "player": {"x": 4, "y": 7},
             "map": {"id": "VIRIDIAN_FOREST_SOUTH_GATE", "region": "5,0", "warps": []}}
    for _ in range(60):
        try:
            ex.note_transition(before, {"op": "sweep"}, after, reason="",
                               op_detail="sweep stopped")
            break
        except AttributeError as e:
            n = str(e).split("attribute '")[1].rstrip("'")
            setattr(ex, n, {} if not n.startswith("_mark") else None)
    return (getattr(ex, "explored", {}) or {}).get("ROUTE_2|3,43") or {}

checks = []
def ck(n, ok, det=""): checks.append((n, bool(ok), det))
got = run(["1791041815 ROUTE_2 3 44", "1791041815 ROUTE_2 3 43",
           "1791041815 VIRIDIAN_FOREST_SOUTH_GATE 4 7"],
          [{"x": 3, "y": 43}, {"x": 15, "y": 39}])
ck("the door the sweep stepped through is recorded under its own tile",
   (got.get("3,43") or {}).get("to") == "VIRIDIAN_FOREST_SOUTH_GATE|5,0", got)
got2 = run(["1791041815 ROUTE_2 5 30",
            "1791041815 VIRIDIAN_FOREST_SOUTH_GATE 4 7"],
           [{"x": 3, "y": 43}])
ck("a landing not from a door tile (a scripted ride) records no way",
   not any(isinstance(v, dict) and v.get("to") == "VIRIDIAN_FOREST_SOUTH_GATE|5,0"
           for v in got2.values()), got2)
bad = [c for c in checks if not c[1]]
for n, ok, det in checks: print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"  {det}"))
raise SystemExit(1 if bad else 0)

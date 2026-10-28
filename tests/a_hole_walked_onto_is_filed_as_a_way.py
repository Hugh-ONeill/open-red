#!/usr/bin/env python3
"""A drop taken by walking onto a hole is filed as a way, not thrown out as
a door the room does not have.

Run 67, 2026-10-28: walk_to (17,6) on Seafoam 1F dropped the party to B1F;
the fall was found and keyed ("transition_by_fall"), then the foreign-door
check refused it for not being one of the floor's warps
("edge_key_foreign"), so no hole drop taken by a walk was ever filed and
`go` from 1F's west half had no way to Cinnabar on the road the run had
crossed by (user: "shouldnt it just be able to 'go'?"). Behavioural; a
cell that is neither a warp nor a hole is still refused.
"""
import os, sys, tempfile
from pathlib import Path
d = tempfile.mkdtemp(); os.environ["RED_BRIDGE_DIR"] = d
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

def run(x, y):
    (Path(d) / "steps.log").write_text("")
    ex = E.Executor.__new__(E.Executor)
    ex.log = lambda *a, **k: None
    ex._save_memory = lambda: None
    before = {"mode": "overworld", "player": {"x": 17, "y": 7},
              "map": {"id": "SEAFOAM_ISLANDS_1F", "region": "3,2",
                      "warps": [{"x": 4, "y": 17}, {"x": 7, "y": 5}],
                      "holes": [{"x": 17, "y": 6, "drop": 1}]}}
    after = {"mode": "overworld", "player": {"x": 17, "y": 6},
             "map": {"id": "SEAFOAM_ISLANDS_B1F", "region": "11,0", "warps": []}}
    for _ in range(80):
        try:
            ex.note_transition(before, {"op": "walk_to", "x": x, "y": y}, after,
                               reason="", op_detail="walked")
            break
        except AttributeError as e:
            n = str(e).split("attribute '")[1].rstrip("'")
            setattr(ex, n, {} if not n.startswith("_mark") else None)
    return (getattr(ex, "explored", {}) or {}).get("SEAFOAM_ISLANDS_1F|3,2") or {}

checks = []
def ck(n, ok, det=""): checks.append((n, bool(ok), det))
got = run(17, 6)
ck("a walk onto a hole files the drop under the hole's tile",
   (got.get("17,6") or {}).get("to") == "SEAFOAM_ISLANDS_B1F|11,0", got)
got2 = run(30, 30)
ck("a cell that is neither a warp nor a hole is still refused",
   not any(isinstance(v, dict) and v.get("to") == "SEAFOAM_ISLANDS_B1F|11,0"
           for v in got2.values()), got2)
bad = [c for c in checks if not c[1]]
for n, ok, det in checks: print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"  {det}"))
raise SystemExit(1 if bad else 0)

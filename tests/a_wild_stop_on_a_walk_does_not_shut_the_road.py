#!/usr/bin/env python3
"""A walk the shim reports as a bare "interrupted (battle or script)" was cut
by the world, and does not stamp the road as not landing.

Run 67, 2026-10-28: Route 9's walk to (50,6), landed 8 times before, came
back "interrupted (battle or script)" once, was stamped blocked in that world
mark, and `go` refused the whole walked road from Route 5 to Celadon; the run
walked Cerulean -> Route 5 -> Route 9 -> Cerulean by hand.

Pinned: the bare words are a world cut; a named talker, or a stop that said
something, is still a refusal. Synthetic.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
W = E.Executor._walk_cut_by_the_world
ck("bare words, nobody named: the world cut it",
   W("interrupted (battle or script) on the way to (50,6) standing on (31,4)"))
ck("a named talker is a refusal",
   not W("interrupted (battle or script) by ROUTE22_GUARD standing on (4,3)"))
ck("a stop that said something is a refusal",
   not W('interrupted (battle or script) — it said: "Wait! You need a badge"'))
ck("the old forms still count", W("a fight started 10 cell(s) short"))
import json
d = tempfile.mkdtemp()
mem = Path(d) / "explored.json"
mem.write_text(json.dumps({"explored": {"ROUTE_9|6,2": {
    "walk:ROUTE_9|50,6": {"to": "ROUTE_9|50,6", "n": 8, "blocked_at": [6, "a", "b"],
                          "blocked_why": "interrupted (battle or script)"},
    "east": {"to": "ROUTE_10|0,0", "blocked_at": [6, "a", "b"],
             "blocked_why": "a LEDGE along 3 cells"}}}}))
ex = object.__new__(E.Executor)
ex.MEMORY, ex._harness_rev = mem, "x"
ex.log = lambda *a, **k: None
for _ in range(200):
    try:
        ex._load_memory()
        break
    except AttributeError as e:
        n = str(e).split("attribute '")[1].rstrip("'")
        setattr(ex, n, {} if not n.startswith("_mark") else None)
g = ex.explored["ROUTE_9|6,2"]
ck("a stamp written for a world cut is lifted at load",
   "blocked_at" not in g["walk:ROUTE_9|50,6"], g)
ck("...a stamp with a ground reason stays", g["east"].get("blocked_at") is not None, g)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)

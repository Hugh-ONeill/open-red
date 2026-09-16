#!/usr/bin/env python3
"""A part walked before CUT was known is not finished while a bush there has
ground past it.

Run 27, 2026-09-16: ROUTE_9|0,8 was walked before HM01, every exit taken, and
went into "Already fully worked". Its way east is the bush at (5,8), and
fully worked is judged by exits, which a bush is not. After CUT was learned
the page, standing in Cerulean, still said Route 9 had nothing left while the
run hunted a way to Celadon (user: "the only really unexplored frontier
should now be rt 9 but it hasnt taken it since learning cut").

Pinned: a reachable bush with ground past it is recorded per part; while a
party Pokemon knows CUT that part is not fully worked and it is listed with
the ways never taken; a cut bush drops off the record; a ledger from before
the record is backfilled from worked parts that sighted a bush on a map
where nothing was cut. Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


def fake():
    ex = object.__new__(E.Executor)
    ex._bush_ways, ex._knows_cut = {}, False
    ex._save_memory = lambda: None
    ex.searched = {"*": {"ROUTE_9|0,8": 1, "ROUTE_3|57,0": 1}}
    ex.explored, ex.map_doors, ex.map_seen = {}, {}, {}
    return ex


def obs(bushes, moves):
    return {"map": {"id": "ROUTE_9", "objects": [
                {"kind": "cut_tree", "name": "CUT_TREE", "x": x, "y": y,
                 "reachable": r, "opens": o} for x, y, r, o in bushes]},
            "party": [{"species": "IVYSAUR", "moves": moves}]}


ex = fake()
ex._note_bush_ways(obs([(5, 8, True, True), (9, 2, False, True),
                        (1, 1, True, None)], ["TACKLE"]), "ROUTE_9|0,8")
ck("a reachable bush with ground past it is recorded",
   ex._bush_ways == {"ROUTE_9|0,8": ["5,8"]})
ck("...but no part reopens while nobody knows CUT",
   ex._bush_way_parts() == {} and "ROUTE_9|0,8" in ex._worked_for("map:X"))
ex._note_bush_ways(obs([(5, 8, True, True)], ["CUT", "TACKLE"]), "ROUTE_9|0,8")
ck("once CUT is known the part is not fully worked",
   "ROUTE_9|0,8" not in ex._worked_for("map:X")
   and "ROUTE_3|57,0" in ex._worked_for("map:X"))
ex._note_bush_ways(obs([], ["CUT"]), "ROUTE_9|0,8")
ck("a felled bush drops off the record",
   ex._bush_ways == {} and "ROUTE_9|0,8" in ex._worked_for("map:X"))

src = (ROOT / "planner/executor.py").read_text()
ck("the ways-never-taken list walks the bush parts too",
   "list(held) + list(bushes)" in src
   and "with ground past it no walk there reaches" in src)
ck("the record is saved", '"bush_ways": getattr(self, "_bush_ways", {})' in src)

# the row for a way onto that part says the bush, not "never pressed"
import ledger as L  # noqa: E402
ex = fake()
ex._knows_cut = True
ex._bush_ways = {"ROUTE_9|0,8": ["5,8"]}
ex.sightings = {"ROUTE_9|0,8": ["CUT_TREE"]}
ex._frontier_left = lambda r: []
ex._touched_on_map = lambda r: set()
ex._gone, ex.region_seen, ex.unreached_at = {}, {}, {}
ex._taken_here = lambda r: {}
row = L._left_parts(ex, "ROUTE_9|0,8")
ck("the row for the way onto it names the bush and CUT",
   any("bush at (5,8)" in p and "knows CUT" in p for p in row))
ck("...and does not call the bush a thing never pressed",
   not any("never pressed" in p for p in row))
ex._knows_cut = False
ck("without CUT the row is as it was",
   any("never pressed (CUT_TREE)" in p for p in L._left_parts(ex, "ROUTE_9|0,8")))

# backfill from a ledger written before the record existed
with tempfile.TemporaryDirectory() as d:
    mem = Path(d) / "explored.json"
    mem.write_text(json.dumps({
        "sightings": {"ROUTE_9|0,8": ["CUT_TREE"],
                      "VERMILION_CITY|18,0": ["CUT_TREE"],
                      "PEWTER_CITY|4,2": ["CUT_TREE"]},
        "searched": {"*": {"ROUTE_9|0,8": 1, "VERMILION_CITY|18,0": 1}},
        "cut_bushes": {"VERMILION_CITY": ["15,18"]}}))
    ex = object.__new__(E.Executor)
    ex.MEMORY, ex._harness_rev = mem, "x"
    ex.log = lambda *a, **k: None
    for _ in range(60):
        try:
            ex._load_memory()
            break
        except AttributeError as e:
            setattr(ex, str(e).split("'")[-2], {})
    ck("an old ledger backfills worked parts that saw a bush, on maps never cut",
       ex._bush_ways == {"ROUTE_9|0,8": ["?"]})

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

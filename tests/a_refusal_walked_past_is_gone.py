#!/usr/bin/env python3
"""A script's refusal on the way to a map is one row, and it goes once the
run walks on from that part onto that map.

Run 58 (2026-10-17): Viridian's old man ("You can't go through here! This is
private property!") turned the run back heading for ROUTE_2, written as two
rows, a cell and a sweep wall, from one refusal. After the parcel the run
crossed north from the same part onto Route 2, and both rows still read
"turned you back 1x" in Cerulean (user: "the viridian blockers should only
have one, and they should both be gone because weve gotten past them").

Synthetic, plus a source check for the hook.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(name, ok, d=""): checks.append((name, bool(ok), d))

SAID = 'a script turned you back on the way there said "You can\'t go through here! This is private property!"'

def fresh():
    x = object.__new__(E.Executor)
    x.blockers = {
        "VIRIDIAN_CITY|17,0|19,5": {"where": "VIRIDIAN_CITY|17,0", "key": "19,5", "kind": "cell",
                                    "n": 1, "what": SAID, "cleared": False, "last": "map:ROUTE_2"},
        "VIRIDIAN_CITY|17,0|19,9": {"where": "VIRIDIAN_CITY|17,0", "key": "19,9", "kind": "wall",
                                    "n": 1, "what": "a sweep was stopped standing here — " + SAID,
                                    "cleared": False, "last": "map:ROUTE_2", "of": "19,5"},
        "CERULEAN_CITY|20,0|east": {"where": "CERULEAN_CITY|20,0", "key": "east", "kind": "seam",
                                    "n": 3, "what": "the walk was fenced — X", "cleared": False,
                                    "last": "map:ROUTE_9"},
        "VIRIDIAN_CITY|17,0|25,9": {"where": "VIRIDIAN_CITY|17,0", "key": "25,9", "kind": "cell",
                                    "n": 1, "what": "a script turned you back", "cleared": False,
                                    "last": "map:VIRIDIAN_GYM"},
    }
    x.log = lambda *a, **k: None
    return x

x = fresh()
x._clear_headed_for("VIRIDIAN_CITY|17,0", "ROUTE_2|3,43")
b = x.blockers
ck("walking on from that part onto the map it was headed for clears the refusal",
   b["VIRIDIAN_CITY|17,0|19,5"]["cleared"], b["VIRIDIAN_CITY|17,0|19,5"])
ck("...and its sweep wall goes with it", b["VIRIDIAN_CITY|17,0|19,9"]["cleared"])
ck("...and says why", "ROUTE_2" in b["VIRIDIAN_CITY|17,0|19,5"].get("cleared_how", ""))
ck("a refusal on the way somewhere else stays", not b["VIRIDIAN_CITY|17,0|25,9"]["cleared"])
ck("a seam elsewhere is untouched", not b["CERULEAN_CITY|20,0|east"]["cleared"])
x = fresh()
x._clear_headed_for("VIRIDIAN_CITY|3,3", "ROUTE_2|3,43")
ck("from another part of the map: nothing cleared",
   not any(v["cleared"] for v in x.blockers.values()))
x = fresh()
x._sweep_blockers = lambda obs: None
x._where = lambda o: "CERULEAN_CITY|20,0"
x._route = lambda a, b: [1]
x._since_words = lambda b: ""
x._named_needs_words = lambda b: ""
t = x.blockers_text({"map": {"id": "CERULEAN_CITY"}}, cap=9)
ck("one refusal is one row on the page", t.count("private property") == 1, t)
src = (ROOT / "planner" / "executor.py").read_text()
ck("the edge recorder asks it on every crossing",
   'self._clear_blocker(src, k, f"it opened — you came out at {dst}")\n'
   '            self._clear_headed_for(src, dst)' in src)
ck("the sweep wall is tagged with its cell", '_wb["of"] = key' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

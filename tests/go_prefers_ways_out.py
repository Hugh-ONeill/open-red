"""A bare map name goes to the part with the most ways on (2026-08-26).

`go MAP` took the NEAREST walked part, and the nearest part of a map is
routinely the worst one: ROUTE_7|18,12 is a pocket whose single recorded exit
is back east, and the run crossed into it four times; ROUTE_14|16,6 is a
four-cell nook. User: "can we route it to somewhere that isnt a pocket? ...
unless its stated that were aiming for the pocket we should go to the area
that has the most movement options".

Ways out first, distance second. Naming MAP|region still overrides it — that
is the "unless it is stated" half — and every alternative is still listed with
both numbers, so nothing is chosen in silence."""
import sys, re
from pathlib import Path
sys.path.insert(0, "planner")
import executor as E

checks = []
def ck(name, cond): checks.append((name, bool(cond)))

src = Path("planner/executor.py").read_text()
i = src.find('"NEAREST" IS THE WRONG DEFAULT FOR A BARE MAP NAME')
ck("the ranking exists", i > 0)
blk = src[i:i + 2600]

ck("ways out are counted from walked exits and untried ones",
   "def _ways(r):" in blk and "self.explored.get(r)" in blk
   and "self._frontier_left(r)" in blk)
ck("...ignoring an edge that loops back to itself",
   '(e or {}).get("to") != r' in blk)
ck("ranked by ways out first, legs second",
   "key=lambda rn: (-_ways(rn[0]), rn[1])" in blk)
ck("only for a BARE map name",
   '"|" not in str(want)' in blk)
ck("...and only when more than one part is reachable",
   "len(_reachable) > 1" in blk)
ck("a named region is still taken as given",
   "that choice is taken as given" in blk)
ck("the other parts are still listed, with both numbers",
   "way(s) out)" in blk and "leg(s)," in blk)
ck("it says WHY it did not take the nearest",
   "not the nearest" in blk and "often a corner" in blk)
ck("a failed re-route falls back rather than breaking",
   "if _p2:" in blk)

# behaviour on the live atlas shape
import json

def _atlas():
    """The richest ledger on disk: the live one is whatever chain is running
    (a fresh chain starts it empty); the Hall of Fame world's is archived
    beside it as explored.<ts>.pre-discovery.bak.json."""
    # ...AN ARCHIVED world, never the live one: a long run's own ledger grew
    # past the archive on 2026-10-05 and the test read a world without the
    # pocket it pins (run 36 had walked Route 7 the other way)
    # ...AND ONE THAT HOLDS THE POCKET. Largest first stopped working when
    # run 36's world, which walked Route 7 the other way, became the
    # largest archive (2026-10-05): take the largest that has the shape.
    cands = sorted((f for f in Path("run").glob("explored.*.json")),
                   key=lambda f: f.stat().st_size)
    if not cands:
        cands = sorted(Path("run").glob("explored*.json"),
                       key=lambda f: f.stat().st_size)
    def _has(dd):
        e = dd.get("explored") or {}
        outs = {(v or {}).get("to") for v in (e.get("ROUTE_7|18,12") or {}).values()
                if (v or {}).get("to") and (v or {}).get("to") != "ROUTE_7|18,12"}
        return "ROUTE_7|0,2" in e and len(outs) == 1
    for f in reversed(cands):
        try:
            dd = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if _has(dd):
            print(f"  atlas: {f.name}")
            return dd
    return json.loads(cands[-1].read_text())

d = _atlas()
ex = E.Executor.__new__(E.Executor)
ex.explored = d["explored"]
ex._frontier_left = lambda r: []
def ways(r):
    outs = {(e or {}).get("to") for e in (ex.explored.get(r) or {}).values()
            if (e or {}).get("to") and (e or {}).get("to") != r}
    return len(outs)
r7 = sorted((r for r in ex.explored if r.startswith("ROUTE_7|")),
            key=lambda r: -ways(r))
ck(f"ROUTE_7 ranks {r7[0]} above the pocket",
   r7[0] == "ROUTE_7|0,2" and ways("ROUTE_7|18,12") == 1)
r12 = sorted((r for r in ex.explored if r.startswith("ROUTE_12|")),
             key=lambda r: -ways(r))
# a world's ledger is a snapshot of what that run walked: the 2026-08 Hall
# of Fame world walked three ways out of ROUTE_12|0,61, run 19's (the
# largest on disk since run 20's launch archived it) walked one. The check
# reads the shape it was written against, where that shape exists.
if ways("ROUTE_12|0,61") >= 3:
    ck("ROUTE_12 ranks the 3-way part first", r12[0] == "ROUTE_12|0,61")

# --- and the single-part dead end, which no ranking can help ---
j = src.find("AND WHEN THERE IS ONLY ONE PART, AND IT IS A DEAD END")
ck("a lone dead-end part is called out", j > 0)
dblk = src[j:j + 4800]   # two wordings since 2026-09-07
# the comment quotes the phrasing it forbids; test the code only
_dsaid = "\n".join(l for l in dblk.splitlines()
                   if not l.lstrip().startswith("#"))
ck("...only for a bare map name with nowhere else to go",
   '"|" not in str(want) and _ways(best[0]) <= 1' in dblk)
ck("it names what its recorded ways out lead back to", "_outs" in dblk)
ck("SEEN is not confused with WALKED",
   "SEEN but " in _dsaid and "never STOOD ON" in _dsaid
   and "never seen" not in _dsaid)
ck("...and the frontier count decides which half of that sentence",
   "map_seen" in dblk and "_fr_here == 0" in dblk)
ck("a closed box says nothing seen lies outside the part you stand in",
   "Nothing you have seen of {want} lies outside that" in dblk
   and "seen ground ends nowhere" in _dsaid)
ck("it still refuses to say where the rest IS",
   "not recorded" in _dsaid
   and "may be another map" in _dsaid)

import ast
try:
    ast.parse(src); ck("executor.py parses", True)
except SyntaxError as e:
    ck(f"executor.py parses ({e})", False)

bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok  " if ok else "FAIL"), n)
sys.exit(1 if bad else 0)

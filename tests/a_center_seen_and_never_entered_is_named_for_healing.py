#!/usr/bin/env python3
"""The heal line names a doorway in a building with POKé written across its
face that the run has seen and never walked into, by walked legs.

Run 63, 2026-10-24: grinding on Mt Moon 1F, the line listed only Centers
walked into ("VIRIDIAN_POKECENTER (10 leg(s))"), and the run walked ten legs
back to Viridian to heal, twice, with such a doorway at the cave's mouth on
Route 4 that the page itself had described ("a small flat-roofed building
with POKé written across its face").

Pinned: a recorded POKé-faced doorway, not walked through and reachable,
is named by where it stands, never by where it leads; once walked through
it is not, by either tile of its doorway; observing a map records each
such building once.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

MM, R4, VC = "MT_MOON_1F|3,2", "ROUTE_4|10,0", "VIRIDIAN_POKECENTER|0,3"


def line(walked_through=False):
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {MM: {"14,35": {"to": R4, "n": 2}},
                   R4: {"18,5": {"to": MM, "n": 2},
                        **({"11,5": {"to": "MT_MOON_POKECENTER|0,3", "n": 1}} if walked_through else {})},
                   VC: {}}
    ex.visits = {MM: 3, R4: 2, VC: 4}
    ex.sightings = {}
    ex._bad_seam = set()
    ex._mark_now = None
    ex.center_doors = {"ROUTE_4": {"11,5;12,5": R4}}
    ex._where = lambda o: MM
    obs = {"respawn": {"map": "VIRIDIAN_POKECENTER"}, "map": {"id": "MT_MOON_1F"}}
    return ex._respawn_line(obs)


t = line()
ck("a POKé-faced doorway seen and never entered is named, by legs",
   "the building with POKé written across its face at (11,5) on ROUTE_4, seen and "
   "never walked into (1 leg(s))" in t, t)
ck("...never by where it leads", "MT_MOON_POKECENTER" not in t, t)
ck("...one row a map", t.count("on ROUTE_4") == 1, t)
ck("once walked through it is not", "seen and never walked into" not in line(True), line(True))

src = (ROOT / "planner" / "executor.py").read_text()
ck("observing a map records such doorways",
   '"POKé written across its face" in str(_b.get("look") or "")' in src
   and '_cd.setdefault(";".join(sorted(str(_dk) for _dk in _b["doors"])), here)' in src)

# one list, nearest first: a seen Center 1 leg away comes before a walked one 8 away
ex = E.Executor.__new__(E.Executor)
ex.explored = {"ROUTE_3|0,0": {"west": {"to": "PEWTER_CITY|4,2", "n": 2}},
               "PEWTER_CITY|4,2": {"south": {"to": "ROUTE_2|8,0", "n": 2}},
               "ROUTE_2|8,0": {"south": {"to": "VIRIDIAN_POKECENTER|0,3", "n": 1}}}
ex.visits = {"ROUTE_3|0,0": 1, "PEWTER_CITY|4,2": 2, "ROUTE_2|8,0": 2, "VIRIDIAN_POKECENTER|0,3": 3}
ex.sightings, ex._bad_seam, ex._mark_now = {}, set(), None
ex.center_doors = {"PEWTER_CITY": {"13,25": "PEWTER_CITY|4,2"}}
ex._where = lambda o: "ROUTE_3|0,0"
t2 = ex._respawn_line({"respawn": {"map": "VIRIDIAN_POKECENTER"}, "map": {"id": "ROUTE_3"}})
ck("one list, nearest first: the seen Center 1 leg away leads",
   "nearest first over walked ground: the building with POKé" in t2
   and t2.index("PEWTER_CITY") < t2.index("VIRIDIAN_POKECENTER (3 leg"), t2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

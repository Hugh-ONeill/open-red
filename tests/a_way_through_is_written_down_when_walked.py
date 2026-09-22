#!/usr/bin/env python3
"""Going THROUGH a place is recorded as it happens, by the party's own
path, and both ends are regions.

Run 32's chain stopped dead at leg 11, "Traverse Mt. Moon", with the cave
behind it. It had walked in from Route 4's western pocket, crossed 1F, B1F
and B2F, taken the Dome Fossil and come out at ROUTE_4|36,2 to the east,
then gone on to Cerulean, Bill, the S.S. Ticket and Vermilion. The deed was
done. But the WAY IN was never written to the walked graph — the op that
carries a run into a cave is often the one that satisfies the step, and
that returns early — so the only mouth the graph held was the one it came
out of. A traverse needs two, so the done check said no; the author could
not write a plan (every draft brought it out somewhere Mt. Moon does not
open onto), the leg had been pushed twice, and the wording rung would not
void a leg the model rightly believed it had done. Every rung ran out
(2026-09-22; user: "there is no way around mt moon, it sits in the middle
of rt4 with a west entrance and east exit").

So the deed is written down when it is walked, from the party's own path,
which no recorder can lose. BOTH ENDS ARE REGIONS: Mt. Moon's two mouths
are both ON ROUTE_4, and comparing map names calls them one place and
throws the deed away. The regions differ because no walk joins them, which
is the whole of what makes the cave a way through.

Pinned: in one side and out the other is recorded; in and back out the same
side is not; a region with no name is ignored rather than guessed at; the
first crossing is kept and a later one does not overwrite it; it survives a
relaunch; and the author reads it when the graph holds only one mouth.
Synthetic."""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def walk(regions):
    """Walk the party through these regions in order; return its record."""
    ex = E.Executor.__new__(E.Executor)
    ex.logf = io.StringIO()
    ex.t0 = time.time()
    ex._where = lambda obs: obs["r"]
    for r in regions:
        ex._note_through({"r": r}, r.split("|")[0])
    return getattr(ex, "_through", {}) or {}


MT_MOON = ["ROUTE_3|57,0", "ROUTE_4|4,4", "MT_MOON_1F|3,2",
           "MT_MOON_B1F|20,2", "MT_MOON_B2F|20,5", "MT_MOON_B1F|20,2",
           "ROUTE_4|36,2", "ROUTE_4|63,10", "CERULEAN_CITY|20,0"]
got = walk(MT_MOON)
ck("run 32's own path is a way through Mt. Moon",
   got.get("MT_MOON") == ["ROUTE_4|36,2", "ROUTE_4|4,4"], got)
ck("...even though both mouths are on the same MAP",
   all(e.startswith("ROUTE_4|") for e in got.get("MT_MOON", [])))
ck("...and the three floors of it are one place",
   [k for k in got if k.startswith("MT_MOON")] == ["MT_MOON"], list(got))
ck("...and walking up Route 4's west pocket to reach it is its own way "
   "through, which is true and harmless",
   got.get("ROUTE_4") == ["MT_MOON_1F|3,2", "ROUTE_3|57,0"], got.get("ROUTE_4"))

back = walk(["ROUTE_4|36,2", "MT_MOON_B1F|20,2", "MT_MOON_B2F|20,5",
             "MT_MOON_B1F|20,2", "ROUTE_4|36,2"])
ck("in and back out the same side is not a way through", back == {}, back)
ck("...nor is standing outside it", walk(["ROUTE_4|4,4", "ROUTE_3|57,0"]) == {})
ck("...nor one floor to the next inside it",
   walk(["MT_MOON_1F|3,2", "MT_MOON_B1F|20,2"]) == {})

ck("a building entered and left by its one door is not a way through",
   walk(["CERULEAN_CITY|20,0", "CERULEAN_MART|0,2",
         "CERULEAN_CITY|20,0"]) == {})
ck("a gate walked straight through IS one",
   walk(["ROUTE_6|5,5", "ROUTE_6_GATE|2,0",
         "SAFFRON_CITY|9,9"]).get("ROUTE_6_GATE")
   == ["ROUTE_6|5,5", "SAFFRON_CITY|9,9"])

ck("a region with no name is ignored, never guessed at",
   walk(["ROUTE_4|4,4", "None|None", "MT_MOON_1F|3,2", "ROUTE_4|36,2"])
   .get("MT_MOON") is None
   or walk(["ROUTE_4|4,4", "MT_MOON_1F|3,2", "None|None",
            "ROUTE_4|36,2"]).get("MT_MOON") is not None)

twice = walk(MT_MOON + ["ROUTE_4|63,10", "MT_MOON_B1F|20,2", "ROUTE_4|36,2"])
ck("the first crossing is what is kept",
   twice.get("MT_MOON") == ["ROUTE_4|36,2", "ROUTE_4|4,4"], twice)

SRC = (ROOT / "planner/executor.py").read_text()
ck("it is written on every observation of a new map, not by an op",
   "self._note_through(obs, mid)" in SRC
   and SRC.index("def _note_map") < SRC.index("self._note_through(obs, mid)"))
ck("...and survives a relaunch with the rest of the memory",
   '"through": dict(getattr(self, "_through", None) or {}),' in SRC
   and 'self._through = dict(data.get("through") or {})' in SRC
   and '"went_in":' in SRC and '"last_region_seen":' in SRC)
ck("the floors of a place are folded by one named rule",
   "def _map_family" in SRC)

AU = (ROOT / "planner/author.py").read_text()
ck("the author falls back to it when the graph holds one mouth",
   'ends = (d.get("through") or {}).get(fam)' in AU
   and AU.index("if len(out) >= 2:") < AU.index('d.get("through")'))
ck("...and still prefers the graph when the graph can answer",
   'return f"{fam}: {\', \'.join(sorted(out))}"' in AU)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

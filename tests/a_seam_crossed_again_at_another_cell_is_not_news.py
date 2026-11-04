#!/usr/bin/env python3
"""A seam crossed again at another cell is not a way taken for the first
time when it lands where that seam already led.

Run 71, 2026-11-02, travel_to_celadon_city r14-r19: crossing Cerulean's
north seam at (21,0) after (20,0) filed "north#skip1", landed in the same
part of Route 24, and the round read "1 way(s) taken for the first time" and
was given free. A seam is a row; the cell matters only when it lands
somewhere else.

Pinned: the same seam to the same part is not news; to a different part it
is; a new door is news. Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex.explored = {"CERULEAN_CITY|20,0": {"north": {"n": 3, "to": "ROUTE_24|4,4"}}}
ex._tried_objs = {}
o = {"map": {"id": "CERULEAN_CITY", "seen": {"n": 500}}}
before = ex._news_snapshot(o)

ex.explored["CERULEAN_CITY|20,0"]["north#skip1"] = {"n": 1, "to": "ROUTE_24|4,4"}
got = ex._round_news(before, o)
ck("the same seam at another cell, to the same part, is not news", got == "", got)

ex.explored["CERULEAN_CITY|20,0"]["north#skip2"] = {"n": 1, "to": "ROUTE_24|17,4"}
got = ex._round_news(before, o)
ck("...to a different part it is", "1 way(s) taken for the first time" in got, got)

ex.explored["CERULEAN_CITY|20,0"]["19,17"] = {"n": 1, "to": "CERULEAN_POKECENTER|0,3"}
got = ex._round_news(before, o)
ck("a new door is news", "2 way(s) taken for the first time" in got, got)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

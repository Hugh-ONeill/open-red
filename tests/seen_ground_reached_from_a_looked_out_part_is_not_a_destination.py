#!/usr/bin/env python3
"""Seen ground another part reaches is an explore destination only while
that part may still show something new.

Run 62, 2026-10-24: on Mansion 2F each part "reached" the other parts' seen
floor (shim seen_unreached.from), b24804b's rule made that an explore
destination, and the page read "explore walks there to sweep — 47 spot(s)
where its seen ground ends" of 2F|6,1, whose own frontier was 0. The run
went round 2F's three parts in turn, sweeping nothing, while the basement's
unseen corner held the Secret Key.

Pinned: with the far part stood in and its frontier 0, explore does not
offer it for the reached ground; with frontier left, or none recorded, it
still does (b24804b's Cerulean corridor); the executor's picker applies the
same gate.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import candidates as C  # noqa: E402
import ledger as L  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

M = "POKEMON_MANSION_2F"
HERE, FAR, UP = M + "|24,9", M + "|6,1", "POKEMON_MANSION_3F|1,1"


def words(frontier_here):
    ex = C.make()
    ex.explored = {HERE: {"25,14": {"to": UP, "n": 3}},
                   UP: {"6,1": {"to": FAR, "n": 4}, "25,14": {"to": HERE, "n": 3}},
                   FAR: {"6,1": {"to": UP, "n": 4}}}
    ex.visits = {HERE: 3, FAR: 4, UP: 5}
    ex.frontier, ex.region_seen = {}, {}
    ex.frontier_here = {} if frontier_here is None else {FAR: frontier_here}
    ex._where = lambda o: HERE
    obs = {"mode": "overworld", "party": [],
           "map": {"id": M, "region": "24,9", "warps": [], "objects": [],
                   "seen_unreached": {"n": 47, "from": [{"region": FAR, "n": 47}]}}}
    return L._plan_explore_words(ex, obs, cands=[])


w0 = words(0)
ck("a part looked out from in full is not offered for reached seen ground",
   FAR not in w0, w0)
w5 = words(5)
ck("...one with frontier left still is", FAR in w5, w5)
wn = words(None)
ck("...and one never measured still is", FAR in wn, wn)
src = (ROOT / "planner" / "executor.py").read_text()
ck("the executor's picker applies the same gate",
   "_rf = _reach_from.get(region, 0)" in src
   and 'if _rf and int((getattr(self, "frontier_here", None) or {})' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A seam is a row, and each cell of it a walk reaches is a way of its own.

Run 27, 2026-09-17, the Route 14 pocket: Route 13's west edge is open at
rows 6, 8 and 10; the plain cross took row 6 every time and landed in the
one-cell strip a Bird Keeper plugs; the page showed the edge as ONE way,
"walk west -> ROUTE_14|16,6 — taken 14x", so with the trainer pressed
nothing on either side read as untried (user: "we've hit the infamous rt14
pocket"). The skip/uncork/re-cross family all key off the model's own
cross, which it never sent westward; and the re-cross that did fire tried
the seam behind it, whose every cell lands back on the same part.

Pinned: the shim lists each seen edge's reachable cells in the order `skip`
counts them; those cells join the frontier under the key a skip crossing
records (dir#skipN); the ledger gives each its own row with the cross op
and marks the plain row's cell; explore turns such a row into a cross with
its skip; the target re-cross stands down when the part behind is a
pocket. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger as L    # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
ck("the seam search can collect every cell in skip order",
   "bfs_to_edge = function(G, dir, skip, surf, blind, collect)" in shim
   and "if collect then collect[#collect + 1] = { x = x, y = y }; return nil end" in shim
   and "if collect then return collect end" in shim)
ck("...and the observation lists them per seen side",
   "o.map.seam_cells = {}" in shim
   and "pcall(bfs_to_edge, G, _dirword[d], 0, nil, nil, cells)" in shim
   and "local bfs_to_edge           -- assigned with the cross op" in shim)

ck("a seam key with a skip becomes a cross with that skip",
   E.Executor._cross_step_for("west#skip2") == {"op": "cross", "dir": "west", "skip": 2}
   and E.Executor._cross_step_for("west") == {"op": "cross", "dir": "west"}
   and E.Executor._cross_step_for("south#alt") == {"op": "cross", "dir": "south"})
src = (ROOT / "planner/executor.py").read_text()
ck("the other cells join the frontier under dir#skipN",
   'keys += [f"{_d}#skip{i}" for i in range(1, min(len(_cells), 6))]' in src)
ck("explore takes such a row with its skip, at home and away",
   src.count("self._cross_step_for(c.key) if c.kind == \"seam\"") == 2)
rc = src[src.index("    def _recross_for_target"):]
rc = rc[:rc.index("\n    def ", 10)]
ck("the target re-cross stands down when the part behind is a pocket",
   "if self._is_pocket(_from, here):" in rc and '"recross_declined"' in rc)

HERE = "ROUTE_13|50,0"


class _Ex:
    frontier = {}
    _inert_objs = {}

    def __init__(self, taken):
        self._t = taken
        self.explored = {HERE: dict(taken)}
        self.visits = {HERE: 14}
        self.hints = {}
        self.hints_at = {}
    def _where(self, _o): return HERE
    def _taken_here(self, h): return dict(self._t)
    def _spent_exits(self, h): return {}
    def _sealed(self, h): return set()
    def _untaken(self, m, t): return set()
    def _worth_another_word(self, h, o, backfill=True): return []
    def _door_groups(self, w): return {}
    def _frontage(self, d): return ""
    def _seen_cells_words(self, h): return ""
    def _walked_dest(self, mid, key):
        v = self._t.get(key)
        return v.get("to") if v else None
    def _snapshot_anywhere(self, o): return None
    def _frontier_left(self, r): return set()
    def dead_for(self, t, r): return 0
    def __getattr__(self, _n): return {}


def obs():
    return {"party": [], "mode": "overworld", "player": {"x": 10, "y": 6},
            "map": {"id": "ROUTE_13", "region": "50,0", "objects": [], "warps": [],
                    "connections": {"west": "ROUTE_14", "north": "ROUTE_12"},
                    "connections_reach": {"west": True, "north": True},
                    "seam_cells": {"west": ["0,6", "0,8", "0,10"], "north": ["50,0"]}}}


TAKEN = {"west": {"n": 14, "to": "ROUTE_14|16,6"}, "north": {"n": 1, "to": "ROUTE_12|0,61"}}
cands = L.build(_Ex(TAKEN), obs(), "map:ROUTE_15", outcomes={})
by = {c.key: c for c in cands}
ck("each other cell of the edge is a seam row of its own, untried",
   "west#skip1" in by and "west#skip2" in by
   and by["west#skip1"].status == "untried" and by["west#skip2"].status == "untried", sorted(by))
ck("...labelled by its cell", by.get("west#skip1") and by["west#skip1"].label() == "walk west at the edge's cell (0,8)",
   by.get("west#skip1") and by["west#skip1"].label())
ck("...carrying the cross op that takes it",
   by.get("west#skip2") and '{"op":"cross","dir":"west","skip":2} crosses at (0,10)' in (by["west#skip2"].note or ""),
   by.get("west#skip2") and by["west#skip2"].note)
ck("the plain row says which cell it uses and that the rest are listed",
   "this edge has 3 cell(s) you can reach; a plain cross uses the nearest, (0,6)" in (by["west"].note or ""),
   by["west"].note)
ck("an edge with one reachable cell gets no extra rows", "north#skip1" not in by)
ck("...and nothing names where an uncrossed cell lands",
   not by["west#skip1"].dest and "ROUTE_14" not in (by["west#skip1"].note or ""))
taken2 = dict(TAKEN, **{"west#skip1": {"n": 1, "to": "ROUTE_14|5,8"}})
cands2 = L.build(_Ex(taken2), obs(), "map:ROUTE_15", outcomes={})
by2 = {c.key: c for c in cands2}
ck("a cell already crossed is a taken row with its landing",
   by2["west#skip1"].status == "taken" and by2["west#skip1"].dest == "ROUTE_14|5,8",
   (by2["west#skip1"].status, by2["west#skip1"].dest))
ck("...while the next cell stays untried", by2["west#skip2"].status == "untried")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:240]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

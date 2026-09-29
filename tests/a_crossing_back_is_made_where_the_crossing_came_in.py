#!/usr/bin/env python3
"""A crossing back is made where the crossing came in (run 19, 2026-09-29).

A seam is a row, and which cell is crossed decides where you land. Saffron's
west edge lands in Route 7's south pocket at rows 20-23; only the row the
party came in on from Route 7's north part leads back to it. The inferred
reverse edge kept only the direction, a plain cross took the nearest cell,
landed in the pocket, and bad_seam threw the working crossing away (user: "it
keeps getting directed to the pocket when it trying to cross west"). The
inference now keeps the landing cell, `go` crosses there, the shim's cross
takes a named cell, and a failed named cell drops only that cell.

Synthetic, plus source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
sh = (ROOT / "harness/shim.lua").read_text()
ck("the inferred reverse edge keeps the cell the crossing landed on",
   '_bn[_rk]["at"] = _at' in src and '_ap = (after_obs or {}).get("player") or {}' in src)
ck("...and is kept even where the bare direction was once refuted",
   'not in (getattr(self, "_bad_seam", None) or set())\n                    or _at)' in src)
ck("go crosses at that cell", '_args["x"], _args["y"] = int(_at[0]), int(_at[1])' in src)
ck("a named cell that fails drops only the cell",
   '_fe.pop("at", None)' in src and '"inference_cell_refused"' in src)
ck("the shim's cross takes a named cell and the seam search takes only it",
   "bfs_to_edge = function(G, dir, skip, surf, blind, collect, only)" in sh
   and "if x == only.x and y == only.y then return x, y end" in sh
   and "{ x = tonumber(c.x), y = tonumber(c.y) }" in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

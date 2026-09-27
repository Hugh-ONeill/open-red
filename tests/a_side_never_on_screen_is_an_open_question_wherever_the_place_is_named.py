#!/usr/bin/env python3
"""A side of a map never on screen is said wherever that place is named, and
a part of a split map lists only the seams it can step off.

Run of record 11 (2026-09-27): the exit leg ended the moment the party came
out of Rock Tunnel's south mouth onto Route 10, eighteen rows short of
Lavender's seam, which had never been on screen. The shim said so for the
map the party stood on, and nothing kept it: from anywhere else the page
named ROUTE_10|14,52 with only "west" -- a seam Route 9 meets along Route
10's top eighteen rows, which no step off the south part takes. The next
leg set off for Lavender by Routes 11 to 15.

Pinned: the executor keeps each outdoor map's unseen sides and persists
them; a room or an older shim changes nothing; each side goes to the part
furthest that way; a map known as one part keeps them all; the remote list
and the unwalked-ground list say them; the shim's reach counts only the
stretch a neighbour meets; and a part of a split map takes only the seams
its walk reaches. Synthetic, plus the shim's source.
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


def fake():
    ex = object.__new__(E.Executor)
    ex.frontier = {"ROUTE_10|0,4": ["west"], "ROUTE_10|14,52": ["8,53"]}
    ex.visits = {"ROUTE_10|0,4": 3, "ROUTE_10|14,52": 1, "ROUTE_2|8,0": 2}
    ex.saved = 0

    def _save():
        ex.saved += 1
    ex._save_memory = _save
    return ex


ex = fake()
ex._note_sides_unseen({"map": {"id": "ROUTE_10", "sides_unseen": ["south"]}})
ck("an outdoor map's unseen sides are kept", ex._sides_unseen == {"ROUTE_10": ["south"]}
   and ex.saved == 1)
ex._note_sides_unseen({"map": {"id": "ROUTE_10", "sides_unseen": ["south"]}})
ck("...and saved only on a change", ex.saved == 1)
ex._note_sides_unseen({"map": {"id": "ROCK_TUNNEL_1F"}})
ck("a room, or an older shim, changes nothing", "ROCK_TUNNEL_1F" not in ex._sides_unseen)

ck("each side goes to the part furthest that way",
   ex._sides_unseen_of("ROUTE_10|14,52") == ["south"]
   and ex._sides_unseen_of("ROUTE_10|0,4") == [])
ex._sides_unseen["ROUTE_10"] = ["north", "south"]
ck("...north to the northern part",
   ex._sides_unseen_of("ROUTE_10|0,4") == ["north"])
ex._sides_unseen["ROUTE_2"] = ["east"]
ck("a map known as one part keeps them all", ex._sides_unseen_of("ROUTE_2|8,0") == ["east"])
ck("the words say it is an open question",
   E.Executor._side_words("south")
   == "its south side never on screen (what lies southward is not known)")

src = (ROOT / "planner/executor.py").read_text()
ck("the ledger persists and reloads them",
   '"sides_unseen": getattr(self, "_sides_unseen", {})' in src
   and 'self._sides_unseen = data.get("sides_unseen") or {}' in src)
ck("the ways-never-taken rows say them, and a place with one is a row",
   "left += [self._side_words(d) for d in _sided.get(region, [])]" in src
   and "+ list(_sided))" in src)
ck("the unwalked-ground rows say them",
   'for d in self._sides_unseen_of(region))' in src)
ck("a part of a split map takes only the seams its walk reaches",
   "if isinstance(_cr, dict) and len(_parts_c | {here}) > 1:" in src
   and "_conns = [d for d in _conns if _cr.get(d)]" in src)

sh = (ROOT / "harness/shim.lua").read_text()
ck("the shim's reach counts only the stretch a neighbour meets",
   'if x == 0 and _in_span("west", x, y) then _cr.west = true end' in sh
   and "return along >= 0 and along < span" in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

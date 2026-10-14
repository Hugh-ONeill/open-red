#!/usr/bin/env python3
"""The wake place is called a Center only when it is one (run 57, 2026-10-14).

A new game wakes at PALLET_TOWN, which has no Center, and the page said
"IF THE PARTY FAINTS you wake at PALLET_TOWN — the last Pokemon Center you
HEALED at"; BULBASAUR at 3/30 planned "return to Pallet Town and heal at the
Pokemon Center".

Synthetic.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def line(wake, sightings=None):
    x = object.__new__(E.Executor)
    x.sightings = sightings or {}
    x.visits, x.explored = {}, {}
    x._where = lambda obs: "ROUTE_1|0,0"
    x._route = lambda a, b: None
    return E.Executor._respawn_line(x, {"respawn": {"map": wake}})


s = line("PALLET_TOWN")
ck("a new game's wake place is not called a Center",
   "PALLET_TOWN — not a Pokemon Center" in s and "Center you HEALED" not in s, s)
s = line("VIRIDIAN_POKECENTER")
ck("a Center is still called one", "the last Pokemon Center you HEALED at" in s, s)
s = line("INDIGO_PLATEAU_LOBBY", {"INDIGO_PLATEAU_LOBBY|7,5": ["INDIGOPLATEAULOBBY_NURSE"]})
ck("a room with a nurse in it is a Center", "the last Pokemon Center you HEALED at" in s, s)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""The party line says which moves are at 0 PP.

Run 70, Route 25 (2026-11-01): KADABRA read "21/56hp" on both party lines
and was led into the grass round after round with CONFUSION, its only
damaging move, at 0/25; the battle policy could only TELEPORT out and the
grinds earned it nothing. Pinned: moves at 0 PP are named, and a member
with no damaging move left says so. Synthetic.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


kad = {"moves": [{"id": "TELEPORT", "power": 0, "pp": 0},
                 {"id": "CONFUSION", "power": 50, "pp": 0},
                 {"id": "DISABLE", "power": 0, "pp": 17}]}
s = E._mon_pp(kad)
ck("names the moves at 0 PP", "0 PP: TELEPORT, CONFUSION" in s, s)
ck("says no damaging move has PP left", "no damaging move has PP left" in s, s)

part = {"moves": [{"id": "TACKLE", "power": 35, "pp": 0},
                  {"id": "VINE_WHIP", "power": 35, "pp": 8}]}
s = E._mon_pp(part)
ck("one dry attack among others is named", "0 PP: TACKLE" in s, s)
ck("...without the none-left words", "no damaging" not in s, s)

ck("all PP left says nothing",
   E._mon_pp({"moves": [{"id": "TACKLE", "power": 35, "pp": 3}]}) == "")
ck("unknown PP says nothing",
   E._mon_pp({"moves": [{"id": "TACKLE", "power": 35}]}) == "")
ck("no moves list is fine", E._mon_pp({}) == "" and E._mon_pp(None) == "")
src = (ROOT / "planner" / "executor.py").read_text()
ck("both party lines carry it", src.count("+ _mon_pp(m)") == 2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A door the walk cannot reach through UNSEEN ground is not "blocked".

Run 52, Mt Moon B2F (2026-10-11): the exit ladder (5,7) lies past the
fossil room's north edge, never on screen. It was written "the way onto it
is blocked; nearest person MTMOONB2F_SUPER_NERD, 8 cells off" — the nerd
long beaten — and the line rode every floor's page, so the run left the
basement sure there was no exit. Probed on run 52's own save after the
fossil: the room's unseen edge is the row y=3 (10 spots) and (7,7)/(7,8),
beside the ladder, are seen but not yet reached; eight earlier runs took
(5,7) from this same room to east ROUTE_4.

Pinned: while the floor has ground never on screen the note says so; with
none, the old words stand. Synthetic.
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


def run(frontier_n):
    ex = E.Executor.__new__(E.Executor)
    ex._unopened_doors = lambda obs: [("5,7", None, "MTMOONB2F_SUPER_NERD", 8)]
    ex.shut_doors = {}
    ex._save_memory = lambda *a, **k: None
    ex.log = lambda *a, **k: None
    obs = {"mode": "overworld", "player": {"x": 13, "y": 7},
           "map": {"id": "MT_MOON_B2F", "region": "3,2", "warps": [],
                   "seen": {"n": 1087, "frontier_n": frontier_n}, "frontier": []}}
    for _ in range(80):
        try:
            ex.note_frontier(obs)
            break
        except AttributeError as e:
            name = str(e).split("'")[-2]
            setattr(ex, name, {})
        except TypeError:
            break
    return " ".join(sum(ex.shut_doors.values(), []))


s = run(10)
ck("with unseen ground it says so", "10 spot(s) never on screen" in s, s)
ck("...and does not call the nerd the block", "nearest person" not in s, s)
s0 = run(0)
ck("with the floor all seen the old words stand",
   "the way onto it is blocked; nearest person MTMOONB2F_SUPER_NERD" in s0, s0)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A push whose walk into place a wild fight cut short may be sent again.

Run 27, 2026-09-18, Victory Road 3F: push(22,15 -> 23,15) had its walk to
(21,15) cut by four wild fights in a row and said "something interrupted
the walk (interrupted (battle or script)) ... send it again"; the repeat
gate knew only "a fight started" / "because of the battle", so it refused
the re-send twice and the run stood still (user: "now its just standing
still not having pushed it in yet").

Pinned: the push op's interruption words count as the world cutting the
op short, and the repeat gate lets such a macro through; the stored reason
is long enough to keep them. Mixed."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


line = ("push(x=22,y=15,to_x=23,to_y=15) — resumed 4x and it is still not on (23,15): "
        "FAILED — shoved it 0 of 1 cell(s) toward (23,15) and then stopped: could not "
        "get to (21,15) to push it right: something interrupted the walk (interrupted "
        "(battle or script)). The ground is fine; send it again. It is at (22,15) now")
ck("the push op's interrupted walk is the world cutting it short", E.Executor._walk_cut_by_the_world(line))
ck("...and so is its interrupted shove",
   E.Executor._walk_cut_by_the_world("shoved it right and something interrupted before it moved (battle)"))
ck("...and a real refusal is not", not E.Executor._walk_cut_by_the_world("shoved it right and it did not move — something is behind it"))
ck("the phrase the gate matches survives the stored cut", "something interrupted" in line[:400])
src = (ROOT / "planner/executor.py").read_text()
ck("the repeat gate lets a fight-cut push through",
   '"a fight started"))' in src and '("something interrupted" in _sw' in src)
ck("...but a guard's script that speaks is still a refusal",
   not E.Executor._walk_cut_by_the_world('cross(dir=east): FAILED — something interrupted (battle or script) — it said: "the road\'s closed."'))
ck("the stored reason keeps 400 characters", '_rec["why"] = _why[:400]' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

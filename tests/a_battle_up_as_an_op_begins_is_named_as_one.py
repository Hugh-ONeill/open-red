#!/usr/bin/env python3
""""not in overworld (a box was up and would not close: kind=wild)" was a
wild battle that had just begun, and the line now says so.

That sentence failed 121 round results across the archived runs (explore 72,
walk_to 30, push 7, cross 2), always right after a fled wild or a landing.
Reproduced 2026-11-01 on a crafted Seafoam B4F save, riding the water back
and forth: 18 of 40 rides answered it, every one with a BattleState on top
that had both battlers and phase=messages ("Wild X appeared!"), the
observation after it in mode=battle. Nothing was stuck: the previous op's
last step had rolled an encounter, the battle's intro was on the stack when
the next op asked for the overworld, and the op called it a box. The
executor's cut detector already counts "a box was up" / "kind=wild" as the
world moving, so the hop was never stamped; only the words were wrong, and
the walk hop now resumes after it (a_walk_a_wild_cut_is_walked_on).

Pinned: the screen name says a battle is up, with its battlers and phase,
when the thing on top is one; a kind-bearing screen that is not a battle
lists its fields instead; the executor still reads it as a world cut."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("local function _screen_name(G)")
blk = shim[i:shim.index("function U.is_battle(t)")]
ck("a kind-bearing screen that is a battle says so, with battlers and phase",
   "if U.is_battle(t) then" in blk
   and '"a battle is up: enemy=%s player=%s phase=%s"' in blk)
ck("...and one that is not lists its fields",
   '"not a battle; fields: "' in blk)
ck("the test for a battle is the one every battle check uses (sides, trainer or phase)",
   "t.enemy ~= nil or (t.kind ~= nil and" in shim[shim.index("function U.is_battle(t)"):][:300])
det = ("could not get onto the water: not in overworld (a box was up and would "
       "not close: kind=wild, a battle is up: enemy=true player=true phase=messages)")
ck("the executor reads that answer as the world moving, not the ground refusing",
   E.Executor._walk_cut_by_the_world(det))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

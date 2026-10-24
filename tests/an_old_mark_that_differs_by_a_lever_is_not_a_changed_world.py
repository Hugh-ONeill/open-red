#!/usr/bin/env python3
"""A part stood in before the lever-free mark existed is not "changed" by a
lever flip alone.

Run 62, 2026-10-24: Viridian City's part 17,0 was looked out from with the
Mansion's statues one way; with them the other way its saved mark (the only
one it had) did not match today's, so _unseen_there kept its 23 spots, and
explore, finding 3F worked out, walked the run six legs by Surf off Cinnabar
to them, where "no walk from here reaches" them. A digest cannot have the
levers taken out, so today's flags are tried with each known lever set and
cleared.

Pinned: an old full mark that today's world reaches by setting a lever is
"done"; one that also differs by a flag gained is "changed"; with no lever
known it is "changed"; a lever-free mark, when there is one, still decides.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R = "VIRIDIAN_CITY|17,0"
LEVER = "EVENT_MANSION_SWITCH_ON"
WM = E.Executor._world_mark


def verdict(then_flags, now_flags, toggled, nt=False):
    ex = object.__new__(E.Executor)
    ex.region_seen = {R: 23}
    ex.frontier_here = {R: 0}
    ex.visits = {R: 22}
    ex._water_unseen = lambda r: 0
    ex._toggled_flags = list(toggled)
    now = {"badges": ["A"], "flags": now_flags, "bag": {"POTION": 1}}
    then = dict(now, flags=then_flags)
    ex._region_mark = {R: WM(then)}
    ex._mark_now = WM(now)
    ex._mark_obs = now
    strip = lambda fl: [f for f in fl if f not in set(toggled)]
    ex._region_mark_nt = {R: WM(dict(then, flags=strip(then_flags)))} if nt else {}
    ex._mark_now_nt = WM(dict(now, flags=strip(now_flags)))
    return ex._unseen_there(R)


ck("an old mark that differs only by a lever is done",
   verdict(["A", LEVER], ["A"], [LEVER]) == (0, "done"), verdict(["A", LEVER], ["A"], [LEVER]))
ck("...either way round", verdict(["A"], ["A", LEVER], [LEVER]) == (0, "done"))
ck("an old mark that also differs by a flag gained is changed",
   verdict(["A", LEVER], ["A", "EVENT_GOT_SECRET_KEY"], [LEVER]) == (23, "changed"))
ck("with no lever known it is changed", verdict(["A", LEVER], ["A"], []) == (23, "changed"))
ck("a lever-free mark still decides when there is one",
   verdict(["A"], ["A", LEVER, "B"], [LEVER], nt=True) == (23, "changed"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

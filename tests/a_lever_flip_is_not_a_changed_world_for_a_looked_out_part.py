#!/usr/bin/env python3
"""A lever thrown since a part was looked out from does not reopen its count.

Run 62, 2026-10-24: _unseen_there keeps a part's old unseen count unless the
run stood there, found nothing reachable left, and the world mark has not
moved since. The mark digests every event flag, and the Mansion's statues
flip EVENT_MANSION_SWITCH_ON back and forth, so the verdict was "changed" on
every floor every time: 2F|10,1 kept "7 spot(s) where its seen ground
ends", and explore's line on 3F sent the run down hole (19,14) to sweep it
instead of offering hole (16,14) to the basement, lap after lap.

Pinned: a flag seen both set and cleared is left out of the mark the verdict
compares; a lever flip leaves a looked-out part "done"; a flag never cleared
(something gained) still makes it "changed"; the general mark still moves
with a lever.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R = "POKEMON_MANSION_2F|10,1"
LEVER = "EVENT_MANSION_SWITCH_ON"


def verdict(then_flags, now_flags, toggled):
    ex = object.__new__(E.Executor)
    ex.region_seen = {R: 7}
    ex.frontier_here = {R: 0}
    ex.visits = {R: 3}
    ex._water_unseen = lambda r: 0
    ex._toggled_flags = list(toggled)
    strip = lambda fl: [f for f in fl if f not in set(toggled)]
    ex._region_mark = {R: E.Executor._world_mark({"flags": then_flags})}
    ex._mark_now = E.Executor._world_mark({"flags": now_flags})
    ex._region_mark_nt = {R: E.Executor._world_mark({"flags": strip(then_flags)})}
    ex._mark_now_nt = E.Executor._world_mark({"flags": strip(now_flags)})
    return ex._unseen_there(R), ex._mark_now != ex._region_mark[R]


(v, moved) = verdict(["A"], ["A", LEVER], toggled=[LEVER])
ck("a lever flip leaves a looked-out part done", v == (0, "done"), v)
ck("...while the general mark still moves with it", moved)
(v2, _) = verdict(["A"], ["A", "EVENT_GOT_SECRET_KEY"], toggled=[LEVER])
ck("a flag never cleared (something gained) still reopens it", v2 == (7, "changed"), v2)

src = (ROOT / "planner" / "executor.py").read_text()
ck("a cleared flag is recorded as a lever",
   "_cleared = self._known_flags - flags" in src and "self._toggled_flags = sorted(" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

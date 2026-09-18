#!/usr/bin/env python3
"""Explore's walk to a wall that may have moved says what the look found,
and sweeps at once when it put unseen ground in reach.

Run 27, 2026-09-18, Mansion B1F: after the (20,3) press, explore walked to
(10,6) beside (9,6); the look opened it and put 6 spots of unseen ground in
reach, the page said only "walk_to(10,6): ok", and the model flipped the
statue back, shutting it again (user: "it had all this new frontier it
could see was open, then it chose to go back and press the statue again").

Pinned: with unseen ground in reach after the look, the sweep runs in the
same op and the page says the wall is gone; with none, the page says the
wall stands and nothing came into reach. Synthetic, no game."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def before():
    return {"mode": "overworld", "badges": [], "party": [],
            "map": {"id": "POKEMON_MANSION_B1F", "frontier": [],
                    "seen": {"frontier_n": 0},
                    "frontier_stale": [{"x": 10, "y": 6, "wx": 9, "wy": 6, "d": 3}]}}


def fake(after):
    ex = object.__new__(E.Executor)
    ex._explore_params = {"until": "item"}
    ex._cur_target = "item:SECRET_KEY"
    ex.ran = []
    ex.logs = []

    def run(sg, ops, ignore_done=False):
        ex.ran.append(ops[0]["op"])
        if ops[0]["op"] == "walk_to":
            return False, ["walk_to(10,6): ok"], []
        return False, ["sweep(until=item): ok (came into view: ITEM at (5,4))"], [ops[0]]
    ex._run_traced = run
    ex.settle = lambda *a, **k: after
    ex.log = lambda kind, **kw: ex.logs.append((kind, kw))
    ex._count_dry_walk = lambda *a, **k: None
    ex._where = lambda o: "POKEMON_MANSION_B1F|20,1"
    ex._knows_move = lambda o, m: False
    return ex


opened = {"mode": "overworld",
          "map": {"id": "POKEMON_MANSION_B1F", "seen": {"frontier_n": 6},
                  "frontier": [{"x": 8, "y": 6, "d": 2}], "frontier_stale": []}}
ex = fake(opened)
ok, tr, cl = ex._explore_step({"id": "t"}, before())
ck("a look that put unseen ground in reach sweeps in the same op", ex.ran == ["walk_to", "sweep"], ex.ran)
ck("...and says the wall is gone and how much ground came in reach",
   any("put 6 spot(s) of unseen ground within reach — (9,6) is not a wall any more" in t for t in tr), tr)
ck("...and the sweep's own words follow", any("came into view: ITEM" in t for t in tr), tr)

shut = {"mode": "overworld",
        "map": {"id": "POKEMON_MANSION_B1F", "seen": {"frontier_n": 0}, "frontier": [],
                "frontier_stale": [{"x": 10, "y": 6, "wx": 9, "wy": 6, "d": 0}]}}
ex = fake(shut)
ok, tr, cl = ex._explore_step({"id": "t"}, before())
ck("a look that opened nothing does not sweep", ex.ran == ["walk_to"], ex.ran)
ck("...and says the wall stands and nothing came in reach",
   any("(9,6) is still a wall, and no unseen ground came within reach" in t for t in tr), tr)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

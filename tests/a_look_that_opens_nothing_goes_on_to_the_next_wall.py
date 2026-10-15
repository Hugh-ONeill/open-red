#!/usr/bin/env python3
"""A look at a moved wall that opens nothing goes on to the next one
(run 57, 2026-10-14).

Mansion B1F with the statue flipped: explore walked beside (13,23), it was
still shut, the look put (26,18) on the stale list, and explore stopped with
"no unseen ground came within reach". The model left the floor and spent
hours elsewhere. Probed on run 57's save with its own seen ground: the
second look, at (26,18), opened 22 spots and the sweep found the second
statue and the ball at (10,2). Explore now makes up to four looks per op,
each at a wall not yet looked at this op, and sweeps after the first that
opens ground; when none does it says how many walls are still unlooked-at.
Synthetic, no game."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def stale(x, y, wx, wy):
    return {"x": x, "y": y, "wx": wx, "wy": wy, "d": 1}


def obs(frontier_n, stales):
    return {"mode": "overworld",
            "map": {"id": "POKEMON_MANSION_B1F", "seen": {"frontier_n": frontier_n},
                    "frontier": [{"x": 26, "y": 10, "d": 3}] if frontier_n else [],
                    "frontier_stale": stales}}


def fake(seq):
    ex = object.__new__(E.Executor)
    ex._explore_params = {"until": "item"}
    ex._cur_target = "item:SECRET_KEY"
    ex.ran, ex.logs = [], []
    it = iter(seq)
    cur = {"o": None}

    def run(sg, ops, ignore_done=False):
        ex.ran.append((ops[0]["op"], ops[0].get("x"), ops[0].get("y")))
        if ops[0]["op"] == "walk_to":
            cur["o"] = next(it)
            return False, [f"walk_to({ops[0]['x']},{ops[0]['y']}): ok"], []
        return False, ["sweep(until=item): ok (came into view: ITEM_POKEMON_MANSION_B1F_10_2)"], [ops[0]]
    ex._run_traced = run
    ex.settle = lambda *a, **k: cur["o"]
    ex.log = lambda kind, **kw: ex.logs.append((kind, kw))
    ex._count_dry_walk = lambda *a, **k: None
    ex._where = lambda o: "POKEMON_MANSION_B1F|10,9"
    ex._knows_move = lambda o, m: False
    return ex


start = obs(0, [stale(14, 23, 13, 23), stale(14, 22, 13, 22)])
# look 1 at (13,23): still shut, (26,18) now on the list; look 2 opens ground
ex = fake([obs(0, [stale(14, 23, 13, 23), stale(26, 17, 26, 18)]), obs(22, [])])
ok, tr, cl = ex._explore_step({"id": "t"}, start)
ck("the first look opened nothing, so a second look went to the next wall",
   [r[:3] for r in ex.ran] == [("walk_to", 14, 23), ("walk_to", 26, 17), ("sweep", None, None)], ex.ran)
ck("...the first look says another wall is still unlooked-at",
   any("1 other wall(s) that may have moved are still unlooked-at, nearest beside (26,18)" in t for t in tr), tr)
ck("...and the second, which opened ground, is swept in the same op",
   any("put 22 spot(s) of unseen ground within reach" in t for t in tr)
   and any("ITEM_POKEMON_MANSION_B1F_10_2" in t for t in tr), tr)

# nothing anywhere opens: four looks at most, each a different wall
walls = [stale(10 + i, 5, 10 + i, 4) for i in range(6)]
ex = fake([obs(0, walls)] * 6)
ok, tr, cl = ex._explore_step({"id": "t"}, obs(0, walls))
ck("no more than four looks in one op", len(ex.ran) == 4 and all(r[0] == "walk_to" for r in ex.ran), ex.ran)
ck("...each at a different wall", len({r[1] for r in ex.ran}) == 4, ex.ran)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

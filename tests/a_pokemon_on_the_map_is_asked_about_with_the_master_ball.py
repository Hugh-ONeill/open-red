#!/usr/bin/env python3
"""A species never owned that was standing on the map is asked about even
when the Master Ball is the only ball, and a yes throws the Master Ball.

Run 27, 2026-09-18, Victory Road 2F: the party walked up to Moltres with
only a MASTER_BALL in the bag. The new-species question counts only balls
the catch ladder throws (the Master Ball is outside it on purpose), so it
never asked; the traversal policy fled on turn one and EVENT_BEAT_MOLTRES
fired (user: "the species you dont own thing should have fired").

Pinned: with only a Master Ball, a wild from the grass is still not asked
about; one standing on the map (its species in a map object's name) is,
the question says so, and a yes names MASTER_BALL for that catch; the catch
policy takes a per-battle ball. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


seen_user = {}


def chat(msgs, model):
    seen_user["u"] = msgs[-1]["content"]
    return '{"catch": true, "why": "one of a kind"}'


E.brock_probe.chat = chat


def fake(objs):
    ex = object.__new__(E.Executor)
    ex._new_species_asked = {}
    ex._save_memory = lambda: None
    ex.log = lambda *a, **k: None
    ex.model = "m"
    ex._last_overworld_objs = objs
    return ex


def obs(bag):
    return {"battle": {"kind": "wild", "foe": {"species": "MOLTRES", "level": 50,
                                               "types": ["FIRE", "FLYING"], "owned": False}},
            "bag": bag, "party": [], "pc_mons": []}


ex = fake([("VICTORYROAD2F_HIKER", 12, 9)])
ck("a wild from the grass with only a Master Ball is not asked about",
   ex._ask_new_species(obs({"MASTER_BALL": 1}), {"id": "t"}) is None)
ex = fake([("VICTORYROAD2F_MOLTRES", 11, 5)])
got = ex._ask_new_species(obs({"MASTER_BALL": 1}), {"id": "t"})
ck("one standing on the map is asked about", got is not None, got)
ck("...a yes names the MASTER_BALL for that catch", (got or {}).get("ball") == "MASTER_BALL", got)
ck("...and the question says it stood on the map and the Master Ball is the ball",
   "IT WAS STANDING ON THE MAP" in seen_user.get("u", "")
   and "your only ball is a MASTER_BALL" in seen_user.get("u", ""), seen_user.get("u", "")[:400])
ex = fake([("VICTORYROAD2F_MOLTRES", 11, 5)])
got = ex._ask_new_species(obs({"MASTER_BALL": 1, "ULTRA_BALL": 3}), {"id": "t"})
ck("with ordinary balls in the bag the Master Ball is not named", "ball" not in (got or {}), got)

import inspect  # noqa: E402
ck("the catch policy takes a ball for this battle",
   "ball=None" in inspect.getsource(E._run_policy).split(")")[0]
   and 'spec["catch"] = dict(spec["catch"], ball=ball)' in inspect.getsource(E._run_policy))
ck("...and a named Master Ball is thrown on turn one",
   'spec["catch"]["first_ball"] = True' in inspect.getsource(E._run_policy))
src = (ROOT / "planner/executor.py").read_text()
ck("the executor passes a named ball to the catch policy",
   'if name == "catch" and (_new or {}).get("ball"):' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

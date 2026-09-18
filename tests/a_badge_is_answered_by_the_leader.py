#!/usr/bin/env python3
"""Under a badge goal, the gym's leader ranks first among the fresh rows and
says a walk reaches them.

Run 27, 2026-09-18, Viridian Gym under EARTHBADGE: every fresh row tied and
the tie fell to kind and name, so GIOVANNI read seventh — behind an item
ball, the door out and three trainers — and the run, a few cells from him,
decided walls and boulders kept it away and went for the others (user: "but
it was right next to the guy"; "the same thing happened with koga i
think").

Pinned: a reachable unbeaten leader outranks other fresh rows under a badge
goal and carries the note; not under another goal; not another trainer; an
unreachable leader gets no "a walk reaches them". Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import ledger as L  # noqa: E402
import candidates as C  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def rows(target, gio_reach=True, gym="VIRIDIAN_GYM", leader="VIRIDIANGYM_GIOVANNI"):
    ex = C.make()
    o = C.obs(ex, [], objects=[
        {"name": "ITEM_VIRIDIAN_GYM_16_9", "kind": "item", "x": 16, "y": 9, "reachable": True},
        {"name": "VIRIDIANGYM_COOLTRAINER_M1", "kind": "trainer", "x": 12, "y": 7,
         "reachable": True, "beaten": False},
        {"name": leader, "kind": "trainer", "x": 2, "y": 1,
         "reachable": gio_reach, "beaten": False}])
    o["map"]["id"] = gym
    return [c for c in L.build(ex, o, target=target, want_explore=False)]


r = rows("badge:EARTHBADGE")
keys = [c.key for c in r]
gio = next(c for c in r if c.key == "VIRIDIANGYM_GIOVANNI")
ck("the leader outranks the item and the other trainer under a badge goal",
   keys.index("VIRIDIANGYM_GIOVANNI") < keys.index("ITEM_VIRIDIAN_GYM_16_9")
   and keys.index("VIRIDIANGYM_GIOVANNI") < keys.index("VIRIDIANGYM_COOLTRAINER_M1"), (keys, [c.status for c in r]))
ck("...and says a walk reaches them", "this gym's LEADER, and a walk from where you stand reaches them" in (gio.note or ""), gio.note)
r2 = rows("item:X")
g2 = next(c for c in r2 if c.key == "VIRIDIANGYM_GIOVANNI")
ck("not under another goal", "LEADER" not in (g2.note or ""), g2.note)
r3 = rows("badge:EARTHBADGE", gio_reach=False)
g3 = next(c for c in r3 if c.key == "VIRIDIANGYM_GIOVANNI")
ck("an unreachable leader gets no 'a walk reaches them'", "walk from where you stand reaches" not in (g3.note or ""), g3.note)
r4 = rows("badge:SOULBADGE", gym="FUCHSIA_GYM", leader="FUCHSIAGYM_KOGA")
k4 = [c.key for c in r4]
ck("the same in Koga's gym", k4.index("FUCHSIAGYM_KOGA") < k4.index("ITEM_VIRIDIAN_GYM_16_9"), k4)

import executor as E  # noqa: E402
ex = C.make()
ex._not_for_explore_to_press = lambda n, k, w: E.Executor._not_for_explore_to_press(ex, n, k, w)
ex._is_gym_leader = E.Executor._is_gym_leader
o = C.obs(ex, [], objects=[{"name": "VIRIDIANGYM_GIOVANNI", "kind": "trainer", "x": 2, "y": 1,
                            "reachable": True, "beaten": False}])
o["map"]["id"] = "VIRIDIAN_GYM"
page = L.render(L.build(ex, o, target="badge:EARTHBADGE"), ex, o, target="badge:EARTHBADGE")
first = page.splitlines()[1]
ck("explore's row never promises to press the leader", "press VIRIDIANGYM_GIOVANNI here" not in page, first)
ck("...and names him as left to the model instead of calling the room worked",
   "explore leaves VIRIDIANGYM_GIOVANNI to you (this gym's LEADER" in first, first)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

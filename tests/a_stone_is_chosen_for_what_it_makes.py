#!/usr/bin/env python3
"""A stone is chosen for what it makes (run 19, 2026-09-29).

Run 19 bought the first stone on Celadon 4F's shelf, FIRE_STONE ("evolution
stones are useful for the party"), and the stone question asked about it
with nothing to weigh it by: EEVEE became a FLAREON with no Fire move while
the outline still asked for "a WATER or ELECTRIC type" (user: "what leg is
even asking for fire??"; "is firestone the first stone offered in the shop").
Both questions now carry the booklet's line for each stone, and the
outline's type legs still ahead; which, if any, stays the model's.

Synthetic, plus source checks.
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


line = E.Executor._booklet_words(["POKE_DOLL", "FIRE_STONE", "THUNDER_STONE", "WATER_STONE"])
ck("the shelf's stones are said in the booklet's words",
   "THUNDER_STONE: This stone has a connection to Electric Pokemon." in line
   and "WATER_STONE: This stone has a connection to Water Pokemon." in line, line)
ck("...and nothing is said of an item the booklet does not list",
   E.Executor._booklet_words(["NOT_AN_ITEM"]) == "")

x = object.__new__(E.Executor)
x._species_names = lambda: set()
E.outline_ahead.catch_goals_ahead = lambda *a, **k: [{"pos": 43, "leg": "the party holds a WATER or ELECTRIC type"}]
ck("the legs ahead are said as the starter question says them",
   "43. the party holds a WATER or ELECTRIC type" in x._type_legs_ahead({"party": []}))
src = (ROOT / "planner/executor.py").read_text()
ck("the stone question carries both",
   "+ self._booklet_words(stones) + self._type_legs_ahead(obs)" in src)
ck("the shop question carries the booklet always and the legs when a stone is on the shelf",
   "+ Executor._booklet_words(shelf)" in src and 'if any(str(i).endswith("_STONE") for i in shelf)' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

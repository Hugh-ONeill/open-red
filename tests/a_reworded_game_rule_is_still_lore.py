#!/usr/bin/env python3
"""A missing-rung reason that calls something a "required item trigger" is
asserting a rule of the game, like "the game requires".

Run 38, 2026-10-08: "Obtain the MOON STONE in Mt. Moon" was turned down for
"the game requires the player to obtain the Moon Stone", then inserted on
the re-ask for "the Moon Stone, which is a required item trigger for the
cave" — the run of record 9 insert the pattern exists to stop.

Pinned: the trigger phrasings are caught; the old phrasings still are; the
game's own quoted words ("A COIN CASE is required!") and a person's
instruction are not."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


R = A._GAME_RULE.search
ck("a required item trigger is lore", R("the Moon Stone, which is a required item trigger for the cave"))
ck("so is an event trigger", R("beating him is the event trigger for the bridge"))
ck("the old phrasings still are", R("the game requires the player to obtain it") and R("needed to trigger the exit"))
ck("the game's own quoted words are not", not R('The machine said "A COIN CASE is required!"'))
ck("a person's instruction is not", not R("Bill said: go to my PC and run the Cell Separation System"))

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

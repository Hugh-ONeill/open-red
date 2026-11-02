#!/usr/bin/env python3
"""A tower's door says it is a tower, as a Mart's and a Center's do.

Run 70, Lavender (2026-11-01): door (14,5) read bare "-> UNKNOWN" beside the
town's POKEMART and POKEMON CENTER rows, and the run explored the town for
seven rounds for a tower it was standing beside. Pinned: the frontage for
POKEMON_TOWER_1F names a tower and nothing inside; a house stays unnamed.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
f = E.Executor._frontage
t = f("POKEMON_TOWER_1F") or ""
checks.append(("the tower door reads as a tower", "TOWER" in t))
checks.append(("...and says nothing of what is inside",
               not any(w in t.upper() for w in ("GHOST", "GRAVE", "SCOPE", "SPIRIT"))))
checks.append(("an upper floor is not a street door", f("POKEMON_TOWER_2F") is None))
checks.append(("a house stays unnamed", f("LAVENDER_CUBONE_HOUSE") is None))
checks.append(("the mart still reads as a mart", "POKEMART" in (f("LAVENDER_MART") or "")))
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

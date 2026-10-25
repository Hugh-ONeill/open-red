#!/usr/bin/env python3
"""An item named the way a person says it is still checked against the bag.

Run 65, 2026-10-25. "Retrieve the Pokemon Flute from Mr. Fuji" was judged
already done ("the player has visited Mr. Fuji's house and completed the
Pokemon Tower event") with no POKE_FLUTE in the bag and the tower's ghost
never passed. _item_not_held squashes the objective to letters and looks for
each item id in it: "Pokemon Flute" squashed to POKEMONFLUTE and "Poké
Flute" to POKFLUTE (the é dropped), and neither holds POKEFLUTE. The leg was
crossed off, and the Flash leg after it was skipped on "since the Flute is
already retrieved, there are no remaining areas that necessitate this HM".

Pinned: both spellings are refused with no flute held, and pass with one;
a place named for Pokemon is not taken for an item.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

NONE = "BAG: POKE_BALL x14, HM_CUT (HM01), NUGGET"
HELD = "BAG: POKE_BALL x14, POKE_FLUTE, HM_CUT (HM01)"

for g in ("Retrieve the Pokemon Flute from Mr. Fuji",
          "Retrieve the Poké Flute from Mr. Fuji",
          "Obtain the POKE_FLUTE"):
    ck(f"{g!r} with no flute held is refused", A._item_not_held(g, NONE) == "POKE_FLUTE",
       A._item_not_held(g, NONE))
    ck(f"{g!r} with the flute held stands", A._item_not_held(g, HELD) is None,
       A._item_not_held(g, HELD))
for g in ("Reach the Pokemon Tower", "Catch a Pokemon in the grass of Route 11",
          "Heal at the Pokemon Center"):
    ck(f"{g!r} names no item", A._item_not_held(g, NONE) is None, A._item_not_held(g, NONE))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
""""I have the Pokedex" is not read back as "the bag holds no POKEDEX".

Run 71, 2026-11-02, enter_route_2 after delivering Oak's parcel: every round
said "WORDS ARE NOT THE BAG: your plan speaks of holding POKEDEX; the bag
holds no POKEDEX." Gen 1 lists POKEDEX as an item, but Oak's gift is the
flag EVENT_GOT_POKEDEX and is never a bag row, so the line told the model it
lacked what it had. Pinned on _held_claim_note: with the flag set the claim
is not contested; without it, it still is.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "planner"))
import executor as E  # noqa: E402

ex = E.Executor.__new__(E.Executor)
said = "Now that I have delivered Oak's parcel and have the Pokedex, the path should be open."
base = {"mode": "overworld", "bag": {"POTION": 1}}
with_flag = ex._held_claim_note(said, dict(base, flags=["EVENT_GOT_POKEDEX"]))
without = ex._held_claim_note(said, dict(base, flags=[]))
checks = [("with EVENT_GOT_POKEDEX the claim stands", "POKEDEX" not in with_flag),
          ("without it the bag check still speaks", "POKEDEX" in without)]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"  {with_flag!r} / {without!r}"))
sys.exit(1 if bad else 0)

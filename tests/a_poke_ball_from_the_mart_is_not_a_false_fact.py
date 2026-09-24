#!/usr/bin/env python3
"""A Poké Ball obtained from the Poké Mart is not a false fact; a Pokémon
from the mart, or a ball from a resident who does not exist, still is.

Run of record, 2026-09-24, leg 4 "Reach Pewter City". The outline had no
parcel leg and its second-member leg after Pewter, so nothing sent the run
into the mart; the old man held the north exit; four attempts were spent
in place. Every rung ran. The wording rung answered "Obtain the Poké Ball
from the Poké Mart in Viridian City and reach Pewter City" — the one
sentence that walks into the clerk who hands over the parcel — and the
garbled-parcel row refused it twice: its pattern read "(pokemon|poke
balls?) from the mart". The chain stopped at leg 4, 47 minutes in, on our
guard.

Pinned: a ball from the mart passes; a Pokemon from the mart is still
garbled; a ball from the Pallet resident is still garbled (run 27's own
false fact); a ball from the Pokemon Center is; buying balls at the mart
passes; the parcel errand passes. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
from outline_facts import false_facts  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def bad(leg):
    return bool(false_facts([leg]))


ck("a Poke Ball obtained from the Poke Mart is not a false fact",
   not bad("Obtain the Poké Ball from the Poké Mart in Viridian City and reach Pewter City"))
ck("...nor Poke Balls bought there", not bad("Buy Poke Balls at the Viridian City Poke Mart"))
ck("...nor retrieved there", not bad("Retrieve Poke Balls from the Viridian Poke Mart"))
ck("a Pokemon from the Poke Mart is still the parcel, garbled",
   bad("Retrieve the Pokemon from the Poke Mart"))
ck("...and from the mart in other words", bad("Obtain a Pokemon from the Mart"))
ck("a Poke Ball from the Pallet Town resident is still false (run 27's own)",
   bad("Retrieve the Poké Ball from the Pallet Town resident"))
ck("...and from a villager or a neighbour",
   bad("Get a Poke Ball from the villager") and bad("Obtain Poke Balls from the neighbour"))
ck("a Poke Ball from the Pokemon Center is false: it sells none",
   bad("Obtain a Poke Ball from the Pokemon Center"))
ck("the parcel errand itself passes",
   not bad("Collect the OAKS_PARCEL from the clerk at the Viridian City Poke Mart and deliver it to Professor Oak"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

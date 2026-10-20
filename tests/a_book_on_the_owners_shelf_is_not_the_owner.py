#!/usr/bin/env python3
"""A thing named by what the screen shows stands for its house's owner only
when it is a body, not a book.

Run 59, 2026-10-19: "Retrieve the Pokemon Flute from Mr. Fuji", with the
Flute in the bag and EVENT_GOT_POKE_FLUTE fired, was refused by check-done,
the already-done sweep and VOID alike on "this objective names BOOK_MR_
FUJIS_HOUSE_3_3, seen in MR_FUJIS_HOUSE|2,1 and never spoken to or pressed",
and the leg was passed over. The owner rule (POKEMON_BILLS_HOUSE_6_5 is
Bill, 2026-09-30) read the bookshelf as Mr. Fuji. Synthetic: a crafted
explored.json in a temporary file, never the live run.
"""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def run(sightings, touched, goal):
    f = Path(tempfile.mkdtemp()) / "explored.json"
    f.write_text(json.dumps({"sightings": sightings, "touched": touched}))
    return author.untouched_named(goal, str(f))

r = run({"MR_FUJIS_HOUSE|2,1": ["BOOK_MR_FUJIS_HOUSE_3_3", "MRFUJISHOUSE_MR_FUJI"]},
        {"MR_FUJIS_HOUSE|2,1": ["MRFUJISHOUSE_MR_FUJI"]},
        "Retrieve the Pokemon Flute from Mr. Fuji")
ck("a book in Mr. Fuji's house is not Mr. Fuji", r == [], r)
r = run({"MR_FUJIS_HOUSE|2,1": ["POKEMON_MR_FUJIS_HOUSE_1_3", "POKEMON_MR_FUJIS_HOUSE_6_4",
                                 "MRFUJISHOUSE_MR_FUJI"]},
        {"MR_FUJIS_HOUSE|2,1": ["MRFUJISHOUSE_MR_FUJI"]},
        "Retrieve the Pokemon Flute from Mr. Fuji")
ck("...nor are his Pokemon, once Mr. Fuji himself was pressed", r == [], r)
r = run({"BILLS_HOUSE|0,2": ["POKEMON_BILLS_HOUSE_6_5"]}, {}, "Talk to Bill")
ck("the Pokemon in Bill's house still stands for Bill",
   r == [("BILLS_HOUSE|0,2", "POKEMON_BILLS_HOUSE_6_5")], r)
r = run({"MR_FUJIS_HOUSE|2,1": ["MRFUJISHOUSE_MR_FUJI"]}, {},
        "Retrieve the Pokemon Flute from Mr. Fuji")
ck("Mr. Fuji himself, never pressed, still refuses it",
   r == [("MR_FUJIS_HOUSE|2,1", "MRFUJISHOUSE_MR_FUJI")], r)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
raise SystemExit(1 if failed else 0)

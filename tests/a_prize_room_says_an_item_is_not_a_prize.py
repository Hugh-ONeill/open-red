#!/usr/bin/env python3
"""A prize room whose counters were all read says an item none lists is not a
prize there.

Run 66, 2026-10-25, leg "Defeat Sabrina", step get_secret_key {has_item
SECRET_KEY} "from the prize machine in the Game Corner": the three Celadon
vendors had been read (ABRA ... PORYGON, TM23/TM15/TM50) and the run wrote
"the Secret Key is not available with my current 2044 coins" and went back
to the slots to win more.

Pinned: the plan naming SECRET_KEY in the prize room with every vendor read
gets the note; a listed prize does not; an unread vendor in the room holds
it back; the mart shelf note is unchanged.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ROOM = "GAME_CORNER_PRIZE_ROOM"
PZ = {"TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_1": ["ABRA (180 coins)", "CLEFAIRY (500 coins)", "NIDORINA (1200 coins)"],
      "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_2": ["DRATINI (2800 coins)", "SCYTHER (5500 coins)", "PORYGON (9999 coins)"],
      "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_3": ["TM23 (3300 coins)", "TM15 (5500 coins)", "TM50 (7700 coins)"]}

def rig(prizes, seen):
    ex = E.Executor.__new__(E.Executor)
    ex._shelves = {}
    ex._prize_lists = {ROOM: dict(prizes)}
    ex.sightings = {f"{ROOM}|0,3": list(seen)}
    return ex

OBS = {"map": {"id": ROOM}}
ex = rig(PZ, list(PZ))
t = ex._shelf_note("I will win coins and buy the SECRET KEY from the prize vendors.", OBS)
ck("the Secret Key, listed by no counter, is said not to be a prize here",
   "SECRET_KEY" in t and "not a prize here at any number of coins" in t, t)
t = ex._shelf_note("I will buy a PORYGON with my coins.", OBS)
ck("a listed prize gets no note", t == "", t)
ex = rig({k: v for k, v in PZ.items() if not k.endswith("_3")}, list(PZ))
t = ex._shelf_note("I will buy the SECRET KEY.", OBS)
ck("an unread counter in the room holds the note back", t == "", t)

ex = E.Executor.__new__(E.Executor)
ex._shelves = {"CELADON_MART_2F": ["POTION", "SUPER_POTION"]}
ex._shelf_reads = {"CELADON_MART_2F": {"n": 3}}
ex._prize_lists = {}
t = ex._shelf_note("I will buy FRESH WATER here.", {"map": {"id": "CELADON_MART_2F"}})
ck("the mart shelf note still speaks", "never listed it in 3 reading(s)" in t, t)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

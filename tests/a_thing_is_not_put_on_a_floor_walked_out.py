#!/usr/bin/env python3
"""A sentence that puts a thing on a floor the run has walked to the end of,
with nothing left on it, is refused by the rungs that write sentences.

Run 60, 2026-10-22: the wording rung rewrote "Retrieve the Secret Key from
the Pokemon Mansion" into "... Mansion 1F" ("the Secret Key is located on
the 1st floor, specifically in the south section") with both parts of 1F
walked to their edges and both its item balls taken; seven plans went to 1F
while the key sat in the basement's unseen corner (user: "it shouldnt be
able to set that 1F is where it is after 1F has been *entirely* explored").

Pinned: a floor whose every part has no seen ground ending and nothing left
untouched is refused; one with unseen ground, or something sighted and not
taken, is not; a sentence naming no floor is not; one naming no item is
not; and both the wording rung and the missing-rung insert ask it.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


M = "POKEMON_MANSION_"
LEDGER = {
    "visits": {M + "1F|1,1": 9, M + "1F|12,14": 4, M + "2F|10,1": 6,
               M + "B1F|10,9": 3, M + "B1F|8,1": 1, M + "3F|1,1": 5},
    "frontier_here": {M + "1F|1,1": 0, M + "1F|12,14": 0, M + "2F|10,1": 8,
                      M + "B1F|10,9": 0, M + "B1F|8,1": 12, M + "3F|1,1": 0},
    "sightings": {M + "1F|1,1": ["ITEM_POKEMON_MANSION_1F_14_3", "SWITCH_POKEMON_MANSION_1F_2_5",
                                 "SIGN_POKEMON_MANSION_1F_3_3"],
                  M + "1F|12,14": ["ITEM_POKEMON_MANSION_1F_18_21"],
                  M + "3F|1,1": ["ITEM_POKEMON_MANSION_3F_1_16"]},
    "touched": {M + "1F|1,1": ["ITEM_POKEMON_MANSION_1F_14_3", "SWITCH_POKEMON_MANSION_1F_2_5"],
                M + "1F|12,14": ["ITEM_POKEMON_MANSION_1F_18_21"]},
}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(LEDGER, f)
L = f.name

r = A.names_an_emptied_floor("Retrieve the Secret Key from the Pokemon Mansion 1F", L)
ck("a floor walked out with everything taken is refused",
   r and "POKEMON_MANSION_1F" in r and "SECRET_KEY was not among them" in r, r)
ck("...an unread sign does not keep it open", r is not None)
ck("a floor with seen ground still ending is not",
   A.names_an_emptied_floor("Retrieve the Secret Key from the Pokemon Mansion B1F", L) is None)
ck("...nor one with unseen ground in its only stood part",
   A.names_an_emptied_floor("Retrieve the Secret Key from the Pokemon Mansion 2F", L) is None)
ck("a floor with an item ball still lying there is not",
   A.names_an_emptied_floor("Retrieve the Secret Key from the Pokemon Mansion 3F", L) is None)
L2 = dict(LEDGER)
L2["visits"] = dict(LEDGER["visits"], **{M + "2F|6,1": 4})
L2["frontier_here"] = dict(LEDGER["frontier_here"], **{M + "2F|10,1": 0, M + "2F|6,1": 0})
L2["sightings"] = dict(LEDGER["sightings"], **{M + "2F|10,1": ["SWITCH_POKEMON_MANSION_2F_2_11"],
                                               M + "2F|6,1": ["SWITCH_POKEMON_MANSION_2F_2_11"]})
L2["touched"] = dict(LEDGER["touched"], **{M + "2F|6,1": ["SWITCH_POKEMON_MANSION_2F_2_11"]})
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f2:
    json.dump(L2, f2)
ck("a thing pressed from one part is pressed for the whole floor",
   A.names_an_emptied_floor("Retrieve the Secret Key from the Pokemon Mansion 2F", f2.name) is not None)
S = "SILPH_CO_5F|20,0"
L3 = {"visits": {S: 8}, "frontier_here": {S: 0}, "region_seen": {S: 15},
      "sightings": {S: ["SILPHCO5F_ROCKER"]}, "touched": {S: ["SILPHCO5F_ROCKER"]}}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f3:
    json.dump(L3, f3)
ck("a floor whose kept count still has unseen ground is not (run 68, Silph 5F)",
   A.names_an_emptied_floor("Obtain the Card Key from Silph Co 5F", f3.name) is None)
L4 = dict(L3, region_seen={S: 0}, seen_far={S: ["ITEM_SILPH_CO_5F_21_16"]})
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f4:
    json.dump(L4, f4)
ck("...nor one with a ball seen across a wall and never taken",
   A.names_an_emptied_floor("Obtain the Card Key from Silph Co 5F", f4.name) is None)
L5 = dict(L4, seen_far={})
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f5:
    json.dump(L5, f5)
ck("...and with both gone it is refused",
   A.names_an_emptied_floor("Obtain the Card Key from Silph Co 5F", f5.name) is not None)
ck("a sentence naming no floor is not",
   A.names_an_emptied_floor("Retrieve the Secret Key from the Pokemon Mansion", L) is None)
ck("a sentence naming no item is not",
   A.names_an_emptied_floor("Explore the Pokemon Mansion 1F", L) is None)
src = (ROOT / "planner" / "author.py").read_text()
ck("the wording rung asks it", "_ef = names_an_emptied_floor(new, observed)" in src)
ck("the missing-rung insert asks it", "_ef = names_an_emptied_floor(ins, observed)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

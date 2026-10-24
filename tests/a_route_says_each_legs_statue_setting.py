#!/usr/bin/env python3
"""When go's replay stops, its line says the switch statue setting each leg
still ahead was walked with, if those settings are not all one.

Run 62, 2026-10-24: the walked way from Mansion 1F to B1F runs up 2F's (6,1)
stair, walked with the statues UNPRESSED, and down 3F's hole (16,14), walked
PRESSED (probed on a copy of the leg 45 checkpoint: the stair is "no path"
PRESSED, the hole is "no path" UNPRESSED). go stopped at whichever leg
disagreed with the statues and named that leg's setting alone, and the run
flipped and re-ran go, round after round, never shown that the record asks
for a flip partway.

Pinned: legs walked under two settings are each named with their setting,
from the stopped leg on; legs all walked one way add nothing; legs with no
setting on record add nothing; the replay's stop line carries it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

F1, F2, F3 = "POKEMON_MANSION_1F|1,1", "POKEMON_MANSION_2F|10,1", "POKEMON_MANSION_3F|1,1"
S1, B1 = "POKEMON_MANSION_1F|12,14", "POKEMON_MANSION_B1F|10,9"
PATH = [("6,1", F3), ("16,14", S1), ("21,23", B1)]


def words(stair, hole, stairs=None):
    ex = object.__new__(E.Executor)
    ex.explored = {
        F1: {"5,10": {"to": F2, "n": 3, "switches": "PRESSED"}},
        F2: {"6,1": {"to": F3, "n": 2, **({"switches": stair} if stair else {})}},
        F3: {"16,14": {"to": S1, "n": 4, **({"switches": hole} if hole else {})}},
        S1: {"21,23": {"to": B1, "n": 2, **({"switches": stairs} if stairs else {})}},
    }
    return ex._route_switch_words(F2, PATH)


w = words("UNPRESSED", "PRESSED", "PRESSED")
ck("legs walked two ways are each named with their setting",
   f"{F2} --6,1--> {F3} UNPRESSED" in w and f"{F3} --16,14--> {S1} PRESSED" in w
   and f"{S1} --21,23--> {B1} PRESSED" in w, w)
ck("...in the order they are walked", w.find("--6,1-->") < w.find("--16,14-->") < w.find("--21,23-->"), w)
ck("...and it says nothing of what to press", "press " not in w.lower().replace("pressed", ""), w)
ck("legs all walked one way add nothing", words("PRESSED", "PRESSED", "PRESSED") == "")
ck("legs with no setting on record add nothing", words(None, None) == "")
ck("one leg with a setting and the rest without adds nothing", words("UNPRESSED", None) == "")

src = (ROOT / "planner" / "executor.py").read_text()
ck("the replay's stop line carries it",
   "+ self._route_switch_words(frm, path[_hop_i:])" in src
   and "for _hop_i, (key, nxt) in enumerate(path):" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

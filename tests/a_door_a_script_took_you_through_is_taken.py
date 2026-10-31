#!/usr/bin/env python3
"""A doorway a script took you through is written as taken.

Run 69, 2026-10-31: paying the Safari attendant took the run into the Center
four times by way of a menu answer. Only doors and seams wrote edges, so the
gate's (3,0) stayed "never taken" and shut, and every Safari area read "no
walked route from here", the Secret House and its HM03 with them.

Pinned: the arrival writes the one doorway whose table destination is the
map arrived on, both tiles, with by_script counted and shut lifted; a heal
through an open door writes the edge without by_script; nothing is written
when the table names no doorway, or two apart; the ledger row says how it
was taken.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.index('self.log("script_transition", frm=self._came_from,')
ck("the script arrival writes its doorway", "self._note_script_door(self._came_from," in src[i:i + 1500])

def bare():
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {}
    ex.door_dests = {}
    ex.log = lambda *a, **k: None
    ex._save_memory = lambda: None
    return ex

ex = bare()
ex.door_dests = {"SAFARI_ZONE_GATE": {"3,5": "LAST_MAP", "4,5": "LAST_MAP",
                                      "3,0": "SAFARI_ZONE_CENTER", "4,0": "SAFARI_ZONE_CENTER"}}
ex.explored = {"SAFARI_ZONE_GATE|3,0": {"3,0": {"n": 0, "to": None, "shut": True, "shut_at": [1]}}}
ex._note_script_door("SAFARI_ZONE_GATE|3,0", "SAFARI_ZONE_CENTER|22,10", at={"x": 3, "y": 1})
g = ex.explored["SAFARI_ZONE_GATE|3,0"]
ck("both tiles of the doorway lead to the Center",
   g["3,0"]["to"] == g["4,0"]["to"] == "SAFARI_ZONE_CENTER|22,10", g)
ck("the shut mark is lifted", "shut" not in g["3,0"], g)
ck("the shut tile counts a script crossing", g["3,0"].get("by_script") == 1, g)
ck("the doors back to the city are untouched", "3,5" not in g, g)
ex._note_script_door("SAFARI_ZONE_GATE|3,0", "SAFARI_ZONE_CENTER|22,10", at={"x": 4, "y": 2})
ck("a second crossing counts again", g["3,0"].get("by_script") == 2 and g["3,0"]["n"] == 2, g)

ex = bare()
ex.door_dests = {"VIRIDIAN_CITY": {"23,25": "VIRIDIAN_POKECENTER"}}
ex._note_script_door("VIRIDIAN_CITY|17,0", "VIRIDIAN_POKECENTER|0,3", at={"x": 23, "y": 26})
e = ex.explored["VIRIDIAN_CITY|17,0"]["23,25"]
ck("a heal through an open door writes the edge", e["to"] == "VIRIDIAN_POKECENTER|0,3", e)
ck("...without saying a walk is turned back", "by_script" not in e, e)

ex = bare()
ex.door_dests = {"X": {"1,1": "Y", "9,9": "Y"}}
ex._note_script_door("X|0,0", "Y|0,0", at={"x": 1, "y": 2})
ck("two doorways apart to the same map: nothing written", ex.explored == {}, ex.explored)
ex._note_script_door("X|0,0", "Z|0,0", at={"x": 1, "y": 2})
ck("no doorway to that map: nothing written", ex.explored == {}, ex.explored)
ex._note_script_door("None|None", "Y|0,0", at={"x": 1, "y": 2})
ck("no source map: nothing written", ex.explored == {}, ex.explored)

# the clock running out moves you to the gate from anywhere in the park
ex = bare()
ex.door_dests = {"SAFARI_ZONE_CENTER": {"14,25": "SAFARI_ZONE_GATE", "15,25": "SAFARI_ZONE_GATE"}}
ex._note_script_door("SAFARI_ZONE_CENTER|14,0", "SAFARI_ZONE_GATE|3,0", at={"x": 14, "y": 2})
ck("a script arrival from far off the doorway writes nothing", ex.explored == {}, ex.explored)
ex._note_script_door("SAFARI_ZONE_CENTER|14,0", "SAFARI_ZONE_GATE|3,0", at={})
ck("...nor with no place on record", ex.explored == {}, ex.explored)
ex._note_script_door("SAFARI_ZONE_CENTER|22,10", "SAFARI_ZONE_GATE|3,0", at={"x": 14, "y": 24})
ck("...but from beside it, it does",
   ex.explored.get("SAFARI_ZONE_CENTER|22,10", {}).get("14,25", {}).get("to") == "SAFARI_ZONE_GATE|3,0", ex.explored)
ck("the arrival passes where the party stood",
   'at=((_src_obs or {}).get("player") or {}))' in src)

lsrc = (ROOT / "planner" / "ledger.py").read_text()
ck("the ledger row says how it was taken",
   'answering the one who stops you at it' in lsrc and 'walked onto alone, it turns you back' in lsrc)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

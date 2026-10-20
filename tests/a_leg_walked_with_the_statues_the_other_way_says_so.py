#!/usr/bin/env python3
"""A walked leg carries the switch-statue state it was walked in, and a go
that stalls on it says the statues stand the other way now; a step going
back to a state it has already been in is not "something changed".

Run 59, 2026-10-20, Pokemon Mansion: 2F's stairs to 3F want the statues
one way and 3F's holes the other, so the walked route 1F -> 2F -> 3F ->
hole -> 1F needs a press partway, and `go` stalled at the leg walked in the
other state with no word of why (user: "the state to get to the stairs on
2F is different from the state required to get to the holes on 3F"). Each
press flipped EVENT_MANSION_SWITCH_ON, so every repeat of the same plan was
echoed "-> something changed" for hours (user: "its also not getting that
its done exactly what its planning to do ... with no changes except the
switch state"). Synthetic + source pins.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, det=""): checks.append((n, bool(ok), det))

ex = object.__new__(E.Executor)
ex.explored = {"POKEMON_MANSION_2F|10,1": {"6,1": {"to": "POKEMON_MANSION_3F|1,1",
                                                   "n": 3, "switches": "UNPRESSED"}}}
on = {"map": {"id": "POKEMON_MANSION_2F", "switches_on": True}}
off = {"map": {"id": "POKEMON_MANSION_2F", "switches_on": False}}
w = ex._switch_words("POKEMON_MANSION_2F|10,1", "6,1", on)
ck("a leg walked UNPRESSED, statues PRESSED now, says both",
   "walked with this building's switch statues UNPRESSED" in w and "PRESSED now" in w, w)
ck("...and nothing when they stand as they did", ex._switch_words("POKEMON_MANSION_2F|10,1", "6,1", off) == "")
ck("...nor on a floor with no lever",
   ex._switch_words("POKEMON_MANSION_2F|10,1", "6,1", {"map": {"id": "X"}}) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("the state is kept with the edge when it is walked",
   'e["switches"] = "PRESSED" if _sw0 else "UNPRESSED"' in src)
ck("go's stalled leg and its blocked hop both say it",
   "+ self._switch_words(frm, key, o)" in src and "+ self._switch_words(_src, _k, obs)" in src)

bad = [c for c in checks if not c[1]]
for n, ok, det in checks: print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"  {det}"))
raise SystemExit(1 if bad else 0)

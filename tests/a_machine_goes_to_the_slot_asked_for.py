#!/usr/bin/env python3
"""A TM/HM goes to the party slot the op names, and a refusal that names
someone else is said as the wrong pick it is.

Run 31, 2026-10-03, on the new base: use_item(HM_CUT, slot=3) taught (tried
to teach) GRAVELER in slot 1. The A presses riding through "Booted up an
HM!" landed as the party list appeared, on the cursor the game had left on
slot 1; the game said "GUMBO is not compatible with CUT." and the op
reported "IVYSAUR is NOT COMPATIBLE", for an hour, with the Vermilion Gym
behind a Cut tree (user: "trouble with the surge leg"). Verified in game
on that run's checkpoint: IVYSAUR learns CUT over TACKLE.

Source pins (the game check is the boot above, recorded in the commit)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
lua = (ROOT / "harness/shim.lua").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))
i = lua.index("ride to the party picker")
ck("the list's remembered cursor is set to the model's slot before the ride",
   "G.partyMenuSavedIndex = _want" in lua[i - 900:i])
ck("the teach loop puts the cursor on the slot whenever the list is up",
   'if t and t.screenId == "PartyMenu" and not t.newMoveId\n         and t.index ~= slot then' in lua)
ck("a refusal naming someone else is said as a wrong pick, not as the species'",
   "the game's machine screen picked a different" in lua
   and "incompatible_said" in lua)
bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(1 if bad else 0)

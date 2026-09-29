#!/usr/bin/env python3
"""A leg naming an item the game has said to you is not VOID as "not an item".

"Obtain the CARD KEY from the Team Rocket executive in Silph Co." was struck
out: "The Card Key is not an item that can be obtained or held in the game;
it is a plot device" with Silph's doors on record saying "Darn! It needs a
CARD KEY!" (run 19, 2026-09-29). A VOID saying the thing is ELSEWHERE is a
different claim and is not touched.

Synthetic.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


d = Path(tempfile.mkdtemp(prefix="voidkey_"))
(d / "run").mkdir()
(d / "plans").mkdir()
(d / "run/obs.json").write_text(json.dumps({"flags": []}))
led = d / "explored.json"
led.write_text(json.dumps({
    "visits": {"SILPH_CO_2F|20,0": 3, "SILPH_CO_5F|20,0": 2},
    "hints": {"SILPH_CO_2F|20,0": ["DOOR_SILPH_CO_2F_4_4: Darn! It needs a CARD KEY!"]}}))
here = os.getcwd()
os.chdir(d)
try:
    g = "Obtain the CARD KEY from the Team Rocket executive in Silph Co."
    why = ("The Card Key is not an item that can be obtained or held in the game; "
           "it is a plot device/event that grants access to the elevator.")
    r = A.void_refused_why(g, str(led), plans_dir="plans", why=why)
    ck("a VOID calling a named item unreal is refused", "CARD_KEY" in r and "Darn!" in r, r)
    r = A.void_refused_why(g, str(led), plans_dir="plans",
                           why="The Card Key is found on the 5th floor, not from an executive.")
    ck("a VOID saying it is elsewhere is not refused by this", r == "", r)
    r = A.void_refused_why("Retrieve the Secret Key from the Rocket Hideout", str(led),
                           plans_dir="plans",
                           why="The Secret Key does not exist in the Rocket Hideout.")
    ck("an item the game never named is not refused by this", "SECRET" not in r, r)
    r = A.void_refused_why("Obtain the BIKE VOUCHER", str(led), plans_dir="plans",
                           why="The bike voucher is not an item that exists here.")
    ck("...nor one never heard", "BIKE" not in r, r)
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

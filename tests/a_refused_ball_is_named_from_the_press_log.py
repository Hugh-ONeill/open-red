#!/usr/bin/env python3
"""A ball a full bag refused is named, by its cell, from the press log when
its hint was kept as "someone".

Run 67, 2026-10-28: the Secret Key, ITEM_POKEMON_MANSION_B1F_5_13, was
refused before _refused_balls existed; its hint read "someone: No more
room for items!", the refused line said "someone in POKEMON_MANSION_B1F",
and the run searched the Mansion's upper floors for the key. The press
log kept the ball by name.

Pinned: the press log's ITEM_ no-room press is named with its cell; a ball
gone since is not; the vague "someone" row for that map is dropped; a
"someone" refusal elsewhere stays. Synthetic.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def line(gone=()):
    ex = E.Executor.__new__(E.Executor)
    ex._press_log = {"POKEMON_MANSION_B1F|8,1": [
        ["SWITCH_POKEMON_MANSION_B1F_20_3", "A secret switch! Press it?"],
        ["ITEM_POKEMON_MANSION_B1F_5_13", "No more room for items!"]]}
    ex.hints = {"POKEMON_MANSION_B1F|8,1": ["someone: No more room for items!"],
                "SILPH_CO_7F|1,1": ["someone: There's no more room for items!"]}
    ex._gone = {"POKEMON_MANSION_B1F|8,1": set(gone)}
    ex._refused_balls, ex._refused_gifts, ex._item_from = {}, {}, {}
    ex.visits = {}
    ex._route = lambda a, b: None
    return ex._refused_gifts_line({"bag": {"A": 1}, "map": {"id": "CINNABAR_ISLAND", "region": "10,0"}})

t = line()
ck("the ball is named by its cell", "a ball at (5,13) in POKEMON_MANSION_B1F" in t, t)
ck("...and the vague row for that map is dropped", "someone in POKEMON_MANSION_B1F" not in t, t)
ck("...while a someone elsewhere stays", "someone in SILPH_CO_7F" in t, t)
t = line(gone=["ITEM_POKEMON_MANSION_B1F_5_13"])
ck("a ball picked up since is not named", "(5,13)" not in t, t)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
sys.exit(1 if bad else 0)

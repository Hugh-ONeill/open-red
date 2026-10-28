#!/usr/bin/env python3
"""A ball whose last answer was "No more room for items!" is not counted as
touched when the record loads, whatever wrote the touch.

Run 67, 2026-10-28: the Secret Key, Mansion B1F (5,13), sat in touched for
POKEMON_MANSION_B1F|8,1 though every press of it was refused, so the floor
never listed it as untouched and the run searched upstairs for the key.

Pinned: such a ball is dropped from the loaded touches; a ball later taken
(in gone) and one whose last answer was something else are not.
"""
import json, os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
R = "POKEMON_MANSION_B1F|8,1"
d = tempfile.mkdtemp()
mem = Path(d) / "explored.json"
mem.write_text(json.dumps({
    "touched": {R: ["ITEM_POKEMON_MANSION_B1F_5_13", "ITEM_POKEMON_MANSION_B1F_5_4",
                    "ITEM_POKEMON_MANSION_B1F_10_2", "SWITCH_POKEMON_MANSION_B1F_20_3"]},
    "gone": {R: ["ITEM_POKEMON_MANSION_B1F_5_4"]},
    "press_log": {R: [["ITEM_POKEMON_MANSION_B1F_5_13", "No more room for items!"],
                      ["ITEM_POKEMON_MANSION_B1F_5_4", "No more room for items!"],
                      ["ITEM_POKEMON_MANSION_B1F_10_2", "No more room for items!"],
                      ["ITEM_POKEMON_MANSION_B1F_10_2", "KODA found TM_X!"]]}}))
ex = object.__new__(E.Executor)
ex.MEMORY, ex._harness_rev = mem, "x"
for _ in range(120):
    try:
        ex._load_memory()
        break
    except AttributeError as e:
        n = str(e).split("attribute '")[1].rstrip("'")
        setattr(ex, n, {} if not n.startswith("_mark") else None)
t = (getattr(ex, "_tried_objs", {}) or {}).get(R, set())
ck("a ball refused for room is not touched", "ITEM_POKEMON_MANSION_B1F_5_13" not in t, t)
ck("...one taken since stays touched", "ITEM_POKEMON_MANSION_B1F_5_4" in t, t)
ck("...one whose last answer was a pickup stays", "ITEM_POKEMON_MANSION_B1F_10_2" in t, t)
ck("...and other things are left alone", "SWITCH_POKEMON_MANSION_B1F_20_3" in t, t)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
sys.exit(1 if bad else 0)

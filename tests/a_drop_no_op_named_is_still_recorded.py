#!/usr/bin/env python3
"""A drop through a hole that no op named is still recorded as a way.

Run 36, 2026-10-05: a walk a trainer fight interrupted carried on, stepped
onto Pokemon Mansion 3F's (17,14) and dropped into 1F's sealed stairs room;
no op text named the cell, the executor logged crossed_door_unnamed and
recorded nothing, and every `go` back answered "no walked way ... is known".
The shim's steps.log had the cell. Behavioural, on that log's real lines.
"""
import json, os, sys, tempfile
from pathlib import Path
d = tempfile.mkdtemp()
os.environ["RED_BRIDGE_DIR"] = d
(Path(d) / "steps.log").write_text(
    "1791179691 POKEMON_MANSION_3F 16 13\n"
    "1791179691 POKEMON_MANSION_3F 17 13\n"
    "1791179691 POKEMON_MANSION_3F 17 14\n"
    "1791179691 POKEMON_MANSION_1F 16 14\n"
    "1791179692 POKEMON_MANSION_1F 16 1")       # a line cut mid-write
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, det=""): checks.append((n, bool(ok), det))
ck("the last cell on the floor before the landing is read back",
   E.Executor._last_cell_on("POKEMON_MANSION_3F", "POKEMON_MANSION_1F") == (17, 14),
   E.Executor._last_cell_on("POKEMON_MANSION_3F", "POKEMON_MANSION_1F"))
ck("...and nothing for a pair the log never had",
   E.Executor._last_cell_on("POKEMON_MANSION_2F", "POKEMON_MANSION_1F") is None)

src = (ROOT / "planner/executor.py").read_text()
i = src.index("WITH NOTHING NAMED AT ALL, THE LAST CELL THE FLOOR SAW")
blk = src[i:i + 2200]
ck("an unnamed crossing on a floor with holes asks steps.log",
   "self._last_cell_on(" in blk and "if key is None and src.split" in blk)
ck("...files it under the hole group's first tile, as a named drop is",
   'key = f"{_grp[0][1]},{_grp[0][0]}"' in blk
   and 'found="steps.log"' in blk)
ck("...and only then gives up as unnamed",
   blk.index("self._last_cell_on(") < src.index('self.log("crossed_door_unnamed"', i) - i + 0)
bad = [c for c in checks if not c[1]]
for n, ok, det in checks: print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"  {det}"))
raise SystemExit(1 if bad else 0)

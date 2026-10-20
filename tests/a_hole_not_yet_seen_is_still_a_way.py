#!/usr/bin/env python3
"""A drop through a hole the observation had not listed yet is recorded.

Run 59, 2026-10-20: a sweep on Pokemon Mansion 3F stepped onto (16,14)
before that hole was ever on screen and landed on 1F at (16,14). The
listed holes are only those seen, so the steps.log fallback found the cell
and no hole to match it, logged crossed_door_unnamed and filed nothing, and
`go` from 1F's front hall answered "no walked way ... to POKEMON_MANSION_
1F|12,14 is known" for hours while the model flipped the statue (user: "it
doesnt seem to get why 'go' wont work"). Behavioural on the run's own
steps.log lines; the rule is pinned in source.
"""
import os, sys, tempfile
from pathlib import Path
d = tempfile.mkdtemp()
os.environ["RED_BRIDGE_DIR"] = d
(Path(d) / "steps.log").write_text(
    "1792508910 POKEMON_MANSION_3F 16 12\n"
    "1792508910 POKEMON_MANSION_3F 16 13\n"
    "1792508910 POKEMON_MANSION_3F 16 14\n"
    "1792508910 POKEMON_MANSION_1F 16 14\n")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, det=""): checks.append((n, bool(ok), det))
ck("the cell the party stood on before the landing is read back",
   E.Executor._last_cell_on("POKEMON_MANSION_3F", "POKEMON_MANSION_1F") == (16, 14))

src = (ROOT / "planner/executor.py").read_text()
i = src.index("...AND A HOLE NOT ON THE LIST YET IS STILL A HOLE.")
blk = src[i:i + 1600]
ck("an unlisted cell, not a doorway, with the landing on the same cell, is a fall",
   "key is None and _cell is not None and _door is None" in blk
   and '(_pl.get("x"), _pl.get("y")) == tuple(_cell)' in blk)
ck("...filed under that cell", 'key = f"{_cell[0]},{_cell[1]}"' in blk)
ck("...before the crossing is given up as unnamed",
   i < src.index('self.log("crossed_door_unnamed"', i))

bad = [c for c in checks if not c[1]]
for n, ok, det in checks: print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"  {det}"))
raise SystemExit(1 if bad else 0)

#!/usr/bin/env python3
"""The bag line names the held kinds the model's own outline still asks for.

Run 71, 2026-11-03: on Pokemon Tower 3F with a full bag the model tossed
MOON_STONE as "not needed" to make room for the Poke Flute, while its own
outline still held the pushed leg "Obtain the Moon Stone". Nothing beside the
bag tied the stone to the plan. The user chose the catch-ahead shape
(2026-11-04): the model's own outline words, read back, nothing else.

Pinned: items_named_ahead finds a held item a leg after the high-water mark
names by all its words; a leg already behind the mark does not count; an
item no leg names is not listed; the bag-pressure line carries it.
Synthetic.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import outline_ahead as OA  # noqa: E402
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

tmp = Path(tempfile.mkdtemp())
plans, run = tmp / "plans", tmp / "run"
plans.mkdir(); run.mkdir()
(plans / "outline.txt").write_text(
    "Pick a starter\nObtain the Silph Scope\nClear the Pokemon Tower\n"
    "Obtain the Moon Stone\nDefeat Koga for the Soul Badge\n")
(run / "outline_leg").write_text("2\n")

got = OA.items_named_ahead(plans, run, ["MOON_STONE", "SILPH_SCOPE", "NUGGET"])
ck("a leg ahead names the Moon Stone",
   ("MOON_STONE", 4, "Obtain the Moon Stone") in got, got)
ck("a leg already behind the mark does not count",
   not any(it == "SILPH_SCOPE" for it, _p, _l in got), got)
ck("an item no leg names is not listed", not any(it == "NUGGET" for it, _p, _l in got), got)

E.PLANS, E.RUN = plans, run
ex = E.Executor.__new__(E.Executor)
ex.visits, ex.explored = {}, {}
ex._where = lambda o: "POKEMON_TOWER_3F|9,1"
bag = {f"ITEM{i}": 1 for i in range(19)}
bag["MOON_STONE"] = 1
line = ex._bag_pressure_line({"bag": bag, "key_items": []})
ck("the bag line says the outline still names it",
   "YOUR OWN OUTLINE, STILL AHEAD, NAMES MOON_STONE (leg 4: \"Obtain the Moon Stone\")" in line,
   line[:400])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

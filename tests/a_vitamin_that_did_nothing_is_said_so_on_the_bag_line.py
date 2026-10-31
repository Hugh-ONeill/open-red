#!/usr/bin/env python3
"""A vitamin that came to nothing is named on the bag line, with the Pokemon.

Run 69, 2026-10-31, Safari Zone North with the bag at 20 of 20: CARBOS on
RAICHU said "It won't have any effect.", the bag line went on listing CARBOS
among the singles a use spends with nothing lost, the result reached the page
only as "use_item: It won't have any effect.", and CARBOS on RAICHU was sent
again three rounds later.

Pinned: the no-effect result is recorded by item and slot where the strike
is; the bag line names the item, the Pokemon and the game's words; an item
with no such record reads as before.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.index("if _noeff:\n                self._strike(")
blk = src[i:i + 1400]
ck("the no-effect use is recorded beside its strike",
   '"_noeff_uses"' in blk and 'str(step["item"])' in blk and "[_sl] = str(_sp)" in blk, blk)

ex = E.Executor.__new__(E.Executor)
ex.visits, ex.explored = {}, {}
ex._where = lambda o: "SAFARI_ZONE_NORTH|1,1"
o = {"bag": {**{f"K{i}": 1 for i in range(17)}, "CARBOS": 1, "PROTEIN": 1, "GREAT_BALL": 10},
     "key_items": []}
t0 = ex._bag_pressure_line(o)
ck("with no record, nothing is said of it", "won't have any effect" not in t0, t0)
ex._noeff_uses = {"CARBOS": {1: "RAICHU"}}
t = ex._bag_pressure_line(o)
ck("the item and the Pokemon it came to nothing on are named",
   "CARBOS has been used on RAICHU (slot 1) and the game said \"It won't have any effect.\"" in t, t)
ck("...and that nothing was spent", "nothing was spent and the slot stayed full" in t, t)
ck("an item without a record is not named so", "PROTEIN has been used" not in t, t)
ck("both still stand in the singles list", "nothing lost from the party: CARBOS, PROTEIN" in t, t)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

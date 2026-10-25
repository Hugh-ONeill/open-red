#!/usr/bin/env python3
"""A fossil, clipboard, book or paper beside a door is a thing, not a person.

Run 66, 2026-10-25: Mt Moon B2F's exit ladder (5,7) read "the way onto it is
blocked; nearest person FOSSIL_MT_MOON_B2F_12_6, 8 cells off" on every
floor's page. The fossils lie across the corridor to it, and the run left by
the west mouth three times, sure the far exit was somewhere outside, before
it picked one up. The ledger fixed this wording for the same fossil on
2026-08-29; the executor's ways-never-taken line had not.

Pinned: the word follows the name's prefix; both executor lines use it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

for nm in ("FOSSIL_MT_MOON_B2F_12_6", "CLIPBOARD_SILPH_CO_1F_3_2", "BOOK_OAKS_LAB_2_1", "PAPER_X_1_1"):
    ck(f"{nm} is a thing", E._nearest_kind(nm) == "thing")
for nm in ("MTMOONB2F_SUPER_NERD", "CERULEANCITY_COP", "", None):
    ck(f"{nm!r} is a person", E._nearest_kind(nm) == "person")
src = (ROOT / "planner" / "executor.py").read_text()
ck("both blocked-door lines use the word", src.count("nearest {_nearest_kind(who)}") == 2
   and "nearest person {who}" not in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

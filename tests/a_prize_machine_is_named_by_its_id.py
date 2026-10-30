#!/usr/bin/env python3
"""A prize counter's machine rows are named by the id the bag carries.

Run 68, 2026-10-30: the prize room listed "TM23 (3300 coins)" and the run
went to buy "TM23 (which is TM_PAY_DAY in some versions)"; TM23 is
TM_DRAGON_RAGE. Pinned: a TM row gains its id and keeps number and price;
non-machine rows are unchanged; an older ledger is named at load; the
shelf note's not-a-prize line no longer exempts machines.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ck("a TM row is named", E._prize_row_named("TM23 (3300 coins)") == "TM_DRAGON_RAGE (TM23, 3300 coins)",
   E._prize_row_named("TM23 (3300 coins)"))
ck("...a bare number too", E._prize_row_named("TM50") == "TM_SUBSTITUTE (TM50)", E._prize_row_named("TM50"))
ck("a Pokemon row is unchanged", E._prize_row_named("ABRA (180 coins)") == "ABRA (180 coins)")
ck("an unknown number is unchanged", E._prize_row_named("TM99 (1 coins)") == "TM99 (1 coins)")
src = (ROOT / "planner" / "executor.py").read_text()
ck("rows are named when recorded", "rows = [_prize_row_named(x) for x in rows]" in src)
ck("...and when an older ledger loads", "[_prize_row_named(_x) for _x in (_rows or [])]" in src)
i = src.find("_offered = \" \".join(\" \".join(r) for r in _pz.values()).upper()")
ck("the prize note no longer exempts machines", i > 0 and 'startswith(("TM_", "HM_"))' not in src[i:i + 600])
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)

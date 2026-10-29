#!/usr/bin/env python3
"""A region's heard-words ledger keeps more than sixteen lines, and the round
speech path files the same words once whoever they were filed under.

Run 68, 2026-10-29: Fuchsia's ledger held each youngster's line twice (once
as "someone:"), its thirteen signs filled the rest, and the sign at (27,29),
"SAFARI ZONE WARDEN's HOME", was the line dropped; the run carried the Gold
Teeth round the Safari Zone looking for the Warden. Source pins + the cap.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
src = (ROOT / "planner" / "executor.py").read_text()
ck("the cap is one constant and above sixteen", E.HINTS_PER_REGION >= 24)
ck("no site still cuts at sixteen", "del lst[:-16]" not in src and src.count("del lst[:-HINTS_PER_REGION]") >= 3)
ck("the round speech path drops same words under another name",
   'if line not in lst and not any(\n                        l.partition(": ")[2] == _ex for l in lst):' in src)
ex = E.Executor.__new__(E.Executor)
ex.hints = {}
ex._save_memory = lambda: None
R = "FUCHSIA_CITY|2,2"
for i in range(17):
    ex._file_sweep_heard(R, f"SIGN_FUCHSIA_CITY_{i}_7", f"Name: MON{i} a long enough flavor line", {})
ex._file_sweep_heard(R, "SIGN_FUCHSIA_CITY_27_29", "SAFARI ZONE WARDEN's HOME", {})
ck("the Warden's sign survives a town of signs",
   any("WARDEN's HOME" in l for l in ex.hints[R]) and len(ex.hints[R]) == 18, len(ex.hints[R]))
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""A leg the ladder moved, reworded, inserted before or went back to
starts its round window afresh, as author.dry_tail already counts its runs.

Run 36, 2026-10-05: the chain went back to HM04, and the leg arrived with
forty dry rounds from before; the leg-dry cut ended it at the end of the
12-round grace, before the run had walked anywhere new.

Pinned: dispositions are counted by the leg's words or its named item, and
only DISPOSED rows count; the window resets when a new one has appeared
since the leg last started, and not when none has; the count is kept with
the memory. Synthetic."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_tmp = tempfile.mkdtemp()
os.environ["RED_BRIDGE_DIR"] = _tmp
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


HM = "Obtain HM04 STRENGTH from the Warden in the Safari Zone"
(Path(E.RUN) / "attempt_yield").write_text(
    f"{HM}\t53\t1\tNOTHING new while this leg ran\n"
    f"{HM}\t53\t0\tDISPOSED: gone back to from leg 57, which waits on it\n"
    f"Obtain HM04 from the Safari Zone\t49\t0\tDISPOSED: reworded to: {HM}\n"
    f"Clear Victory Road\t54\t0\tDISPOSED: a step was put before it\n")
ck("dispositions are counted by words or named item, DISPOSED rows only",
   E.Executor._dispositions_of(HM) == 2, E.Executor._dispositions_of(HM))
ck("another leg's are its own", E.Executor._dispositions_of("Clear Victory Road") == 1)
ck("no file, none", E.Executor._dispositions_of("Defeat Brock") == 0)

src = (ROOT / "planner/executor.py").read_text()
ck("the window resets when a disposition has appeared since the leg last started",
   "if _ndisp > int(_seen.get(_goal_now, 0) or 0) and self._leg_rounds:" in src
   and "self._leg_rounds = []\n            _seen[_goal_now] = _ndisp" in src)
ck("...before the attempt is counted",
   src.index("_ndisp = self._dispositions_of(_goal_now)")
   < src.index('self._leg_tries = int(getattr(self, "_leg_tries", 0)) + 1'))
ck("the count is kept with the memory",
   '"leg_disp_seen": getattr(self, "_leg_disp_seen", None) or {},' in src
   and 'self._leg_disp_seen = data.get("leg_disp_seen") or {}' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

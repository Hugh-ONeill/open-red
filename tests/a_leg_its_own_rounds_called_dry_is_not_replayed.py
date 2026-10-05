#!/usr/bin/env python3
"""A leg the executor's window just cut as dry is not replayed on the
strength of any gain at all.

Run 36, 2026-10-05: "Defeat the Pokemon League Champion", with no Strength,
was cut by the leg-dry window (40 rounds, one find) and then replayed
three times because explore's wandering had entered Pewter's museum and
the Mt Moon Pokecenter, which leg_delta reads as the world moving.

Pinned: the flag is set only by a campaign that ran and exited 2 (first or
remaining attempts), not by the dry-tail gate; the replay rule reads it.
Source pins over fresh_discovery.sh."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "fresh_discovery.sh").read_text()
ck("the script parses", subprocess.run(["bash", "-n", str(ROOT / "fresh_discovery.sh")]).returncode == 0)
ck("the dry-tail gate does not set it",
   'crc=2\n    _leg_dry_cut=0\n  else' in src)
ck("a first campaign that exits 2 sets it",
   '_leg_dry_cut=0; [ "$crc" = 2 ] && _leg_dry_cut=1' in src)
ck("so do the remaining attempts",
   '[ "$_crc2" = 2 ] && _leg_dry_cut=1' in src)
ck("the replay rule reads it",
   'if [ "${_rep:-0}" -lt 3 ] && [ "${_leg_dry_cut:-0}" != 1 ] \\\n'
   '        && python planner/leg_delta.py moved run/attempt_yield "$leg"; then' in src)
ck("and the flag is set before the replay rule is reached",
   src.index('_leg_dry_cut=0; [ "$crc" = 2 ]') < src.index('[ "${_leg_dry_cut:-0}" != 1 ]'))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

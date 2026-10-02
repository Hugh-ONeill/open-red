#!/usr/bin/env python3
"""Pressing a starter's ball reaches its yes/no question past the Pokedex page.

The updated base (2026-10-02) shows the Pokemon's Pokedex entry (DexEntryMenu)
before "So! You want ...?", and the page takes no key while the cry plays: real
audio, real seconds. The interact op's stall count ran out first and returned
"dialog still open", so the question was never reported as one and the survey
that lays all three starters side by side never ran (runs 26 and 27; user:
"the harness forcing it to look at all the choices was purposeful though").
Checked live: with this, the press answers "ASKING ... CHARMANDER?".
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sh = (ROOT / "harness/shim.lua").read_text()
i = sh.index("local function settle_dialog()")
blk = sh[i:i + 4000]
checks = []


def ck(n, ok):
    checks.append((n, bool(ok)))


ck("a ceremony screen's own page counts as progress", "local _pg = t and (t.pageIndex or t.page)" in blk)
ck("...and the cry is waited out in wall time, capped", "pcall(t.crying, t)" in blk
   and "_clock() - _t0 > 6" in blk)
j = sh.index("-- ...BUT NOT WHILE THE NEW SPECIES CRIES.")
ck("a catch waits the new species' cry out before pressing toward the nickname question",
   "pcall(t.crying, t)" in sh[j:j + 900])
fd = (ROOT / "fresh_discovery.sh").read_text()
ck("a fresh start rotates the viewer's event feed and trail",
   'mv "$_feed" "${_feed%.jsonl}.${ts}.jsonl"' in fd and 'trail.jsonl' in fd)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if failed else 0)

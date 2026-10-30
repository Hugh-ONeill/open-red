#!/usr/bin/env python3
"""A party line names each member's nickname beside its species.

Run 68, 2026-10-29: the game refused SURF with "No SURFing on GLITCHES
here!" and the run wrote "SURF failed due to a 'GLITCHES' error"; GLITCHES
was its LAPRAS, and nothing on the page said so. "deposited HUCKLE" was its
HYPNO. Pinned: nickname shown when it differs from the species; not when it
matches (any case) or is missing; both party lines use it.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ck("a nickname is shown", E._mon_nick({"species": "LAPRAS", "nickname": "GLITCHES"}) == ' "GLITCHES"')
ck("...not when it is the species", E._mon_nick({"species": "LAPRAS", "nickname": "Lapras"}) == "")
ck("...nor when there is none", E._mon_nick({"species": "LAPRAS"}) == "" and E._mon_nick(None) == "")
src = (ROOT / "planner" / "executor.py").read_text()
ck("both party lines carry it", src.count("{m.get('species')}{_mon_nick(m)}{_mon_types(m)}") == 2)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)

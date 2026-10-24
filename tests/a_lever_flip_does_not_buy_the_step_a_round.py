#!/usr/bin/env python3
"""A round whose only change is a lever thrown does not move the step's
round cap out.

Run 62, 2026-10-24: a round that fires a flag or changes the party moves the
cap out by one (the Pokemon Tower 7F rule), and the count compared was the
flag count, so every Mansion statue flip (EVENT_MANSION_SWITCH_ON on, then
off) read as the world changing: defeat_blaine flipped statues past its idle
end, to round 21 and on, lap after lap.

Pinned: the news test counts flags without those seen both set and cleared.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.find('trace.append("(this round changed the world')
blk = src[max(0, i - 1600):i]
ck("the news test reads the toggled flags",
   '_tgl = set(getattr(self, "_toggled_flags", None) or ())' in blk, blk[-600:])
ck("...and compares the flag count without them",
   "(sig1[4], _nf(cur)) != (sig0[4], _nf(start))" in blk)
ck("...and the old full-count comparison is gone",
   "and (sig1[4], sig1[5]) != (sig0[4], sig0[5])\n                    and _news_bonus" not in src)

# the counting itself
_tgl = {"EVENT_MANSION_SWITCH_ON"}
_nf = lambda o: len([f for f in ((o or {}).get("flags") or []) if f not in _tgl])
before = {"flags": ["A", "B"]}
flip = {"flags": ["A", "B", "EVENT_MANSION_SWITCH_ON"]}
gain = {"flags": ["A", "B", "EVENT_GOT_SECRET_KEY"]}
ck("a flip alone counts the same", _nf(before) == _nf(flip))
ck("a flag gained still counts", _nf(before) != _nf(gain))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A sweep the party guard stopped before its first step is not a dry sweep.

Run 71, 2026-11-03, Pokemon Tower 7F: after each of the Rocket fights the
explore sweep stopped at "your party is nearly out -- 3 of 5 still
standing, 33% of its HP left; a sweep does not walk a spent party into more
fights", swept 0 steps and showed 0 cells. Both counted as dry sweeps of
POKEMON_TOWER_7F|10,2, so after the heal the page still listed four spots
of never-seen ground on the floor (Mr. Fuji's corner) while explore said
"this area is fully worked" and walked the party two floors down, twice.

Pinned: both shim guard stops carry the words the executor reads; a trace
with those words moves neither the consecutive dry count nor the dry-walk
ledger; an ordinary 0-cell sweep still counts.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "planner/executor.py").read_text()
SHIM = (ROOT / "harness/shim.lua").read_text()

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

MARK = "a sweep does not walk"
ck("the spent-party stop says it", f"; {MARK} a spent party" in SHIM)
ck("the no-PP stop says it", f"{MARK} a party" in SHIM)

i = SRC.index("A SWEEP THE PARTY GUARD REFUSED LOOKED AT NOTHING")
blk = SRC[i:i + 4000]
ck("the executor reads that mark", f'_refused = "{MARK}" in' in blk, blk[:400])
ck("a refusal skips the dry-walk ledger",
   "if not _refused:\n                self._count_dry_walk(self._where(obs), tr)" in blk)
ck("...and leaves the consecutive count alone",
   blk.index("if _refused:\n                    pass")
   < blk.index("elif _new and int(_new.group(1)) == 0:"))


def tally(t, region, trace):
    """The gate's count, worked the way the source now works it."""
    t = dict(t)
    j = " ".join(trace)
    if MARK in j:
        return t
    m = re.search(r"(\d+) cell\(s\) newly on screen", j)
    if m and int(m.group(1)) == 0:
        t[region] = t.get(region, 0) + 1
    else:
        t.pop(region, None)
    return t


R = "POKEMON_TOWER_7F|10,2"
RUN71 = ["explore (sweeping unseen ground): sweep(until=person): ran but had "
         "NO visible effect (nothing changed) — swept 0 step(s), 0 cell(s) "
         "newly on screen; nothing new came into view — stopped: stopped: "
         "your party is nearly out -- 3 of 5 still standing, 33% of its HP "
         "left; a sweep does not walk a spent party into more fights"]
DRY = ["sweep(): ok (moved, swept 8 step(s), 0 cell(s) newly on screen; "
       "nothing new came into view)"]
t = tally(tally({}, R, RUN71), R, RUN71)
ck("run 71's two refusals leave 7F uncounted", t == {}, t)
ck("an ordinary dry sweep still counts", tally({}, R, DRY) == {R: 1})

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

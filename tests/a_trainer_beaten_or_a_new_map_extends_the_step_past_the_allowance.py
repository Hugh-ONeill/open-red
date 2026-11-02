#!/usr/bin/env python3
"""A trainer beaten or a map first stood on gets the step a round past the allowance.

Run 70, 2026-11-02, Pokemon Tower 7F, speak_to_mr_fuji: the step's twelve
free rounds were spent by round 24 (round_for_news bonus 12); rounds 45 to
49 beat the 7F Rockets standing between the party and MR. FUJI, the
world-change rule could pay nothing more, and the hard cap ended the step at
round 49 with Fuji a few cells on. User at the stop: beating a trainer and
reaching a new map count as progress.

Pinned by source: a separate _deed_bonus, in the loop's ceiling, paid for a
new EVENT_BEAT_ flag (not a toggled one) or a map not stood on before the
step, only when nothing else paid that round, bounded by rounds * 3.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

ck("the loop's ceiling counts the deed bonus",
   "rnd < (rounds * 3 + _fresh_bonus + _news_bonus\n                                        + _deed_bonus)" in src)
i = src.index("# A TRAINER BEATEN OR A MAP FIRST STOOD ON MOVES THE CAP PAST THE")
blk = src[i:i + 2600]
ck("a newly fired EVENT_BEAT_ flag counts, a toggled one does not",
   'startswith("EVENT_BEAT_")' in blk and "f not in _tgl" in blk
   and 'f not in set((start or {}).get("flags") or [])' in blk)
ck("a map not stood on before the step counts, once",
   "_map_end not in _maps_stood" in blk and "_maps_stood.add(_map_end)" in blk)
ck("only when no other bonus paid this round",
   "_fresh_bonus + _news_bonus == _bonus_at_start" in blk
   and "_bonus_at_start = _fresh_bonus + _news_bonus" in src)
ck("bounded by rounds * 3", "_deed_bonus < rounds * 3" in blk)
ck("logged and said on the page",
   '"round_for_deed"' in blk and "gets the step one more round" in blk)
ck("it sits before the target notes",
   i < src.index("# accumulate targets that failed or did nothing", i))
init = src.index("_deed_bonus = 0")
ck("maps stood on are read from the ledger before the step's first round",
   "_maps_stood = {str(r).split(\"|\")[0]" in src[init:init + 300])

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

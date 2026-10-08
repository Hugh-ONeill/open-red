#!/usr/bin/env python3
"""An explore re-sent after a script turned the last sweep back is not
refused as a repeat.

A sweep stopped by a script writes the spot it walked toward and the cell
it stood on as blockers, and later sweeps go round them. Neither moves the
world mark, so the repeat gate read the next explore as "same ops, same
world, same answer" and refused it five times in Viridian City; the east
side (Mart, Gym) never came on screen and the step died with its budget
untouched (run 40, 2026-10-08, user: "it stopped at the old man instead of
being able to explore the rest of viridian city"). The spent record now
keeps how many blockers stood here before the round that spent it, and an
explore is let through again when there are more now.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i_seen = src.find("_seen = self._spent_macros.get(_mac_key)")
i_rule = src.find('self.log("repeat_allowed_new_wall"')
i_refuse = src.find('self.log("escalate_repeat_refused"')
ck("the new-wall rule sits between the lookup and the refusal",
   0 < i_seen < i_rule < i_refuse)
ck("...counts the blockers written where the party stands",
   '_b.get("where") == _here_blk' in src)
ck("...and lets only an explore through",
   re.search(r'st\.get\("op"\) == "explore"\s+for st in macro\)\s+and _blk_now > int\(_seen\.get\("blk"',
             src) is not None)
ck("the spent record keeps the count from before its round",
   '_rec["blk"] = _blk_now' in src)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

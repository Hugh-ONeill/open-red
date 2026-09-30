#!/usr/bin/env python3
"""From the second wipe, what keeps killing the run is the first thing on
the page, not the last.

Run 27 lost to BROCK ten times, five of them inside ninety seconds, walking
back and pressing him again with nothing healed, nothing trained and no
level gained. The page said so every round: "THIS STEP HAS BLACKED OUT 5
TIME(S)", "WHAT BEAT YOU", "something about the plan has to change". It
said so at 87-96% of the prompt, while BROCK's own name sat at 4%
(measured with planner/blocks.py, 2026-09-21). This project's own earlier
measurement is that the first-listed option is taken 54% of the time
against a chance rate near 8%, and that the median position of whatever the
run acts on is 14% of the way in. A fact at 96% is close to unsaid.

The words do not change. Where they sit does. The FIRST wipe stays where it
was, because one is bad luck and the page has better things to open with;
from the second it leads (user, 2026-09-21: "we cant forget about the
position findings").

Pinned: one wipe appends, two or more prepend; the text is the same either
way and nothing is duplicated; what follows the block is untouched; the
count, the foes, the lost fight and the experience line all travel with it;
no wipes, no block. Synthetic."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


# the assembly, as the source has it
_blk = SRC[SRC.index('_wipes_block = ""'):]
_blk = _blk[:_blk.index("self._note_switches(start)")]

ck("the block is built apart from the page",
   '_wipes_block = ""' in SRC and "_wipes_block += (" in _blk)
ck("...and nothing of it is appended to the page while it is built",
   "memory +=" not in _blk, _blk[:200])
ck("the count and what beat you are in it",
   "THIS STEP HAS BLACKED OUT {_bo_eff} TIME(S)" in _blk
   and "WHAT BEAT YOU, in the order it came out" in _blk)
ck("...and so are the lost fight and the experience since the step began",
   "THE LAST FIGHT YOU LOST" in _blk and "_wipes_block += _since" in _blk)
ck("...and the wild-ground note that only a repeat earns",
   "_bo_eff > 1" in _blk and "_wild.rstrip()" in _blk)
ck("one wipe leaves the page as it was; two or more lead with it",
   'memory = ((_wipes_block.lstrip("\\n") + "\\n" + memory)\n'
   "                          if _bo_eff > 1 else memory + _wipes_block)"
   in SRC)
ck("the move happens before the page is logged or sent",
   SRC.index("if _wipes_block:")
   < SRC.index('self.log("escalate_context", subgoal=sg["id"],\n'
               '                     target=self._target_key(sg)'))


# ---- the placement itself, worked the way the source works it ----------
def page(block, rest, wipes):
    if not block:
        return rest
    return (block.lstrip("\n") + "\n" + rest) if wipes > 1 else rest + block


BLOCK = "\nTHIS STEP HAS BLACKED OUT 2 TIME(S). WHAT BEAT YOU: ONIX.\n"
REST = "WHERE YOU STAND: PEWTER_GYM|1,1\nWAYS OUT OF HERE: the door.\n"

one = page(BLOCK, REST, 1)
two = page(BLOCK, REST, 2)
ck("with one wipe the page still opens where it always did",
   one.startswith("WHERE YOU STAND"), one[:40])
ck("...and the block is still on it", "BLACKED OUT" in one)
ck("with two the block is the first thing read",
   two.startswith("THIS STEP HAS BLACKED OUT"), two[:40])
ck("...and everything else keeps its order behind it",
   two.index("WHERE YOU STAND") < two.index("WAYS OUT OF HERE"))
ck("the words are the same either way, and said once",
   sorted(one.split()) == sorted(two.split())
   and two.count("BLACKED OUT") == 1)
ck("no wipe, no block at all",
   page("", REST, 0) == REST and "BLACKED" not in page("", REST, 0))

# where it lands, as blocks.py would measure it
_hi, _lo = (two.index("THIS STEP HAS") / len(two),
            one.index("THIS STEP HAS") / len(one))
ck("the block moves from the bottom of the page to the very top",
   _hi == 0.0 and _lo > 0.5, (_hi, _lo))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:220]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""The lever line after a press says it was pressed, not "Press one and look".

Run 57, 2026-10-21, Mansion 2F go_to_mansion_b1f rounds 9-16: the same macro
pressed SWITCH_2F_2_11 every round and the line printed after it still said
"A LEVER IS WITHIN REACH HERE ... Press one and look" (TODO line 2935, open at
run 70's stop, 2026-11-02). Pinned by source: when this round's ops pressed
a toggle, the line names it and the setting now.
"""
import sys
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
i = src.index('...AND NOT "PRESS ONE" RIGHT AFTER ONE WAS PRESSED.')
blk = src[i:i + 2600]
checks = [
    ("the round's own presses of a toggle are read",
     'st.get("op") == "interact"' in blk and '_tog.get(str(st.get("name")))' in blk),
    ("a pressed lever is named with the setting now",
     "this round, and the setting every" in blk),
    ("...and the old advice is kept for a round that pressed none",
     blk.index("this round, and the setting every") < blk.index("one and look.")),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)

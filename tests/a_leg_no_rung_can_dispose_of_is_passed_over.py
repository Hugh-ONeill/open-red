#!/usr/bin/env python3
"""A story leg every rung has failed to move, change or strike out is
passed over, and the run plays on; it is never counted as done.

Run 36 stopped on its own outline's "Retrieve the Secret Key from the Game
Corner" (the key is in the Cinnabar Mansion) after 10.6 hours and 740
rounds (user, 2026-10-04: "if it cant be done the chain cant just stop as
a result, its gotta be skipped").
"""
import os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
checks = []
def ck(n, ok): checks.append((n, bool(ok)))
sh = (ROOT / "fresh_discovery.sh").read_text()
i = sh.index('if wording_rung "" last-word; then continue; fi')
blk = sh[i:i + 2200]
ck("after the last word the leg is written down as passed over",
   'echo "$leg" >> run/outline_passed' in blk)
ck("...the chain moves on past it and sweeps ahead",
   'echo "$i" > "$PROGRESS"' in blk and 'sweep_ahead "$i"' in blk
   and "continue" in blk and "exit 1" not in blk)
ck("a fresh chain starts with no passed legs",
   "run/outline_passed" in sh[sh.index("rm -f run/outline_skips"):sh.index("rm -f run/outline_skips") + 600])
d = tempfile.mkdtemp(); (Path(d) / "run").mkdir()
KEY = "Retrieve the Secret Key from the Game Corner"
(Path(d) / "run/outline_passed").write_text(KEY + "\n")
os.chdir(d)
m = A._leg_marks(KEY)
ck("every page that lists the outline marks it passed over and not done",
   "PASSED OVER, NOT DONE" in m and "still open" in m)
ck("...and no other leg", A._leg_marks("Reach Saffron City") == "")
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)

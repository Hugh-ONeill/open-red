#!/usr/bin/env python3
"""A flag the run has seen flip back is not "an event fired since" on a way
that turned it back.

Run 67, 2026-10-28: the Cinnabar gym door's row read "SINCE IT TURNED YOU
BACK: 1 event(s) have fired (including: EVENT_MANSION_SWITCH_ON), so it may
answer differently now" after each Mansion statue press, and the run went
back to the locked door again and again. The flag is the switch's own
setting, already in _toggled_flags.

Pinned: a toggled flag alone says nothing; a real event still does.
Synthetic.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ex = E.Executor.__new__(E.Executor)
ex._toggled_flags = ["EVENT_MANSION_SWITCH_ON"]
ex._mark_now = [6, "a", "b"]
b = {"mark": [6, "x", "b"], "flags_then": ["EVENT_GOT_HM03"]}
ex._flags_now = ["EVENT_GOT_HM03", "EVENT_MANSION_SWITCH_ON"]
ck("a lever flipped alone is not news", ex._since_words(b) == "", ex._since_words(b))
ex._flags_now = ["EVENT_GOT_HM03", "EVENT_MANSION_SWITCH_ON", "EVENT_GOT_SECRET_KEY"]
w = ex._since_words(b)
ck("...a real event still is", "EVENT_GOT_SECRET_KEY" in w and "SWITCH" not in w, w)
src = (ROOT / "planner" / "author.py").read_text()
ck("the author's blocker rows drop toggled flags too",
   '- _toggled) \\\\' in src or "- _toggled)" in src)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)

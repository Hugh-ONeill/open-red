#!/usr/bin/env python3
"""A TM on a shelf is shown by its number unless the run has owned it.

Ruling (user, 2026-10-01): "has to be tm01 unless its already used tm01 in
which case it can be shown to be megapunch since thats knowledge"; an owned
TM keeps its move name (holding one is, by the run's rules, booting it).
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


x = object.__new__(E.Executor)
x._item_from = {}
x._machines_owned = set()
mp = next(k for k, v in E.MACHINE_NUMBERS.items() if v == "TM01")
ck("a TM never owned is its number alone on a shelf", x._disp_shelf(mp) == "TM01", x._disp_shelf(mp))
ck("...and a buy by that number still finds it", E.canon_item("TM01") == mp)
x._machines_owned = {mp}
ck("a TM the run has owned shows its move", mp in x._disp_shelf(mp), x._disp_shelf(mp))
ck("other items are untouched", x._disp_shelf("GREAT_BALL") == "GREAT_BALL")
x._machines_owned = set()
t = x._shelf_words('"Hi there!" THIS COUNTER SELLS: ' + mp + ", POTION. more text")
ck("the counter's SELLS line is rewritten the same way",
   "SELLS: TM01, POTION." in t and mp not in t, t)
src = (ROOT / "planner/executor.py").read_text()
ck("the shops line, the feedback and the outcome record all use it",
   "self._disp_shelf(x) for x in _it[:10]" in src
   and "{self._shelf_words(t)}" in src
   and "speech_excerpt(self._shelf_words(last.strip()), 200)" in src)
ck("what the run has held is kept across attempts", '"machines_owned":' in src
   and 'data.get("machines_owned")' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

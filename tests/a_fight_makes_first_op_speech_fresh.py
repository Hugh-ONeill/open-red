#!/usr/bin/env python3
"""A fight in the first op makes that op's speech its own.

Run 51, Cerulean (2026-10-11): the rival fight came in the first op of an
attempt. The first-op guard (_said_ready) keeps a resumed save's leftover
line off the first op, and it also dropped the rival's second box — "I went
to BILL's ... go thank him!" — while his first box went in by the main
path. The fourth run in a row without the Bill line. Probed on run 51's
own Cerulean save as a fresh executor's first op: before, no BILL in the
hints; after, kept.

Pinned: a fight recorded in this op makes its words fresh for the round's
quote, the extra boxes and the earlier speeches; with no fight, the guard
stands. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("fresh when ready, or when a fight was recorded this op",
   '_fresh = bool(self._said_ready\n                          or getattr(self, "_last_fight", None) is not _fight0)' in SRC)
ck("the round's quote reads it", 'heard = said if _fresh else ""' in SRC)
ck("the extra boxes read it", "for _xn, _xs in (_extra if _fresh else []):" in SRC)
ck("the earlier speeches read it", "said, _fresh)" in SRC)

ex = E.Executor.__new__(E.Executor)
ex.hints, ex._said_ready = {}, False
ex.log = lambda *a, **k: None
MAP = {"id": "CERULEAN_CITY", "region": "20,0"}
OBS = {"text_seq": 9, "map": MAP,
       "ended_runs": [{"seq": 9, "text": "CHAD: Hey, guess what? I went to BILL's and got him to show me his rare POKeMON!"}]}
ck("not fresh: nothing", ex._earlier_speech({"text_seq": 1, "map": MAP}, OBS, None, {}, "x", False) == [])
ck("fresh by a fight: kept", ex._earlier_speech({"text_seq": 1, "map": MAP}, OBS, None, {}, "x", True) != [])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

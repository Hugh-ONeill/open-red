#!/usr/bin/env python3
"""Speech an early-handled op heard is caught up and said.

Run 52, Cerulean (2026-10-11): the rival met the run on cross(dir=north)
to Nugget Bridge. cross and walk_to run early handlers that leave the op
loop before the speech path, so his "I went to BILL's ... go thank him!"
sat in the shim's ended runs, filed nowhere and said nowhere — the fifth
run without the line. Replayed on run 52's own save with the run's policy
as an attempt's first op: before, no BILL in the round or the hints; after,
"(on the way, BIFF said: ...)" and BILL filed.

Pinned: every op's start and the macro's end catch up finished speeches
past the mark; the general path moves the mark so nothing is said twice; a
run printed before the mark is not. Synthetic.
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


rt = SRC[SRC.index("    def _run_traced("):]
rt = rt[:rt.index("\n    def ", 10)]
ck("caught up at every op's start", "self._stop_if_asked()\n            self._catch_up_speech(sg, trace)" in rt)
ck("...and at the macro's end", "self._catch_up_speech(sg, trace)\n        return pred_holds(done" in rt)
ck("the general path moves the mark", 'self._speech_mark = (obs or {}).get("text_seq")' in rt)

MAP = {"id": "ROUTE_24", "region": "4,4"}


class B:
    def __init__(self, o): self.o = o
    def obs(self): return self.o


ex = E.Executor.__new__(E.Executor)
ex.hints, ex._said_ready = {}, True
ex.log = lambda *a, **k: None
ex.b = B({"text_seq": 900, "map": MAP, "ended_runs": []})
trace = []
ex._catch_up_speech({}, trace)                 # sets the mark
ex.b = B({"text_seq": 1033, "map": MAP, "ended_runs": [
    {"seq": 880, "text": "OLD: said long before the mark, not again"},
    {"seq": 987, "text": "BIFF: Yo! TRENT! / BIFF: Hey, guess what? I went to BILL's and got him to show me his rare POKeMON!"}]})
ex._catch_up_speech({}, trace)
ck("the rival's speech is said on the way", any("BIFF said" in t and "BILL" in t for t in trace), trace)
ck("...and filed", any("BILL" in l for v in ex.hints.values() for l in v))
ck("a run from before the mark is not", not any("long before" in t for t in trace))
n = len(trace)
ex._catch_up_speech({}, trace)
ck("nothing is said twice", len(trace) == n)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

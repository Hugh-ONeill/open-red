#!/usr/bin/env python3
"""A push retry is not sent to a refusal that will only say itself again.

Seafoam B3F, run 68, 2026-10-30. Three pushes to (6,16) each came back
"no sequence of shoves puts it on (6,16)" with no battle, and each was
re-sent to the same refusal by the resume rule. A retry that did drop a
boulder down a hole still read "still not on", because a boulder on a
hole is never standing there. Now the resume loop skips a no-battle
refusal of the kind a re-solve cannot change, counts a drop down a listed
hole as landed, and logs whether a battle came first and why it retried.
A round that reached the goal logs its trace too.
"""
from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXEC = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(name, cond): checks.append((name, bool(cond)))

i = EXEC.index("_final = any(w in _pdet for w in (")
blk = EXEC[i - 900:i + 2400]
for w in ("no sequence of shoves", "nothing is standing",
          "is not switched on", "cannot be shoved ANY way"):
    ck(f"'{w}' is a final refusal", f'"{w}"' in blk)
ck("a final refusal with no battle is not retried",
   "while _tries < 4 and not (_final and not _fought and not _tries):" in blk)
ck("a drop down a hole is landed",
   "push_went_down_hole(pre_obs, _o, _tx, _ty)" in blk
   and "if _landed(obs):" in blk and "_arrived = _landed(obs)" in blk)
ck("the retry log says whether it fought and why",
   "fought=_fought, why=_pdet[:160]" in blk)
ck("a resumed drop says the boulder left the floor",
   blk.count("the boulder went down the hole at ") == 1)
ck("a successful round logs its trace",
   'self.log("escalate_round_ok", subgoal=sg["id"], round=rnd,\n'
   '                         trace=trace)' in EXEC)
ck("the unverified commits log it too",
   EXEC.count('round=rnd,\n                         trace=trace, proposed') == 2)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
raise SystemExit(1 if bad else 0)

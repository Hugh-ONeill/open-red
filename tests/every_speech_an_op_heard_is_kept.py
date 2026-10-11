#!/usr/bin/env python3
"""Every speech an op heard is kept, not only its last one.

Run 49, Cerulean (2026-10-11): the rival met the run on its way to press a
sign, and the sign's line ("Grass and caves handled easily! BIKE SHOP")
then stood for the whole op. The rival's "I went to BILL's ... go thank
him!", the one pointer to the S.S. Ticket, reached neither the round nor
the hints — the third run in a row to lose it, each time to whatever was
said after it. Probed on run 49's leg-10 save: the shim's ended_runs holds
the rival's whole speech (BILL included) at print count 313, after an op
that began at 0.

Pinned: a speech ended during the op (by print count) and not the op's
last words is filed under its own speaker and returned for the round's
note; one printed before the op, the last words themselves, and short
noise are not. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


RIVAL = ("BUSTER: Yo! SLY! You're still struggling along back here? / BUSTER: Hey, guess "
         "what? I went to BILL's and got him to show me his rare POKeMON! Since you're "
         "using his system, go thank him!")
SIGN = "Grass and caves handled easily! BIKE SHOP"
MAP = {"id": "CERULEAN_CITY", "region": "20,0"}
PRE = {"text_seq": 290, "map": MAP}
OBS = {"text_seq": 320, "last_text": SIGN, "map": MAP,
       "ended_runs": [{"seq": 200, "text": "OLD: something said long before this op began"},
                      {"seq": 313, "text": RIVAL},
                      {"seq": 320, "text": SIGN},
                      {"seq": 318, "text": "OK"}]}

ex = E.Executor.__new__(E.Executor)
ex.hints = {}
ex._said_ready = True
ex.logged = []
ex.log = lambda kind, **kw: ex.logged.append((kind, kw))
got = ex._earlier_speech(PRE, OBS, None, {"id": "x"}, SIGN)
ck("the rival's speech is returned, under his name",
   len(got) == 1 and got[0][0] == "BUSTER" and "BILL" in got[0][1], got)
filed = [l for v in ex.hints.values() for l in v]
ck("...and filed in the hints under him", any(l.startswith("BUSTER: ") and "BILL" in l
                                             for l in filed), filed)
ck("a speech from before the op is not", not any("long before" in l for l in filed))
ck("the op's own last words are not doubled", not any(SIGN in l for l in filed))
ck("short noise is not", not any(l.endswith(": OK") for l in filed))
ex._said_ready = False
ck("nothing before the first op is trusted", ex._earlier_speech(PRE, OBS, None, {}, SIGN) == [])
src = (ROOT / "planner/executor.py").read_text()
ck("the round's note says it", "note += (f' — earlier in this op, {_en} said: \"'" in src)
shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim keeps each ended speech with its print count",
   "_er[#_er + 1] = { seq = text_seq, text = text_run }" in shim
   and "o.ended_runs = _er" in shim)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

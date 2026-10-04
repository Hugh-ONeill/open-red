#!/usr/bin/env python3
"""A reword whose reason says the run DISCOVERED something must show it: a
line the run heard, quoted, or an event that fired. Memory may be a reason;
it may not rewrite the objective as a finding.

Run 36, 2026-10-03: "Retrieve the Secret Key from the Game Corner" became
"...from the Game Corner Prize Room" because "The run has discovered that the
Secret Key is obtained by exchanging coins at the Prize Room counter". The
vendors had said only "A COIN CASE is required!"; every plan after it chased
coins and a Coin Case (user: "its got the totally wrong idea")."""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
with tempfile.TemporaryDirectory() as td:
    ob = Path(td) / "explored.json"
    ob.write_text(json.dumps({"hints": {"GAME_CORNER_PRIZE_ROOM|0,3": [
        "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_1: A COIN CASE is required!"],
        "GAME_CORNER|8,5": ["GAMECORNER_ROCKET: I'm guarding this poster!"]}}))
    run36 = ("The run has discovered that the Secret Key is obtained by exchanging "
             "coins at the Prize Room counter, which is a separate area")
    ck("run 36's reason is refused: a discovery nothing on record shows",
       A.unearned_discovery(run36, ob), A.unearned_discovery(run36, ob))
    ok_q = 'The run has learned that a guard stands by it: "I\'m guarding this poster!"'
    ck("a discovery quoting what was heard stands", A.unearned_discovery(ok_q, ob) == "")
    bad_q = 'The run has discovered it: "the key is a prize for 9999 coins"'
    ck("a quote nobody said does not count", A.unearned_discovery(bad_q, ob))
    run36b = ("The run has already entered the Prize Room and attempted to trade "
              "for the key, confirming it is located there rather than in the "
              "general Game Corner area.")
    ck("...and the second one, 'confirming it is located there', too",
       A.unearned_discovery(run36b, ob), A.unearned_discovery(run36b, ob))
    belief = "I believe the Secret Key is a prize at the Prize Room counter."
    ck("a belief said as a belief is not refused here", A.unearned_discovery(belief, ob) == "")
src = (ROOT / "planner/author.py").read_text()
ck("check_wording refuses before accepting the reword",
   src.index("_ue = unearned_discovery(why, observed)") < src.index('print(f"[wording] {goal!r} -> {new!r}: {why}"'))
ck("the rung's prompt asks for the quote", "quote what it heard" in A.WORDING_SYS)
failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if failed else 0)

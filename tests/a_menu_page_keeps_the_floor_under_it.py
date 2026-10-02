#!/usr/bin/env python3
"""A box or menu page carries one line of the floor under it, from the last
page that could read it.

Run 20 (2026-10-01), Celadon Mart 5F, hunting Fresh Water: the floor page
listed "stairs up (12,1) -> UNKNOWN — never taken" the round before and the
round after; on the clerk's BUY/SELL menu between them, whose page says only
that the floor cannot be read, the model wrote "the Department Store has been
exhausted" and then took the stairs down. The roof sells the Fresh Water.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import ledger as L  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


class Ex:
    pass


ex = Ex()
C = L.Candidate
cands = [C(key="explore", kind="op", status="op"),
         C(key="12,1", kind="door", status="untried", look="stairs"),
         C(key="16,1", kind="door", status="taken", look="stairs"),
         C(key="CELADONMART5F_GENTLEMAN", kind="person", status="unspoken"),
         C(key="CELADONMART5F_CLERK1", kind="person", status="touched")]
L._note_floor(ex, "CELADON_MART_5F|1,1", cands)
t = L._floor_under_text(ex)
ck("the line names the floor and its never-taken way", "CELADON_MART_5F|1,1" in t
   and "1 way(s) never taken (stairs (12,1))" in t, t)
ck("...and its never-pressed thing", "1 thing(s) never pressed (CELADONMART5F_GENTLEMAN)" in t, t)
ck("...and not what was taken or pressed", "16,1" not in t and "CLERK1" not in t, t)
L._note_floor(ex, "CELADON_MART_4F|1,1", [C(key="16,1", kind="door", status="taken")])
ck("a finished floor says so", "nothing there untried" in L._floor_under_text(ex))
ck("no floor read yet, no line", L._floor_under_text(Ex()) == "")

src = (ROOT / "planner/ledger.py").read_text()
i = src.index("def render(")
blk = src[i:src.index('head = f"WHERE YOU STAND: {here}"', i)]
ck("both box pages carry it", blk.count("_under") >= 3 and "+ _under)" in blk
   and "+ _under + _ahead)" in blk)
ck("the overworld page records it", "_note_floor(ex, here, cands)" in blk)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

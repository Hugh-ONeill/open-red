#!/usr/bin/env python3
"""An op's result is its own, not the field medicine used after its fight.

Run 47, Route 12 (2026-10-11): use_item(POKE_FLUTE) woke ROUTE12_SNORLAX,
the fight that followed threw five balls and won, the harness then used a
SUPER_POTION, and the round read only "use_item(item=POKE_FLUTE): ok (used
SUPER_POTION on HYPNO: HP 71 -> 120)". The wake, the fight and the open
road were never said; the medicine's answer had become the op's.

Pinned on run 47's words: a result that is the last medicine's is said as
the fight and then the medicine; any other result is untouched; the op
loop reads the result through it, and every field item is recorded.
Synthetic.
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


MED = "used SUPER_POTION on HYPNO: HP 71 -> 120"
ex = E.Executor.__new__(E.Executor)
ex._op_meds = [MED]
ex._op_foes = ["SNORLAX L30"]
r = ex._med_result({"ok": True, "detail": MED})
ck("the fight is said first", r["detail"].startswith("a fight with SNORLAX L30 came of it"), r)
ck("...then the medicine", r["detail"].endswith("after it, " + MED), r)
own = {"ok": True, "detail": "used POKE_FLUTE"}
ck("an op's own result is untouched", ex._med_result(own) is own)
ex._op_meds = []
ck("with no medicine used nothing changes",
   ex._med_result({"ok": True, "detail": MED})["detail"] == MED)
src = (ROOT / "planner/executor.py").read_text()
ck("the op loop reads the result through it",
   'r = self._med_result((obs or {}).get("result") or {})' in src)
ck("cure, revive and heal are each recorded", src.count("self._note_med(") == 3)
ck("each op starts with none", "self._op_meds = []" in src and "self._op_foes = []" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

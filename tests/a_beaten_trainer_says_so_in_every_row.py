#!/usr/bin/env python3
"""A trainer the save says is beaten says so in his row whatever its status.

Run 65, 2026-10-24: Mt Moon B2F's ROCKET3 was beaten, and his rows read
"pressed 1x" from his part and "you cannot walk to it ... DOES reach it" from
the other part, under "Every entry above may be taken"; a step waiting on an
unnamed TRAINER_3 flag took him for it and shuttled between the two parts.

Pinned: a beaten trainer not reachable from here, and one pressed, carry
"you have beaten them"; an unbeaten one does not.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import candidates as C  # noqa: E402
import ledger as L  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R = "MT_MOON_B2F|23,21"


def row(beaten, reachable, pressed):
    ex = C.make()
    ex._where = lambda o: R
    ex._tried_objs = {R: {"MTMOONB2F_ROCKET3"}} if pressed else {}
    o = C.obs(ex, [], objects=[{"name": "MTMOONB2F_ROCKET3", "kind": "trainer", "x": 29, "y": 11,
                                "reachable": reachable, "beaten": beaten}], region="23,21")
    o["map"]["id"] = "MT_MOON_B2F"
    cands = L.build(ex, o, "")
    return next((c for c in cands if c.key == "MTMOONB2F_ROCKET3"), None)


r1 = row(True, False, False)
ck("a beaten trainer out of reach says beaten", r1 and "you have beaten them" in (r1.note or ""), r1 and (r1.status, r1.note))
r2 = row(True, True, True)
ck("a beaten trainer pressed says beaten", r2 and "you have beaten them" in (r2.note or ""), r2 and (r2.status, r2.note))
r3 = row(False, True, True)
ck("an unbeaten one does not", r3 and "you have beaten them" not in (r3.note or ""), r3 and (r3.status, r3.note))

ex = C.make(); ex._where = lambda o: R; ex._tried_objs = {}
o = C.obs(ex, [], objects=[{"name": "MTMOONB2F_ROCKET3", "kind": "trainer", "x": 29, "y": 11,
                            "reachable": False, "beaten": True}], region="23,21")
o["map"]["id"] = "MT_MOON_B2F"
ck("a beaten trainer is not on the stuck list",
   "MTMOONB2F_ROCKET3" not in [c.key for c in L._stuck_things(L.build(ex, o, ""))])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

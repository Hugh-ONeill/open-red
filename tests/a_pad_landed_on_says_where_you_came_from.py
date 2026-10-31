#!/usr/bin/env python3
"""A pad you landed on says where you came from, and nothing about where
riding it goes.

Run 69, 2026-10-31, Saffron Gym after Sabrina. The exit room (7,13) is
entered only by the pad at (19,17) in room 14,13; the run had landed on
(19,17) coming out of that room, and the record says so (the 7,13 room's
pad (11,15): to 14,13, land 19,17). Room 14,13's page still read "warp pad
(19,17) -> UNKNOWN — never taken from here", and the model rode pads round
the whole gym for the way out for two steps.

Pinned: the row says it was landed on coming from that room; it stays
untried with no destination (a pad's ride back can land elsewhere, see
a_pad_arrived_on_is_not_a_pad_ridden); a pad nobody landed on says nothing.
Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import ledger as L  # noqa: E402
import candidates as C  # noqa: E402
import untried as U  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


MID = U.MAP
ex = C.make()
here = f"{MID}|0,0"
ex.explored = {f"{MID}|7,13": {"11,15": {"to": here, "land": "19,17", "n": 1}}}
o = C.obs(ex, ["19,17", "15,15"])
for w in o["map"]["warps"]:
    w["dest"] = MID
    w["look"] = "pad"
rows = {c.key: c for c in L.build(ex, o, want_explore=False)}
r = rows.get("19,17")
ck("the pad landed on says where you came from",
   r is not None and f"you landed on this pad coming from {MID}|7,13" in (r.note or ""),
   r and r.note)
ck("...stays untried", r is not None and r.status == "untried", r and r.status)
ck("...with no destination claimed", r is not None and not r.dest, r and r.dest)
r2 = rows.get("15,15")
ck("a pad nobody landed on says nothing of it",
   r2 is not None and "landed on this pad" not in (r2.note or ""), r2 and r2.note)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

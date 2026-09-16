#!/usr/bin/env python3
"""Lt. Surge's gym page says whether each electric lock is open.

Run 27 pressed TRASH_CAN_2 eleven times as "the most reliable way to open
the first lock", nine of them "Nope, there's only trash here", each followed
by more cans pressed against a lock still shut (user, 2026-09-16: "build the
lock state line"). The barriers are drawn across the room, up or down; the
page now says which. Pinned: the line reads the engine's two lock flags, the
2nd open implies the 1st, it appears only in that gym, and it says nothing
about which can holds a switch.

Synthetic: the render is fed a stub executor; no game, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import ledger as L            # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


class Stub:
    """Every method answers empty; every attribute is an empty dict."""
    def __getattr__(self, name):
        if name.startswith("_") and name not in ("_where", "_outcomes",
                                                 "_cur_target"):
            pass
        return _Empty()

    def _where(self, obs):
        m = (obs or {}).get("map") or {}
        return f"{m.get('id')}|{m.get('region')}"


class _Empty(dict):
    def __call__(self, *a, **k):
        return ""


def page(flags, mid="VERMILION_GYM"):
    obs = {"mode": "overworld", "flags": list(flags),
           "map": {"id": mid, "region": "4,5", "objects": [], "warps": []},
           "player": {"x": 4, "y": 5}}
    try:
        return L.render([], Stub(), obs)
    except Exception as e:           # the stub is thin; fall back to source
        return f"RENDER FAILED: {e}"


src = (ROOT / "planner/ledger.py").read_text()
blk = src[src.index("THE ELECTRIC LOCKS AS THEY STAND"):]
blk = blk[:blk.index('lines.append("Every entry above may be taken')]
ck("the line reads the engine's two lock flags",
   '"EVENT_1ST_LOCK_OPENED" in _fl' in blk and '"EVENT_2ND_LOCK_OPENED" in _fl' in blk)
ck("the 2nd open counts the 1st open too", '("OPEN" if _one or _two else "closed")' in blk)
ck("only in Lt. Surge's gym", '== "VERMILION_GYM"' in blk)
ck("nothing about which can holds a switch",
   "TRASH_CAN_" not in blk.split("lines.append(")[1])

p0 = page([])
if not p0.startswith("RENDER FAILED"):
    ck("both closed", "THE ELECTRIC LOCKS RIGHT NOW: the 1st is closed, the 2nd is closed." in p0)
    ck("the 1st open", "the 1st is OPEN, the 2nd is closed." in page(["EVENT_1ST_LOCK_OPENED"]))
    ck("both open", "the 1st is OPEN, the 2nd is OPEN." in page(["EVENT_2ND_LOCK_OPENED"]))
    ck("not in another room", "ELECTRIC LOCKS" not in page([], mid="VERMILION_CITY"))

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

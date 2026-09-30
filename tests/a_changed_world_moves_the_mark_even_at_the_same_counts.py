#!/usr/bin/env python3
"""A changed world moves the mark even when the counts come out the same.

Mansion 1F's east door was stamped blocked at [6, 314, 20]; after the SECRET_KEY
pickup and several lever flips the counts were [6, 314, 20] again, and `go`
kept refusing the walked exit (run 19, 2026-09-30).

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


W = E.Executor._world_mark
a = {"badges": ["B"] * 6, "flags": ["EVENT_MANSION_SWITCH_ON", "EVENT_X"], "bag": {"POTION": 1, "ESCAPE_ROPE": 2}}
b = {"badges": ["B"] * 6, "flags": ["EVENT_Y", "EVENT_X"], "bag": {"SECRET_KEY": 1, "ESCAPE_ROPE": 2}}
ck("same counts, different flags and bag: a different mark", W(a) != W(b), (W(a), W(b)))
ck("the same world is the same mark", W(a) == W(dict(a)))
ck("the order the game lists them in does not matter",
   W(a) == W(dict(a, flags=list(reversed(a["flags"])))))
ck("a count in the bag is not a change of kind", W(a) == W(dict(a, bag={"POTION": 5, "ESCAPE_ROPE": 1})))
ck("the badge count stays a number (_since_words compares it)", W(a)[0] == 6)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

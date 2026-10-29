#!/usr/bin/env python3
"""{"has_item": {"SAFARI_BALL": n}} is read off the Safari game's own count.

The gate hands over thirty Safari Balls, and the game keeps them apart from
the bag (the shim's obs["safari"]["balls"]); run 68's get_safari_pass,
{"has_item":{"SAFARI_BALL":1}}, read false with thirty in hand and was
carried past (2026-10-29).
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


bag = {"GREAT_BALL": 25}
ck("thirty in the Safari count meets SAFARI_BALL 1",
   E.pred_holds({"has_item": {"SAFARI_BALL": 1}}, {"bag": bag, "safari": {"balls": 30, "steps": 500}}))
ck("...and 30, not 31",
   E.pred_holds({"has_item": {"SAFARI_BALL": 30}}, {"bag": bag, "safari": {"balls": 30}})
   and not E.pred_holds({"has_item": {"SAFARI_BALL": 31}}, {"bag": bag, "safari": {"balls": 30}}))
ck("no Safari game reads as none",
   not E.pred_holds({"has_item": {"SAFARI_BALL": 1}}, {"bag": bag}))
ck("the string shape reads the same way",
   E.pred_holds({"has_item": "SAFARI_BALL"}, {"bag": bag, "safari": {"balls": 3}}))
ck("other balls are still read off the bag",
   not E.pred_holds({"has_item": {"GREAT_BALL": 26}}, {"bag": bag, "safari": {"balls": 30}}))
ck("a junk safari field does not raise",
   not E.pred_holds({"has_item": {"SAFARI_BALL": 1}}, {"bag": bag, "safari": "x"}))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

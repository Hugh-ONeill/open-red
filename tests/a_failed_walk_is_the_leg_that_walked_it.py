#!/usr/bin/env python3
"""A failed walk is held against the leg whose plan walked it, not the
next leg the ladder asks about.

Run 36, 2026-10-05: "Clear Victory Road" could not be drafted, so it ran
no plan, and the journal's last plan_start was "Obtain HM04 STRENGTH"'s.
The missing rung then turned down "Obtain HM04 STRENGTH from the Warden in
the Safari Zone" for Victory Road with "it names SAFARI_ZONE, and this
leg's plan has just failed walking there": the HM04 leg's walk.

Pinned: with the leg named, a last plan of another objective says
nothing; the leg's own plan, or one of the same named item, still counts;
without the leg named the old behaviour stands; both rungs pass the leg.
Synthetic."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


HM = "Obtain HM04 STRENGTH from the Warden in the Safari Zone"
VR = "Clear Victory Road"
rows = [{"kind": "plan_start", "goal": HM},
        {"kind": "escalate_context", "subgoal": "s", "target": "map:SAFARI_ZONE_CENTER"},
        {"kind": "escalate_end", "subgoal": "s", "success": False}]
with tempfile.TemporaryDirectory() as d:
    j = Path(d) / "executor_log.jsonl"
    j.write_text("".join(json.dumps(r) + "\n" for r in rows))
    f = A._reword_points_at_what_failed
    ck("another leg's last plan says nothing about this one", f(HM, j, VR) is None)
    ck("the leg's own plan still counts", f(HM, j, HM) == "SAFARI_ZONE", f(HM, j, HM))
    ck("so does a plan for the same named item",
       f("Retrieve HM04 in the Safari Zone", j, "Get HM04 from the Warden") == "SAFARI_ZONE")
    ck("unnamed, the old reading stands", f(HM, j) == "SAFARI_ZONE")

src = (ROOT / "planner/author.py").read_text()
ck("the missing rung names the leg",
   "_reword_points_at_what_failed(ins, journal, goal)" in src)
ck("so does the wording rung",
   "_reword_points_at_what_failed(new, journal_path, goal)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

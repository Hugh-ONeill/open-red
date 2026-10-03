#!/usr/bin/env python3
"""Every plan carries its leg's objective as its goal, so the chain finds it.

Run 36, 2026-10-03: drafted from an idea ("PLAN THIS IDEA, and only this
one: Go to the Celadon Department Store..."), the rewrite's goal was written
as the idea; find_plan matches a leg to its plan by goal, so the rewrite was
never found and the chain re-ran the old roof plan (user: "it should see that
its explored the mansion ... with the rewrite right? did it?").

Pinned: the draws and the final write both set the goal to the objective
(notes stripped as find_plan strips them), and find_plan then picks the
newest version."""
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/author.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ck("each draft gets the objective as its goal",
   'p["goal"] = _re_goal.sub("", str(goal)).strip() or str(goal)' in src)
ck("the written plan gets the objective, never the model's restatement",
   'plan["goal"] = _re_goal.sub("", str(args.goal)).strip() or str(args.goal)' in src
   and 'plan.setdefault("goal", args.goal)' not in src)
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
leg = "Infiltrate the Team Rocket secret base in Celadon City (you added this when outlining, for: X)"
ck("the outline's note is stripped the way find_plan strips it",
   A._re_goal.sub("", leg).strip() == "Infiltrate the Team Rocket secret base in Celadon City")
with tempfile.TemporaryDirectory() as td:
    (Path(td) / "plans").mkdir()
    g = "Infiltrate the Team Rocket secret base in Celadon City"
    sg = [{"id": "a", "done_when": {"map": "GAME_CORNER"}}]
    (Path(td) / "plans/leg_26_x.json").write_text(json.dumps({"goal": g, "subgoals": sg}))
    (Path(td) / "plans/leg_26_x.v1.json").write_text(json.dumps({"goal": g, "subgoals": sg}))
    out = subprocess.run([sys.executable, str(ROOT / "planner/find_plan.py"), leg],
                         cwd=td, capture_output=True, text=True).stdout.strip()
    ck("with the goal kept, find_plan hands the leg its newest plan",
       out.endswith("leg_26_x.v1.json"), out)
failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if failed else 0)

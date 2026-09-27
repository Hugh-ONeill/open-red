#!/usr/bin/env python3
"""check-done is shown the next line of the model's own list as a separate
objective, so it does not fold that line into the one it is judging.

Run of record 12 (2026-09-27): "Navigate Mt. Moon and fight Team Rocket" had
its conditions met and was judged "not done: ... has not yet exited the
mountain on the far side" — the next line, "Exit Mt. Moon". Its second
verdict was refused as hedged and the leg was pushed behind Cerulean with
its successor.

Pinned: the judge's prompt names the next line after the objective; the
purpose note on either side does not stop the match; the last line has no
next; an objective not on the list gets nothing. Synthetic.
"""
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


plans = Path(tempfile.mkdtemp(prefix="nextline_"))
(plans / "outline.txt").write_text(
    "Reach Mt. Moon\nNavigate Mt. Moon and fight Team Rocket\nExit Mt. Moon\n")
t = A.next_objective_text("Navigate Mt. Moon and fight Team Rocket", plans)
ck("the next line is named as a separate objective",
   'a separate line: "Exit Mt. Moon"' in t and "not part of it" in t, t)
ck("...a purpose note does not stop the match",
   A.next_objective_text("Reach Mt. Moon (a doubt you recorded when outlining: "
                         "for: X)", plans).count("Navigate Mt. Moon") == 1)
ck("the last line has no next", A.next_objective_text("Exit Mt. Moon", plans) == "")
ck("an objective not on the list gets nothing",
   A.next_objective_text("Catch a DRATINI", plans) == "")

asked = []
A.brock_probe.chat = lambda msgs, model: (asked.append(msgs[-1]["content"]),
                                          json.dumps({"done": False, "why": "x"}))[1]
import os  # noqa: E402
os.chdir(plans.parent)
(plans.parent / "plans").mkdir(exist_ok=True)
(plans.parent / "plans" / "outline.txt").write_text((plans / "outline.txt").read_text())
import upkeep_ask  # noqa: E402
upkeep_ask.maybe_skip = lambda *a, **k: ""
A.check_done("Navigate Mt. Moon and fight Team Rocket",
             "standing in MT_MOON_1F with IVYSAUR L19 (GRASS/POISON)", "m")
ck("check-done's prompt carries it right after the objective",
   asked and asked[-1].startswith("THE OBJECTIVE: Navigate Mt. Moon and fight "
                                  "Team Rocket\n\nTHE NEXT OBJECTIVE ON YOUR LIST"),
   asked[-1][:200] if asked else "")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

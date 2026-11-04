#!/usr/bin/env python3
"""The first press of an executor says what it printed.

Run 72, 2026-11-04: an attempt's first press of Bill's Cell Separator
printed "TELEPORTER is displayed on the PC monitor." (Bill had not gone
into the machine yet) and the trace read "ok (moved)": the first-op guard,
written before the print counter existed, dropped the line. The step took
the press as done and the run walked off to look for the S.S. Ticket on the
S.S. Anne. Reproduced from the run's save: a fresh executor's first press
read "ran but had NO visible effect", its second the line.

Boots the game (a boot test, listed in tests/run_suite.sh BOOTS) from
tests/fixtures/bills_house_console.lua, standing under the console.
Pinned: the first press of a fresh executor quotes the line it printed.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "planner"))
import contract as C  # noqa: E402

RUN = Path(os.environ.get("RED_BRIDGE_DIR") or (ROOT / "run/contract"))
SAVE = ROOT / "tests/fixtures/bills_house_console.lua"

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

proc = C.start_game(RUN, SAVE, "200")
os.environ["RED_BRIDGE_DIR"] = str(RUN)
try:
    from bridge import Bridge                       # noqa: E402
    import executor as E                            # noqa: E402
    b = Bridge(RUN)
    E.bootstrap(b, cont=True)
    ck("the fixture stands in Bill's house",
       ((b.obs() or {}).get("map") or {}).get("id") == "BILLS_HOUSE")
    sg = {"id": "press", "goal_text": "press the separator",
          "done_when": {"flag": "EVENT_USED_CELL_SEPARATOR_ON_BILL"},
          "max_attempts": 1}
    ex = E.Executor(b, plan={"goal": "first press", "subgoals": [sg]},
                    plan_path=None, can_escalate=False, model="",
                    run_id="firstpress")
    ex.MEMORY = RUN / "explored.json"
    ex._load_memory()
    out = ex._run_traced(sg, [{"op": "interact",
                               "name": "CELL_SEPARATION_SYSTEM",
                               "answer": "yes"}], ignore_done=True)
    tr = " ".join(str(t) for t in (out[1] if isinstance(out, tuple) else out))
    ck("the first press quotes what it printed",
       "TELEPORTER is displayed on the PC monitor." in tr, tr[:300])
    ck("...and is not called a press with no effect",
       "NO visible effect" not in tr, tr[:300])
finally:
    proc.terminate()

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

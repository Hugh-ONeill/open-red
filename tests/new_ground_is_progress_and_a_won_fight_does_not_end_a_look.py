#!/usr/bin/env python3
"""Three pieces of friction from run 20's S.S. Ticket leg (2026-10-01).

The step "travel to Route 9" (east of Cerulean, behind a Cut tree) gave up
the round explore first carried the run onto Route 25, where Bill was: the
drift count had run 14 rounds without getting closer to Route 9 on paper.
Explore's refusal to walk away called the way north "going backwards". And
every Route 25 trainer stopped the sweep, so the far end came ten cells a
round. User: "yeah do all three".
"""
import inspect
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


src = inspect.getsource(E.Executor)
i = src.index("NEW GROUND IS PROGRESS, WHEREVER IT LIES ON PAPER")
blk = src[i:i + 1600]
ck("a map stood on for the first time resets the drift count",
   'elif _first:\n            st["since"] = 0' in blk and "<= 1" in blk)
ck("...once per map per subgoal", 'here_map not in st.setdefault("new", [])' in blk)
ck("...and getting closer still resets it as before",
   'st["best"], st["since"], st["at"] = d, 0, here_map' in blk)

exs = inspect.getsource(E.Executor._explore_step)
ck("explore's refusal no longer calls it going backwards",
   "so walking to one is going" not in exs and "whether to go is yours" in exs)
ck("...but keeps the printed-map fact", "is AWAY from it" in exs)

ck("a sweep a won trainer battle stopped goes on, up to three times",
   "for _resume in range(3):" in exs and "sweep_resumed_after_trainer" in exs
   and "EVENT_BEAT_" in exs and "TRAINER" in exs)
ck("...but not after a script, a loss or a map change",
   '_now_s.get("mode") != "overworld"' in exs and "!= ((_pre_sweep" in exs
   and "if (not _won" in exs)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

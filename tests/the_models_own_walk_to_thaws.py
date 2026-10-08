#!/usr/bin/env python3
"""The model's own walk_to goes out with "thaw", like its use_warp and
interact.

Run 37, 2026-10-08: walk_to has its own handler (the retry from other
walked parts of the map), and it sent walk_to past _named, so the rule of
2026-09-05 (a wall the model's own switch opened is walked through on the
model's own op) never reached walk_to. In the Pokemon Mansion the run
flipped the switch, sent walk_to(12,14), and was refused eight times over
"2 cell(s) that were WALLS the last time they were on screen", each time
told a walk_to it sent itself would go through.

Pinned: _named adds thaw to walk_to, use_warp and interact, never while
explore runs the walk, never twice; every send in the walk_to handler and
the after-fights re-send go out named; no bare walk_to send of the step
is left. Synthetic and source."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
ex._explore_params = None
ck("walk_to is named", ex._named("walk_to", {"x": 12, "y": 14}).get("thaw") is True)
ck("so are use_warp and interact",
   ex._named("use_warp", {"x": 1, "y": 1}).get("thaw") is True
   and ex._named("interact", {"name": "X"}).get("thaw") is True)
ck("cross is not", "thaw" not in ex._named("cross", {"dir": "west"}))
ex._explore_params = {"until": "map_change"}
ck("explore's own walks keep the freeze", "thaw" not in ex._named("walk_to", {"x": 1, "y": 1}))
ex._explore_params = None
st = {"x": 1, "y": 1}
ck("the step itself is untouched", ex._named("walk_to", st) is not st and "thaw" not in st)

src = (ROOT / "planner/executor.py").read_text()
ck("every send in the walk_to handler goes out named",
   src.count('self._send_safe("walk_to", **self._named("walk_to", step))') == 3
   and 'self._send_safe("walk_to", **step)' not in src)
ck("the after-fights re-send goes out named",
   "self._send_safe(op, **self._named(op, step))" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

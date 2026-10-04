#!/usr/bin/env python3
"""What the run heard elsewhere rotates: inside a room the least-shown line
comes first, so a third sentence is not dropped for ever behind first ones.

Run 36, 2026-10-03: from Celadon City more than fourteen rooms are in reach,
the round robin only ever read each room's first sentence, and the Diner's
"Psst! There's a basement under the GAME CORNER." never reached a page while
the run hunted the Secret Key for hours (user: "its just been doing the same
stuff"). Replayed on a copy of the run's record: the old code never showed it
in eight page builds; this shows it on the third. Source pins."""
from pathlib import Path
src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
checks = [
    ("lines inside a room are ordered least-shown first",
     "_stand = sorted(_stand, key=lambda l, _r=_rg: _shown.get((_r, l), 0))" in src),
    ("showing a line counts it", "self._hint_shown[(_rg, _ls[_round])] = (" in src),
    ("rooms are still ordered by distance only, never by meaning",
     "said_away.sort(key=lambda t: (t[0], t[1]))" in src),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)

#!/usr/bin/env python3
"""A doorway that is walled in the map's current state says so as it comes
into view.

Run 71, 2026-11-03, enter_rocket_hideout r1-r2: a sweep of the Game Corner
said "came into view: a doorway at (17,4)" (the hideout stairs, closed until
the poster's switch), and the next round's use_warp found it "a WALL right
now". Both true, of different layers; the sweep line alone read as an open
door and cost a round.

Boots the game (a boot test, in tests/run_suite.sh BOOTS) from
tests/fixtures/game_corner_poster_shut.lua with no seen map, and sweeps until
(17,4) is reported. Pinned: it is reported walled right now.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "planner"))
import contract as C  # noqa: E402

RUN = Path(os.environ.get("RED_BRIDGE_DIR") or (ROOT / "run/contract"))
SAVE = ROOT / "tests/fixtures/game_corner_poster_shut.lua"

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

(RUN / "seen.json").unlink(missing_ok=True)
proc = C.start_game(RUN, SAVE, "200")
os.environ["RED_BRIDGE_DIR"] = str(RUN)
try:
    from bridge import Bridge                       # noqa: E402
    import executor as E                            # noqa: E402
    b = Bridge(RUN)
    E.bootstrap(b, cont=True)
    ck("the fixture stands in the Game Corner",
       ((b.obs() or {}).get("map") or {}).get("id") == "GAME_CORNER")
    said = ""
    for _ in range(5):
        d = str(((b.send("sweep") or {}).get("result") or {}).get("detail") or "")
        if "(17,4)" in d:
            said = d
            break
    ck("the stairs come into view", said, said[:300])
    ck("...and are said to be walled right now",
       "a doorway at (17,4) — WALLED right now" in said, said[:300])
finally:
    proc.terminate()

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

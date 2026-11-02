#!/usr/bin/env python3
"""An interact that stood beside the target, pressed, and got nothing says so.

Run 70, Celadon Game Corner (2026-11-02), win_secret_key: interact on
SLOT_MACHINE_12 walked to (13,16), the free cell below it, pressed A and
brought up nothing (these machines answer only from the side), then
reported "no reachable tile adjacent to target — standing on the tiles you
would press from: SLOT_MACHINE_11 at (13,14), SLOT_MACHINE_13 at (12,15)".
The party had stood beside it. The page kept offering the machine and the
model kept walking to it.

Pinned by source shape (in the suite) and, with --boot, live on the
next354 fixture: the refusal names the cell pressed from and says nothing
came up.
"""
from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/game_corner_no_coin_case.lua"
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "harness/shim.lua").read_text()
i = src.index("function OPS.interact(G, c)")
body = src[i:src.index("\nfunction ", i + 10)]
ck("a press beside the target that opened nothing is recorded",
   "pressed_empty[#pressed_empty + 1]" in body)
a = body.find("if #pressed_empty > 0 then")
b = body.find('return false, "no reachable tile adjacent to target — standing on "')
ck("...and said before the no-reachable-tile refusal", 0 < a < b, (a, b))
ck("...in those words", "and nothing came up" in body)

if "--boot" in sys.argv:
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "planner")]
    import contract as C                               # noqa: E402
    run_dir = ROOT / "run/pressempty"
    for f in ("seen.json", "seen_walk.json"):
        (run_dir / f).unlink(missing_ok=True)
    proc = C.start_game(run_dir, FIXTURE, "200")
    try:
        os.environ["RED_BRIDGE_DIR"] = str(run_dir)
        from bridge import Bridge                       # noqa: E402
        from executor import bootstrap                  # noqa: E402
        b = Bridge(run_dir); bootstrap(b, cont=True)
        r = (b.send("interact", name="SLOT_MACHINE_12") or {}).get("result") or {}
        d = str(r.get("detail"))
        ck("live: SLOT_MACHINE_12 says it was pressed and nothing came up",
           "nothing came up" in d and "(13,16)" in d, d)
        ck("live: ...and not that no tile beside it was reachable",
           "no reachable tile adjacent" not in d, d)
    finally:
        os.killpg(proc.pid, signal.SIGTERM)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

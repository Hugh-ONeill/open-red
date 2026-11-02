#!/usr/bin/env python3
"""A slot machine that brings up nothing says so, and every side is tried.

Run 70, Celadon Game Corner (2026-11-02): retrieve_gold_teeth r2 pressed
four machines and each was reported as saying the Safari gate worker's
"Hi! Is it your first time here? / SAFARI ZONE has 4 zones in it...".
OPS.slots read last_text, which outlives the box that printed it, so a
press that opened no box handed the model the line before it. Probed on a
copy of the run's save, teleported to GAME_CORNER (12,16), no Coin Case:
SLOT_MACHINE_13 pressed from below brings up nothing, and after pressing
another machine it "said" that one's "A COIN CASE is required!".
SLOT_MACHINE_24 brings up nothing from below and speaks from its east side,
and the op tried only the first side it reached.

Pinned by source shape (in the suite) and, with --boot, live on the
fixture: 13 reports nothing (twice, after 24 has spoken) and 24 reports
the Coin Case line.
"""
from __future__ import annotations

import os
import re
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/game_corner_no_coin_case.lua"
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "harness/shim.lua").read_text()
i = src.index("function OPS.slots(G, c)")
body = src[i:src.index("\nfunction ", i + 10)]
press = body.index('U.tap(G, "a")')
loop = body.index("for _, s in ipairs({ { mach.x, mach.y + 1")
loop_end = body.index("if not faced then")
ck("the first press happens inside the side loop", loop < press < loop_end)
ck("the side loop stops on a side that spoke",
   re.search(r"text_seq ~= _seq0 then break", body[loop:loop_end]))
guard = body.find("if text_seq == _seq0 then")
read = body.find('local said = tostring(last_text or "")')
ck("a press that printed nothing returns before last_text is quoted",
   0 < guard < read and "brought up" in body[guard:read], (guard, read))

if "--boot" in sys.argv:
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "planner")]
    import contract as C                               # noqa: E402
    run_dir = ROOT / "run/slotpress"
    for f in ("seen.json", "seen_walk.json"):
        (run_dir / f).unlink(missing_ok=True)
    proc = C.start_game(run_dir, FIXTURE, "200")
    try:
        os.environ["RED_BRIDGE_DIR"] = str(run_dir)
        from bridge import Bridge                       # noqa: E402
        from executor import bootstrap                  # noqa: E402
        b = Bridge(run_dir); bootstrap(b, cont=True)
        got = {}
        for m in ("SLOT_MACHINE_24", "SLOT_MACHINE_13", "SLOT_MACHINE_13b"):
            r = (b.send("slots", name=m.rstrip("b"), bet=1, spins=1) or {}).get("result") or {}
            got[m] = str(r.get("detail"))
        ck("24 speaks from a side that answers", "COIN CASE" in got["SLOT_MACHINE_24"], got["SLOT_MACHINE_24"])
        for m in ("SLOT_MACHINE_13", "SLOT_MACHINE_13b"):
            ck(f"{m}: nothing came up, and no stale line is quoted",
               "brought up nothing" in got[m] and "COIN CASE" not in got[m], got[m])
    finally:
        os.killpg(proc.pid, signal.SIGTERM)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

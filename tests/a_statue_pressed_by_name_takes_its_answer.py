#!/usr/bin/env python3
"""A switch statue pressed by name takes its answer on the first press.

Run 62, 2026-10-24: the shim lets a Mansion switch statue's "Press it?" take
the op's answer at once (it takes nothing and gives nothing), but it tested
the tile at the op's own x/y, and the model presses statues by name
(interact name=SWITCH_POKEMON_MANSION_2F_2_11). With no x/y the test never
matched, the box was left open, and every flip spent a round on its answer.
Probed on a copy of the leg 45 checkpoint: one press by name now flips the
statues and leaves the overworld up.

Pinned: the statue test reads the tile the name resolved to.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "harness" / "shim.lua").read_text()
ck("the statue test reads the resolved tile",
   "local _sx, _sy = tx or c.x, ty or c.y" in src)
ck("...a SWITCH name resolves to that tile",
   'smp, sx, sy = tostring(c.name):match("^SWITCH_(.-)_(%d+)_(%d+)$")' in src
   and "tx, ty = tonumber(sx), tonumber(sy)" in src)
ck("...and the exemption still keys on the statue tile",
   "_is_switch = _okt and _t == 61" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

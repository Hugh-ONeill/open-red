#!/usr/bin/env python3
"""A pad landing between two places of one floor is named by the pad, and a
press that a pad ride rescued says what the ride got it.

Silph 5F's (9,15) is the one thing between the main floor and the Card Key's
corner. Landing on it from 9F flooded both sides (the cell under your feet is
a corridor for the reach fill), the landing took the main floor's name, and
the step off into the corner was filed as a walk from the main floor to the
corner, which no walk makes (run 19, 2026-09-29). The same ride's trace read
"interact(ITEM_SILPH_CO_5F_21_16): FAILED — no reachable tile adjacent ...
[CARD_KEY +1 (now 1)]".

Checked live 2026-09-30 by booting a Silph save with the player on each pad:
5F (9,15) -> region 9,15 junction; 5F (11,5) -> 20,0; Saffron Gym (11,15) ->
its room's name. Here: source checks on the shim, the executor's handling.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sh = (ROOT / "harness/shim.lua").read_text()
wr = sh[sh.index("function warp_reach(G, no_ledges, surf, start)"):]
wr = wr[:wr.index("\nend\n")]
ck("the reach fill can start from a cell other than the player's",
   "local ox, oy = (start and start.x) or p.cellX" in wr)
ck("...and only its own start is exempt from the seal", "THROUGH[key(ox, oy)] = nil" in wr)
rr = sh[sh.index("region_reach = function(G)"):]
rr = rr[:rr.index("\nend\n")]
ck("region_reach says when the player stands on a firing warp", "warp_seals(G, w.x, w.y)" in rr
   and "if not fires[px .. \",\" .. py] then return r end" in rr)
ck("...and fills each side from the step off it, the pad sealed",
   "warp_reach(G, true, nil, { x = nx, y = ny })" in rr)
ck("...a junction only when two or more separate places touch it",
   "if sides >= 2 then return r, true end" in rr)
ob = sh[sh.index("local rreach, _junction = region_reach(G)"):]
ob = ob[:ob.index("LAST_MAP is gen1")]
ck("a junction is named by the pad cell", "local name = _junction and here or known[here]" in ob)
ck("...paints no ground with that name", "if _junction then\n            o.map.junction = true\n          else" in ob)
ck("...and is joined to nothing", "if _junction then parts = { name } end" in ob)

import executor as E  # noqa: E402
nf = inspect.getsource(E.Executor.note_frontier)
ck("a junction keeps no exits of its own", 'if keys and not _m.get("junction"):' in nf)

n = E.Executor._reridden_note(
    "interact(name=ITEM_SILPH_CO_5F_21_16,answer=yes): FAILED — no reachable "
    "tile adjacent to target", "ok (moved)")
ck("a rescued press drops its first FAILED verdict",
   "FAILED" not in n and n.startswith("interact(name=ITEM_SILPH_CO_5F_21_16,answer=yes): "), n)
ck("...and carries the ride's own result", n.endswith("from where the ride above set you down: ok (moved)"), n)
src = inspect.getsource(E.Executor)
ck("all three pad rescues rewrite the op's line",
   src.count("note = self._reridden_note(note, _pd)") == 2
   and src.count("note = self._reridden_note(note, _pd2)") == 1)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

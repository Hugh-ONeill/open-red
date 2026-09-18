#!/usr/bin/env python3
"""A floor whose unseen ground lies across water is not finished while the
party can SURF.

Run 27, 2026-09-18: ROUTE_21 is nearly all sea. Once its beach was swept,
its foot frontier read 0 and it left every list as finished, with SURF in
the party and none of its water ever on screen; the run shuttled Route 20
<-> Cinnabar looking for another way.

Pinned: the water frontier is kept per region and saved; the remote count
adds it only while SURF is known AND the SOULBADGE is held; a swept beach
("done" on foot) does not zero it; the unseen-ground row says how many spots
are across water. Nothing says where the water goes. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def fake(surf=True, badge=True):
    ex = object.__new__(E.Executor)
    ex.region_seen = {"ROUTE_21|10,88": 0}
    ex.region_seen_water = {"ROUTE_21|10,88": 5}
    ex.frontier_here = {"ROUTE_21|10,88": 0}
    ex.visits = {"ROUTE_21|10,88": 4}
    ex._region_mark = {"ROUTE_21|10,88": [1, 2, 3]}
    ex._mark_now = [1, 2, 3]
    ex._knows_surf = surf
    ex._soulbadge = badge
    return ex


ck("a swept beach with sea past it still counts, with SURF usable",
   fake()._unseen_there("ROUTE_21|10,88") == (5, ""), fake()._unseen_there("ROUTE_21|10,88"))
ck("...not without SURF", fake(surf=False)._unseen_there("ROUTE_21|10,88") == (0, ""))
ck("...not without the SOULBADGE", fake(badge=False)._unseen_there("ROUTE_21|10,88") == (0, ""))
ex = fake(); ex.region_seen["ROUTE_21|10,88"] = 3; ex.frontier_here["ROUTE_21|10,88"] = 2
ck("foot and water add", ex._unseen_there("ROUTE_21|10,88") == (8, ""), ex._unseen_there("ROUTE_21|10,88"))
ex = fake(); ex.region_seen["ROUTE_21|10,88"] = 3
ck("a part stood in with nothing left on foot keeps its water",
   ex._unseen_there("ROUTE_21|10,88") == (5, ""), ex._unseen_there("ROUTE_21|10,88"))
ex = fake(); ex.region_seen_water = {}; ex.region_seen["ROUTE_21|10,88"] = 3
ck("...and with no water it is done, as before", ex._unseen_there("ROUTE_21|10,88") == (0, "done"))

src = (ROOT / "planner/executor.py").read_text()
ck("the water frontier is recorded per region from the shim's count",
   '_fw_n = int(_sn.get("frontier_water_n") or 0)' in src
   and "self.region_seen_water[here] = _fw_n" in src)
ck("...and saved with the ledger",
   '"region_seen_water": getattr(self, "region_seen_water", {}),' in src
   and 'self.region_seen_water = data.get("region_seen_water", {}) or {}' in src)
ck("the unseen-ground row lists water-only floors and says how many spots are across water",
   '| set(getattr(self, "region_seen_water", None) or {}))' in src
   and "of them across water, which " in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

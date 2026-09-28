#!/usr/bin/env python3
"""The printed map is the booklet's (user ruling, 2026-09-28; audit PT-17b).

The US instruction booklet carries a World Map of Kanto (pp.4-5), so the
printed layout is pamphlet tier whether or not the run holds the TOWN_MAP
item, which it only picks up by luck. Before this the run was told "you are
not carrying a TOWN MAP" while static_hops ranked explore on the full map
underneath. RED_PRINTED_MAP=bag restores the item gate for comparison
replays.

Synthetic, plus source checks.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
os.environ.pop("RED_PRINTED_MAP", None)
import author as A  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


d = Path(tempfile.mkdtemp(prefix="pmap_"))
(d / "run").mkdir()
(d / "run/obs.json").write_text(json.dumps({"bag": {"POKE_BALL": 3}}))
here = os.getcwd()
os.chdir(d)
try:
    ck("the author has the printed map with no TOWN_MAP in the bag",
       A.holding_town_map() is True)
    os.environ["RED_PRINTED_MAP"] = "bag"
    ck("...and RED_PRINTED_MAP=bag puts the item gate back",
       A.holding_town_map() is False)
    ck("...in the executor too",
       E.Executor._holding_town_map({"bag": {}}) is False
       and E.Executor._holding_town_map({"bag": {"TOWN_MAP": 1}}) is True)
    os.environ.pop("RED_PRINTED_MAP")
finally:
    os.chdir(here)
ck("the executor has it with an empty bag",
   E.Executor._holding_town_map({"bag": {}}) is True)
ck("the distances behind explore's ranking use the printed map by default",
   E.PRINTED_MAP_HELD is True)
ck("...and not under RED_PRINTED_MAP=bag",
   subprocess.run([sys.executable, "-c",
                   "import sys; sys.path.insert(0, 'planner'); import executor as E; "
                   "sys.exit(0 if E.PRINTED_MAP_HELD is False else 1)"],
                  cwd=ROOT, env=dict(os.environ, RED_PRINTED_MAP="bag"),
                  capture_output=True).returncode == 0)

shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim names a seam off the printed map unless told bag",
   'local _held = (os.getenv("RED_PRINTED_MAP") or "always") ~= "bag"' in shim)
exs = (ROOT / "planner/executor.py").read_text()
ck("the whole-map line is the printed map's, not an item's",
   'THE PRINTED MAP OF KANTO (every road and town it shows' in exs
   and 'f"\\nTHE TOWN MAP (every road' not in exs)

# The places line names only what the printed maps name: no floors, rooms
# or houses off the warp table (audit 6b).
PRINTED = {"CERULEAN CAVE", "SAFARI ZONE", "POKéMON TOWER", "POWER PLANT",
           "ROCK TUNNEL", "DIGLETT's CAVE", "VIRIDIAN FOREST", "SEAFOAM ISLANDS",
           "ROUTE 22", "VICTORY ROAD", "SEA COTTAGE", "MT.MOON",
           "UNDERGROUND PATH", "S.S.ANNE"}
labels = {lbl for places in A.MAP_DOORS.values() for lbl in places}
ck("every place the doors line names is on the printed map",
   labels and labels <= PRINTED, sorted(labels - PRINTED))

# Split roads are said in the GAME's order (user, 2026-09-28): Route 9
# reaches Route 10's north part, not Rock Tunnel as the booklet draws it.
import split_roads as S  # noqa: E402
bad = [r for r, (place, frm, _n, _f, to) in S.SPLITS.items()
       if set(E.MAP_EDGES.get(r, {}).values()) != {frm, to}
       or place not in (A.MAP_DOORS.get(r) or {})]
ck("each split road's two ends are its printed neighbours and its place is pinned there",
   not bad, bad)
ck("Rock Tunnel is said inside Route 10, reached from Route 9",
   "ROUTE_9 -> ROUTE_10's north part -> ROCK TUNNEL -> ROUTE_10's south part"
   " -> LAVENDER_TOWN" in A.doors_text())
ck("the walker's printed-map line carries the same block",
   "route_line += split_roads.split_roads_text()" in exs)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

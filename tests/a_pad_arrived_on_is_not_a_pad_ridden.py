#!/usr/bin/env python3
"""Arriving through a warp pad does not say where riding it back lands.

Silph 5F's pad at (9,15) sits in a corridor: walked onto from the main
floor it sends you to 9F, and only riding 9F's (17,15) back sets you down
on the side the CARD KEY is on, past a Rocket. Arriving on 9F wrote "9F's
pad leads back to 5F's main floor" (n=0), so the pad read as ridden and
the explorer never offered it (run 19, 2026-09-29).

A pad whose twin opens onto ground on screen that no walk reached is kept
apart and named as such (user: "its on screen information, you can see
the corridor it leads to"); one whose twin opens onto nothing new is a
door like any other.

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def fresh():
    x = object.__new__(E.Executor)
    x.explored, x.visits, x._entered_map = {}, {}, {}
    x._cur_target = None
    x.logged = []
    x.log = lambda kind, **kw: x.logged.append((kind, kw))
    x._save_memory = lambda: None
    x._count_visit = lambda r: None
    x.pad_lands = {}
    return x


def obs(mid, px, py, warps, outdoor=False):
    return {"map": {"id": mid, "outdoor": outdoor, "warps": warps},
            "player": {"x": px, "y": py}}


NINE = [{"x": 17, "y": 15, "dest": "SILPH_CO_5F", "look": "pad"}]
x = fresh()
x._note_arrival("SILPH_CO_5F|20,0", "SILPH_CO_9F|14,0",
                obs("SILPH_CO_5F", 9, 15, [{"x": 9, "y": 15, "dest": "SILPH_CO_9F",
                                            "look": "pad", "opens_past": True}]),
                obs("SILPH_CO_9F", 17, 15, NINE))
ck("the twin opens onto seen, unreached ground: no way back in the walked graph",
   "17,15" not in x.explored.get("SILPH_CO_9F|14,0", {}), x.explored)
ck("...where it sets you down is kept", x.pad_lands.get("SILPH_CO_9F|17,15")
   == {"map": "SILPH_CO_5F", "at": "9,15"}, getattr(x, "pad_lands", None))
ck("...and logged", any(k == "pad_arrival_not_reversed" for k, _ in x.logged))
x.map_doors = {"SILPH_CO_9F": ["17,15", "14,0"]}
x.warp_looks = {"SILPH_CO_9F": {"17,15": "pad", "14,0": "stairs_up"}}
line = x._pads_unridden_in_building({"SILPH_CO_9F"})
ck("the pads line says it sets you down beside seen ground",
   "(17,15) sets you down ON SILPH_CO_5F's pad at (9,15)" in line
   and "no walk reached" in line, line)

x = fresh()
x._note_arrival("SILPH_CO_5F|20,0", "SILPH_CO_9F|14,0",
                obs("SILPH_CO_5F", 9, 15, [{"x": 9, "y": 15, "dest": "SILPH_CO_9F",
                                            "look": "pad"}]),
                obs("SILPH_CO_9F", 17, 15, NINE))
ck("a twin opening onto nothing new is a door like any other",
   x.explored.get("SILPH_CO_9F|14,0", {}).get("17,15", {}).get("to") == "SILPH_CO_5F|20,0",
   x.explored)

x = fresh()
x._note_arrival("SILPH_CO_4F|20,0", "SILPH_CO_10F|8,9",
                obs("SILPH_CO_4F", 6, 15, [{"x": 3, "y": 15, "dest": "SILPH_CO_10F",
                                            "look": "pad"}]),
                obs("SILPH_CO_10F", 13, 15, [{"x": 13, "y": 15, "dest": "SILPH_CO_4F",
                                              "look": "pad"}]), left_by="3,15")
ck("the twin is the tile left by, not where the op began",
   x.explored.get("SILPH_CO_10F|8,9", {}).get("13,15", {}).get("to") == "SILPH_CO_4F|20,0",
   x.explored)

x = fresh()
x._note_arrival("SILPH_CO_5F|20,0", "SILPH_CO_9F|14,0",
                obs("SILPH_CO_5F", 9, 15, []), obs("SILPH_CO_9F", 17, 15, NINE))
ck("a twin not seen at all claims nothing",
   "17,15" not in x.explored.get("SILPH_CO_9F|14,0", {}), x.explored)

x = fresh()
x._note_arrival("SILPH_CO_4F|20,0", "SILPH_CO_5F|20,0",
                obs("SILPH_CO_4F", 26, 0, []),
                obs("SILPH_CO_5F", 26, 0,
                    [{"x": 26, "y": 0, "dest": "SILPH_CO_4F", "look": "stairs_down"}]))
ck("arriving by stairs still writes the way back",
   x.explored.get("SILPH_CO_5F|20,0", {}).get("26,0", {}).get("to") == "SILPH_CO_4F|20,0",
   x.explored)

x = fresh()
x.warp_looks = {"SILPH_CO_9F": {"17,15": "pad", "14,0": "stairs_up"}}
x.explored = {"SILPH_CO_9F|14,0": {
    "17,15": {"to": "SILPH_CO_5F|20,0", "n": 0},
    "14,0": {"to": "SILPH_CO_10F|8,0", "n": 0},
    "9,3": {"to": "SILPH_CO_3F|3,3", "n": 2}}}
x.warp_looks["SILPH_CO_9F"]["9,3"] = "pad"
ck("load drops the one pad known only by arriving", x._drop_pad_arrivals() == 1)
ck("...the ridden pad and the stairs stay",
   set(x.explored["SILPH_CO_9F|14,0"]) == {"14,0", "9,3"}, x.explored)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

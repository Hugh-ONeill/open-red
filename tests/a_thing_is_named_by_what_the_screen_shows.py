#!/usr/bin/env python3
"""A sign, a fossil, a Pokemon on a shared sprite and a stranger are named by
what the screen shows, not by what the map data says they are.

The ledger listed "TEXT_FUCHSIACITY_GYM_SIGN (sign at 5,29) — never pressed",
the fossils as MTMOONB2F_HELIX_FOSSIL / DOME_FOSSIL before the blind pick, and
the birds as ZAPDOS and MOLTRES (user, 2026-09-29: "the player cant see the
sign title"). harness/public_names.lua names them SIGN_/FOSSIL_/POKEMON_<MAP>_
x_y and the like; the real names still resolve in interact; the planner
carries a ledger written under the old names over (planner/public_names.json).

Runs the naming module under lua against the game's map data; source checks
on the shim; the ledger rewrite on a small ledger (no live file is touched).
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
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


MAPS = Path.home() / "Developer/gen1recomp/data/generated/maps.lua"
LUA = f'''
local P = dofile("{ROOT}/harness/public_names.lua")
local M = dofile("{MAPS}")
local function obj(map, name)
  for _, o in ipairs(M[map].objects) do
    if o.name == name then return P.object(map, o, 0, 0) end
  end
  return "MISSING"
end
local function sign(map, text)
  for _, s in ipairs(M[map].signs) do
    if s.text == text then return P.sign(map, s) end
  end
  return "MISSING"
end
print(sign("FUCHSIA_CITY", "TEXT_FUCHSIACITY_GYM_SIGN"))
print(sign("VIRIDIAN_CITY", "TEXT_VIRIDIANCITY_TRAINER_TIPS1"))
print(sign("CELADON_MART_ROOF", "TEXT_CELADONMARTROOF_VENDING_MACHINE1"))
print(obj("MT_MOON_B2F", "MTMOONB2F_HELIX_FOSSIL"))
print(obj("MT_MOON_B2F", "MTMOONB2F_DOME_FOSSIL"))
print(obj("VICTORY_ROAD_2F", "VICTORYROAD2F_MOLTRES"))
print(obj("BILLS_HOUSE", "BILLSHOUSE_BILL_POKEMON"))
print(obj("BILLS_HOUSE", "BILLSHOUSE_BILL1"))
print(obj("FUCHSIA_CITY", "FUCHSIACITY_ERIK"))
print(obj("POKEMON_FAN_CLUB", "POKEMONFANCLUB_CHAIRMAN"))
print(obj("POWER_PLANT", "POWERPLANT_VOLTORB1"))
print(obj("SILPH_CO_5F", "SILPHCO5F_POKEMON_REPORT1"))
print(obj("PEWTER_GYM", "PEWTERGYM_BROCK"))
print(obj("ROUTE_12", "ROUTE12_SNORLAX"))
print(obj("FUCHSIA_CITY", "FUCHSIACITY_CHANSEY"))
local od = P.resolve("MT_MOON_B2F", M.MT_MOON_B2F, "FOSSIL_MT_MOON_B2F_13_6")
print(od and od.name or "nil")
local sg = P.resolve("FUCHSIA_CITY", M.FUCHSIA_CITY, "SIGN_FUCHSIA_CITY_5_29")
print(sg and (sg.x .. "," .. sg.y) or "nil")
'''
if not MAPS.exists():
    print(f"skip: no map data at {MAPS}")
    sys.exit(0)
got = subprocess.run(["lua", "-e", LUA], capture_output=True, text=True)
out = got.stdout.split("\n")
ck("the naming module runs against the game's maps", got.returncode == 0, got.stderr)
if got.returncode == 0:
    want = [
        ("a signpost is a sign at its place", "SIGN_FUCHSIA_CITY_5_29"),
        ("a Trainer Tips board is a signpost too", "SIGN_VIRIDIAN_CITY_19_1"),
        ("a vending machine keeps its name (it looks like one)",
         "TEXT_CELADONMARTROOF_VENDING_MACHINE1"),
        ("the helix fossil is a fossil at its place", "FOSSIL_MT_MOON_B2F_13_6"),
        ("...and so is the dome: the pick is blind, as in the game", "FOSSIL_MT_MOON_B2F_12_6"),
        ("a legendary on a bird sprite is a Pokemon", "POKEMON_VICTORY_ROAD_2F_11_5"),
        ("Bill in the machine is a Pokemon", "POKEMON_BILLS_HOUSE_6_5"),
        ("Bill in his own house keeps his name", "BILLSHOUSE_BILL1"),
        ("Erik on a Fisher sprite in the street is a fisher", "FISHER_FUCHSIA_CITY_30_14"),
        ("the Fan Club's Chairman keeps his name", "POKEMONFANCLUB_CHAIRMAN"),
        ("a Voltorb waiting in a ball is a ball", "ITEM_POWER_PLANT_9_20"),
        ("a Silph report is a clipboard", "CLIPBOARD_SILPH_CO_5F_22_12"),
        ("a gym leader keeps his name (the booklet)", "PEWTERGYM_BROCK"),
        ("Snorlax on its own sprite keeps its name", "ROUTE12_SNORLAX"),
        ("a walker is named by where the map puts it, not by x,y passed",
         "POKEMON_FUCHSIA_CITY_31_5"),
        ("a published name resolves back to the map's object", "MTMOONB2F_HELIX_FOSSIL"),
        ("...and a sign's to its cell", "5,29"),
    ]
    for i, (n, w) in enumerate(want):
        ck(n, i < len(out) and out[i] == w, out[i] if i < len(out) else "")

sh = (ROOT / "harness/shim.lua").read_text()
ck("the shim loads the naming module into package.loaded, not a new local",
   "package.loaded.red_public_names = dofile(dir .. \"/public_names.lua\")" in sh)
ob = sh[sh.index("for _, npc in ipairs(G.overworld.npcs or {}) do\n      local d = npc.def or {}"):]
ob = ob[:4000]
ck("observe names every live object through the module",
   "name = package.loaded.red_public_names.object(" in ob)
ck("observe names every sign through the module",
   "local nm = package.loaded.red_public_names.sign(" in sh)
it = sh[sh.index("function OPS.interact("):]
it = it[:it.index("\nfunction OPS.", 10)]
ck("interact resolves a published name to the map's own before any lookup",
   it.index("red_public_names.resolve(") < it.index("^ITEM_(.-)_(%d+)_(%d+)$"))
ck("...and people are matched by the map's name", "(npc.def or {}).name == rn" in it)
ck("a ball is a ball by its sprite too (the Voltorb traps)",
   "red_public_names.is_ball(d2)" in it)
ck("no raw object name is emitted by the fence/occupied lines",
   'tostring((npc.def or {}).name or "someone")' not in sh
   and 'tostring((npc.def or {}).name or "something")' not in sh)

# the ledger carry-over
import executor as E  # noqa: E402
led = {"sightings": {"MT_MOON_B2F|20,5": ["MTMOONB2F_HELIX_FOSSIL", "MTMOONB2F_ROCKET1"]},
       "touched": {"FUCHSIA_CITY|20,0": ["TEXT_FUCHSIACITY_GYM_SIGN"]},
       "hints": {"FUCHSIA_CITY|20,0": ["TEXT_FUCHSIACITY_GYM_SIGN: FUCHSIA CITY POKeMON GYM"]},
       "press_log": {"MT_MOON_B2F|20,5": [["MTMOONB2F_DOME_FOSSIL", "You want the DOME FOSSIL?"]]}}
new, n = E._public_names(led)
ck("an old ledger's names are carried over", n == 4, n)
ck("...sightings", new["sightings"]["MT_MOON_B2F|20,5"] == ["FOSSIL_MT_MOON_B2F_13_6", "MTMOONB2F_ROCKET1"],
   new["sightings"])
ck("...hints keep what was said", new["hints"]["FUCHSIA_CITY|20,0"] == ["SIGN_FUCHSIA_CITY_5_29: FUCHSIA CITY POKeMON GYM"])
ck("...the words the game said are not rewritten (DOME FOSSIL is not a name)",
   new["press_log"]["MT_MOON_B2F|20,5"] == [["FOSSIL_MT_MOON_B2F_12_6", "You want the DOME FOSSIL?"]])
again, n2 = E._public_names(new)
ck("a carried-over ledger is left alone", n2 == 0 and again == new)
lm = E.Executor._load_memory
ck("the executor carries its ledger over on load", "_public_names(data)" in __import__("inspect").getsource(lm))
tab = json.loads((ROOT / "planner/public_names.json").read_text())
ck("the committed table is what the module says today",
   tab.get("TEXT_FUCHSIACITY_GYM_SIGN") == "SIGN_FUCHSIA_CITY_5_29"
   and tab.get("POWERPLANT_ZAPDOS") == "POKEMON_POWER_PLANT_4_9")

# the judge still knows the thing in Bill's house is in Bill's house
import author as A  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "explored.json"
    p.write_text(json.dumps({"sightings": {"BILLS_HOUSE|2,1": ["POKEMON_BILLS_HOUSE_6_5"],
                                           "VERMILION_PIDGEY_HOUSE|2,1": ["POKEMON_VERMILION_PIDGEY_HOUSE_3_5"]},
                             "touched": {}}))
    ck("a Pokemon never pressed in Bill's house answers to Bill",
       A.untouched_named("Help Bill at Sea Cottage", p) == [("BILLS_HOUSE|2,1", "POKEMON_BILLS_HOUSE_6_5")],
       A.untouched_named("Help Bill at Sea Cottage", p))
    ck("...but a house's other words are not a person (the Pidgey house)",
       A.untouched_named("Catch a Pidgey", p) == [])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

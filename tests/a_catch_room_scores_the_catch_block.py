#!/usr/bin/env python3
"""The catch block is scored in a room built for it, and the words the
model authors it from say what the code does.

The spec's `catch` block rode unexamined from v8 to v14 — every arena is a
trainer fight and the catch branch runs only on a wild one — while its
description still said "weaken with the gentlest non-KO move until below
that fraction", which stopped being true when the status move, the
seen-damage rule and the named-want cap landed (user, 2026-09-16: "build
the catch room and fix the stale docs").

Pinned here, synthetically (no game, no model):
  * the catch rooms are in the arena table as their own kind, their saves
    and specs are named, and each spec names a want, a battle budget and a
    target count, stands the party on a grass cell and marks every trainer
    on the map beaten;
  * a catch result reads as caught-of-met, is ranked by catches then by
    fewer balls, and its quality rewards thrift;
  * an arena points the outline reader at its own room, so the live run's
    type legs cannot widen a room's want;
  * the DSL doc the model reads names the status move, the 45% seen-damage
    rule, the 0.4 cap, the run after max_balls, and the ball class — and no
    longer says "gentlest non-KO move until".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import battle_policy as bp        # noqa: E402
import gin_gym_arenas as GG       # noqa: E402
import policy_author as PA        # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


# ---- the table ------------------------------------------------------------
for name in ("catch_weedle", "catch_abra", "catch_powerplant"):
    kind, save, spec = PA.ARENAS.get(name, (None, None, None))
    ck(f"{name} is a catch arena", kind == "catch")
    ck(f"{name} names its save and spec",
       str(save).endswith(f"run/arena_{name}.lua")
       and str(spec).endswith(f"plans/arena_{name}.json"))
ck("the catch rooms are not gyms and join no gym sweep",
   not any(r.startswith("catch") for r in PA.GYM_ROOMS))

# ---- what the builder writes ---------------------------------------------
GRASS = {"VIRIDIAN_FOREST": 32, "ROUTE_24": 82}


def spawns_here(map_id, x, y) -> bool:
    """The engine's rule (OverworldController, mirrored in the shim's
    grind): grass anywhere, and on an indoor map past firstIndoorMap whose
    tileset is not FOREST, every walkable tile."""
    import subprocess
    import tempfile
    lua = (f'local G="{Path.home()}/Developer/gen1recomp/data/generated/";'
           'local m=dofile(G.."maps.lua")[arg[1]];'
           'local t=dofile(G.."tilesets.lua")[m.tileset];'
           'local ind=dofile(G.."field.lua").indoorEncounters;'
           'local cx,cy=tonumber(arg[2]),tonumber(arg[3]);'
           'local tx,ty=cx*2,cy*2+1;'
           'local bx,by=math.floor(tx/4),math.floor(ty/4);'
           'local b=t.blocks[m.blocks[by*m.width+bx+1]+1];'
           'local c=b[(ty%4)*4+(tx%4)+1];'
           'local walk=false;'
           'for k,v in pairs(t.walkable or {}) do if v==c or (k==c and v==true) then walk=true end end;'
           'local indoor=m.index and m.index>=ind.firstIndoorMap and m.tileset~=ind.excludedTileset;'
           'print((c==t.grassTile) or (indoor and walk))')
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(lua)
    out = subprocess.run(["lua", f.name, map_id, str(x), str(y)],
                         capture_output=True, text=True, timeout=30)
    return out.stdout.strip() == "true"


for c in GG.CATCHES:
    spec = GG.build_catch(c)
    ck(f"{c['name']} names what it hunts, a battle budget and a target count",
       (spec["catch"]["want_types"] or spec["catch"]["want_species"])
       and spec["catch"]["encounters"] > 0 and spec["catch"]["targets"] > 0)
    _engine = {l.strip() for l in (ROOT / "planner/engine_types.txt")
               .read_text().splitlines() if l.strip()}
    ck(f"{c['name']} wants a type the engine spells that way, or a species",
       set(spec["catch"]["want_types"]) <= _engine
       and set(spec["catch"]["want_species"])
       <= __import__("executor").Executor._species_names())
    ck(f"{c['name']} starts the party where wild Pokemon appear",
       spawns_here(c["map"], *c["start"]) is True)
    ck(f"{c['name']} marks every trainer on the map beaten",
       set(spec["set_flags"]) == set(GG.trainer_flags(c["map"]))
       and len(spec["set_trainers"]) == len(GG.room_objects(c["map"])))
    ck(f"{c['name']} carries balls", spec["bag"].get("POKE_BALL", 0) > 0)

# ---- the three kinds of catch (user, 2026-09-16) -----------------------------
_by = {c["name"]: c for c in GG.CATCHES}
ck("an easy catch: WEEDLE in the Forest",
   _by["catch_weedle"]["want_species"] == ["WEEDLE"]
   and _by["catch_weedle"]["map"] == "VIRIDIAN_FOREST")
ck("a runner: ABRA, with a lead whose status moves cost the only turn",
   _by["catch_abra"]["want_species"] == ["ABRA"]
   and {"STUN_SPORE", "SLEEP_POWDER"}
   <= set(GG.build_catch(_by["catch_abra"])["party"][0]["moves"]))
_pp = GG.build_catch(_by["catch_powerplant"])
ck("a hard catch: ELECTRIC in the Power Plant, with a VILEPLUME that sleeps "
   "and paralyses",
   _by["catch_powerplant"]["want_types"] == ["ELECTRIC"]
   and _pp["party"][0]["species"] == "VILEPLUME"
   and {"SLEEP_POWDER", "STUN_SPORE"} <= set(_pp["party"][0]["moves"])
   and _pp["bag"].get("GREAT_BALL", 0) > 0)

# ---- first_ball ---------------------------------------------------------------
ABRA = {"mode": "battle",
        "battle": {"kind": "wild",
                   "foe": {"species": "ABRA", "level": 10, "hp": 25,
                           "maxhp": 25, "types": ["PSYCHIC_TYPE"]},
                   "me": {"species": "BUTTERFREE", "level": 20, "hp": 55,
                          "maxhp": 55, "types": ["BUG", "FLYING"],
                          "moves": [{"index": 1, "id": "SLEEP_POWDER", "pp": 15,
                                     "type": "GRASS", "power": 0},
                                    {"index": 2, "id": "CONFUSION", "pp": 25,
                                     "type": "PSYCHIC_TYPE", "power": 50}]}},
        "party": [{"species": "BUTTERFREE", "level": 20, "hp": 55,
                   "max_hp": 55}],
        "bag": {"POKE_BALL": 10}}
WANT = {"species": {"ABRA"}, "types": set()}
_c0 = {"turn": 1, "intent": "catch", "want": WANT, "journal": {}}
_plain = {"catch": {"ball": "ball", "throw_at_hp_frac": 0.2, "max_balls": 5}}
ck("without first_ball, a sleep move comes first",
   bp.choose(ABRA, _plain, dict(_c0)).get("op") == "battle_move")
_fb = {"catch": dict(_plain["catch"], first_ball=True)}
_ctx = dict(_c0)
_o1 = bp.choose(ABRA, _fb, _ctx)
_o2 = bp.choose(ABRA, _fb, _ctx)
ck("with first_ball, one ball goes on the first turn",
   _o1.get("op") == "throw_ball" and "first_ball" in _o1.get("_why", ""))
ck("...and only one: the status move follows",
   _o2.get("op") == "battle_move" and _o2.get("index") == 1)
ck("first_ball validates as a bool",
   not bp.validate_spec(_fb)
   and any("first_ball" in p for p in bp.validate_spec(
       {"catch": dict(_plain["catch"], first_ball="yes")})))
ck("the doc the model authors from names first_ball and why",
   '"first_ball"' in PA.DSL_DOC and "TELEPORT" in PA.DSL_DOC
   and "first_ball" in bp.__doc__)

# ---- probe_hit (user, 2026-09-16: "probe hits are how a human would tackle it")
PIKA = {"mode": "battle",
        "battle": {"kind": "wild",
                   "foe": {"species": "PIKACHU", "level": 22, "hp": 50,
                           "maxhp": 50, "types": ["ELECTRIC"],
                           "status": "SLP"},
                   "me": {"species": "VILEPLUME", "level": 40, "hp": 120,
                          "maxhp": 120, "types": ["GRASS", "POISON"],
                          "moves": [{"index": 1, "id": "SLEEP_POWDER", "pp": 15,
                                     "type": "GRASS", "power": 0},
                                    {"index": 2, "id": "ACID", "pp": 30,
                                     "type": "POISON", "power": 40},
                                    {"index": 3, "id": "MEGA_DRAIN", "pp": 10,
                                     "type": "GRASS", "power": 40}]}},
        "party": [{"species": "VILEPLUME", "level": 40, "hp": 120,
                   "max_hp": 120}],
        "bag": {"POKE_BALL": 10}}
EWANT = {"species": set(), "types": {"ELECTRIC"}}
_pc = {"catch": {"ball": "ball", "throw_at_hp_frac": 0.2, "max_balls": 5}}
_pr = {"catch": dict(_pc["catch"], probe_hit=True)}
_x0 = {"turn": 1, "intent": "catch", "want": EWANT, "journal": {},
       "status_tried": True}
ck("without probe_hit, nothing seen means a throw at full health",
   bp.choose(PIKA, _pc, dict(_x0)).get("op") == "throw_ball")
_xp = dict(_x0)
_p1 = bp.choose(PIKA, _pr, _xp)
ck("with probe_hit, the weakest attack is used once",
   _p1.get("op") == "battle_move" and "probe_hit" in _p1.get("_why", ""))
ck("...once only: the next turn throws or weakens, it does not probe again",
   "probe_hit" not in bp.choose(PIKA, _pr, _xp).get("_why", ""))
_low = {**PIKA, "battle": {**PIKA["battle"],
                           "foe": dict(PIKA["battle"]["foe"], hp=20)}}
ck("no probe on a foe already under half its HP",
   bp.choose(_low, _pr, dict(_x0, foe_hp0=50)).get("op") == "throw_ball")
ck("probe_hit validates as a bool",
   not bp.validate_spec(_pr)
   and any("probe_hit" in p for p in bp.validate_spec(
       {"catch": dict(_pc["catch"], probe_hit=1)})))
ck("the doc the model authors from names probe_hit and its risk",
   '"probe_hit"' in PA.DSL_DOC and "knock it out" in PA.DSL_DOC
   and "probe_hit" in bp.__doc__)

# ---- scoring ----------------------------------------------------------------
r = {"arena": "catch", "gauntlet_trials": 2, "met": 4, "caught": 3,
     "balls": 6, "battles": 40, "blackouts": 0, "bodies": 2.0,
     "agree": 0, "scored": 0, "dmg_gap": 0.0, "rival_wins": 0,
     "rival_trials": 0, "badge": 0, "pewter": 0,
     "gauntlet_detail": ["caught 2 of 2 GRASS met in 20 wild battle(s), "
                         "3 ball(s) thrown; stopped at 20 wild battles",
                         "caught 1 of 2 GRASS met in 20 wild battle(s), "
                         "3 ball(s) thrown, 1 lost in the fight; stopped "
                         "at 20 wild battles"]}
ck("a catch room's fraction is caught of met", PA.arena_fraction(r) == 0.75)
ck("a room that met nothing divides by nothing", PA.arena_fraction(
    dict(r, met=0, caught=0)) == 0.0)
thrifty = dict(r, balls=3)
ck("the same catches for fewer balls score higher",
   PA.arena_points(thrifty) > PA.arena_points(r))
ck("one more catch always beats any thrift",
   PA.arena_points(dict(r, caught=4, balls=40))
   > PA.arena_points(dict(r, caught=3, balls=3)))
ck("the rank key orders catches, then fewer balls",
   PA.rank_key(dict(r, caught=3, balls=4)) > PA.rank_key(r)
   and PA.rank_key(dict(r, caught=4, balls=20)) > PA.rank_key(r))
fb = PA.feedback_text("v13", r)
ck("the feedback says caught of met, and balls",
   "caught 3 of the 4 wanted Pokemon met" in fb and "6 ball(s) thrown" in fb
   and "trial 2: caught 1 of 2" in fb)

# ---- an arena has no outline ---------------------------------------------------
import executor as E                # noqa: E402
import tempfile                      # noqa: E402
live_run, live_plans = E.RUN, E.PLANS
room = Path(tempfile.mkdtemp(prefix="catchroom_"))
PA._bind_books(room)
ck("an arena reads its outline from its own room", E.PLANS == room)
E.bind_run(live_run)
E.PLANS = live_plans

# ---- the words the model authors from --------------------------------------
doc = PA.DSL_DOC
i = doc.index("  catch:")
block = doc[i:doc.index("  lead:", i)]
ck("the doc no longer says gentlest-non-KO-until",
   "gentlest non-KO" not in block)
ck("the doc names the status move first",
   "SLEEP_POWDER" in block and "THUNDER_WAVE" in block
   and set(bp.CATCH_STATUS_MOVES) <= set(
       w.strip(",.()") for w in block.split()))
ck("the doc names the seen-damage rule", "SEEN" in block and "45%" in block)
ck("the doc names the 0.4 cap with a named want", "0.4" in block)
ck("the doc names the run after max_balls", "runs and leaves the wild" in block)
ck("the doc names the ball class and its order",
   "POKE_BALL before GREAT_BALL before ULTRA_BALL" in block
   and bp.BALL_LADDER == ("POKE_BALL", "GREAT_BALL", "ULTRA_BALL"))
ck("the module's own DSL comment was rewritten too",
   "gentlest non-KO" not in bp.__doc__ and "45%" in bp.__doc__)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""Build a clean-room arena for every gym in the game, in order.

WHY EIGHT AND NOT FOUR. The first four arenas were scavenged from whatever
a real run happened to be carrying when it walked into a gym, and three of
them saturated: once a policy's healing rules could actually reach the bag,
every candidate swept Pewter, Celadon and Fuchsia and the scores stopped
telling them apart (2026-09-15, user: "a more serious clean room setup
through all of the gyms in order and teams with levels, mons, and
mixed-tiered items matching the difficulty of each gym to really put it to
the test and discriminate out a little better").

So each arena here is BUILT, not found:

  * The party is the one a run would plausibly have at that gym, at the
    level it would be if it had not been ground — the lead about level
    with the leader's ace, and one or two members well under, because
    attrition is what an item policy is FOR. Movesets are the natural
    ones: level-1 moves plus everything learned at or below that level,
    last four kept, straight out of the engine's own learnset. Nothing is
    hand-picked to make a fight winnable.
  * ONE COUNTER PER ROOM, and never in slot 1. Each party carries a
    Pokemon that is super effective against that gym, sitting on the
    bench: Mankey's KARATE_CHOP for Brock's rock, Pikachu for Misty,
    Diglett — which electricity cannot touch at all — for Surge,
    Beedrill's TWINEEDLE for Erika and again for Sabrina's psychics,
    Kadabra for Koga's poison, Poliwhirl's WATER_GUN for Blaine and for
    Giovanni's ground. A gym's type is pamphlet tier: its guide says it
    out loud in every gym in the game (user, 2026-09-15). Without one of
    these on the bench there is nothing for a lead rule or a switch rule
    to be RIGHT about, and the arena measures only whether the starter
    can grind the room down. With one, leading correctly is worth
    something and leading with the chewed-up starter costs.
    The starter line is FIRE all game and is never the answer: bad into
    Misty, resisted by Blaine, merely adequate elsewhere.
  * The bag holds what that stage of the game SELLS, and where it can, it
    holds MORE THAN ONE TIER of it. A bag with a single kind of potion
    cannot tell `best_available` from `weakest_sufficient`, so the
    preference ladder in the policy DSL goes untested. Mixed tiers begin
    at Vermilion, which is where SUPER_POTION first appears on a shelf;
    Pewter and Cerulean are single-tier because that is the truth about
    those shops.
  * Badges come from the base save, so each arena is ginned on top of a
    checkpoint from the right era and carries the stat boosts a run
    would have had.

FOUR GYMS ARE PUZZLE ROOMS: Vermilion's trash-can locks, Saffron's
teleport pads, Cinnabar's quiz doors, Viridian's spin tiles. A BATTLE
policy is not a navigation policy, and teaching the arena driver four
puzzles would measure the wrong thing, so those four are parked in front
of the leader with the rest of the room already beaten. What they score is
one hard fight, which is what they are for.

  gin_gym_arenas.py --list        what would be built, and from what
  gin_gym_arenas.py               write the specs and gin the saves
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GEN = Path.home() / "Developer/gen1recomp/data/generated"
BADGE_NAMES = ("BOULDERBADGE", "CASCADEBADGE", "THUNDERBADGE", "RAINBOWBADGE",
               "SOULBADGE", "MARSHBADGE", "VOLCANOBADGE", "EARTHBADGE")


# ------------------------------------------------------- the engine's word
def _block(src: str, name: str) -> str:
    m = re.search(r"\n  " + re.escape(name) + r" = \{", src)
    if not m:
        return ""
    i, depth = m.end() - 1, 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
    return ""


def natural_moves(species: str, level: int) -> list:
    """What this Pokemon knows at this level, having learned nothing else.
    Level-1 moves plus every learnset entry at or below the level, last
    four kept — the same four the game would leave it holding."""
    b = _block((GEN / "pokemon.lua").read_text(errors="ignore"), species)
    got = re.findall(r'"([A-Z_0-9]+)"',
                     (re.search(r"level1Moves = \{(.*?)\}", b, re.S)
                      or re.match("", "")).group(1) if b else "")
    ls = re.search(r"learnset = \{(.*?)\n    \},", b, re.S)
    for m in re.finditer(r"\{\s*level = (\d+),\s*move = \"([A-Z_0-9]+)\",\s*\}",
                         ls.group(1) if ls else ""):
        if int(m.group(1)) <= level and m.group(2) not in got:
            got.append(m.group(2))
    return got[-4:]


def can_learn(species: str, move: str) -> bool:
    b = _block((GEN / "pokemon.lua").read_text(errors="ignore"), species)
    tm = re.search(r"tmhm = \{(.*?)\}", b, re.S)
    return bool(tm and f'"{move}"' in tm.group(1))


def room_objects(map_id: str) -> list:
    """[(index, name, x, y)] for one map, from the engine's map table."""
    b = _block((GEN / "maps.lua").read_text(errors="ignore"), map_id)
    o = re.search(r"objects = \{", b)
    if not o:
        return []
    i, depth = o.end() - 1, 0
    for j in range(i, len(b)):
        if b[j] == "{":
            depth += 1
        elif b[j] == "}":
            depth -= 1
            if depth == 0:
                break
    out = []
    for e in re.finditer(r"\{(.*?)\}", b[i:j + 1], re.S):
        body = e.group(1)
        nm = re.search(r'name = "([A-Z0-9_]+)"', body)
        ix = re.search(r"\bindex = (\d+)", body)
        x = re.search(r"\bx = (\d+)", body)
        y = re.search(r"\by = (\d+)", body)
        if nm and ix and x and y:
            out.append((int(ix.group(1)), nm.group(1),
                        int(x.group(1)), int(y.group(1))))
    return out


def trainer_flags(map_id: str) -> list:
    out = []
    for line in (REPO / "planner/engine_trainer_events.txt").read_text().splitlines():
        f, _, m = line.partition("\t")
        if m.strip() == map_id:
            out.append(f.strip())
    return sorted(out)


def badges_of(save: Path) -> list:
    try:
        s = save.read_text(errors="ignore")
    except OSError:
        return []
    return [b for b in BADGE_NAMES if re.search(rf"\b{b} = ", s)]


_BASES: dict = {}


def pick_base(want_badges: int) -> Path | None:
    """A checkpoint carrying exactly this many badges.

    BADGES COME FROM THE BASE, because gin_save keeps them and a spec
    cannot take one away. Picking by leg number got this wrong three times
    out of eight — leg 9 is before Misty, not after her — so the count
    itself is the key, and the EARLIEST leg holding it is the one taken:
    that is the save from just after the badge was won, before the run
    wandered off and levelled."""
    if not _BASES:
        for d in sorted((REPO / "run/saves").iterdir()):
            f = d / "slot1.lua"
            if d.is_dir() and f.exists():
                _BASES.setdefault(len(badges_of(f)), []).append(f)
    got = _BASES.get(want_badges) or []
    return got[0] if got else None


# ---------------------------------------------------------- the eight gyms
# level: the leader's ace, for reference when reading the party beside it.
GYMS = [
    dict(name="pewter", map="PEWTER_GYM", leader="BROCK", ace=14,
         badges=0, door=(4, 13), puzzle=False, money=1500,
         party=[("CHARMANDER", 12), ("NIDORAN_M", 11), ("PIDGEY", 10),
                ("MANKEY", 15)],
         bag={"POTION": 5, "ANTIDOTE": 1},
         note="Charmander's Ember is halved by ONIX's rock and its "
              "defence is the wall it is; four Potions and a Nidoran's "
              "HORN_ATTACK is the whole of the answer."),
    dict(name="cerulean", map="CERULEAN_GYM", leader="MISTY", ace=21,
         badges=1, door=(4, 13), puzzle=False, money=2800,
         party=[("CHARMELEON", 18), ("NIDORINO", 17), ("PIDGEOTTO", 16),
                ("PIKACHU", 17)],
         bag={"POTION": 8, "ANTIDOTE": 2, "PARLYZ_HEAL": 1},
         note="Fire into water, and STARMIE outspeeds all three. Single "
              "tier on purpose: POTION is the only heal a Cerulean-era "
              "shelf sells."),
    dict(name="vermilion", map="VERMILION_GYM", leader="LT_SURGE", ace=24,
         badges=2, door=(5, 2), puzzle=True, money=4200,
         party=[("CHARMELEON", 23), ("NIDORINO", 21), ("PIDGEOTTO", 20),
                ("DIGLETT", 20)],
         bag={"POTION": 5, "SUPER_POTION": 3, "PARLYZ_HEAL": 3,
              "ANTIDOTE": 1},
         note="The first mixed-tier bag, because Vermilion is where "
              "SUPER_POTION appears. RAICHU paralyses, so the cure class "
              "has something to do."),
    dict(name="celadon", map="CELADON_GYM", leader="ERIKA", ace=29,
         badges=3, door=(4, 17), puzzle=False, money=6000,
         party=[("CHARMELEON", 28), ("NIDORINO", 27), ("FARFETCHD", 24),
                ("EEVEE", 22),
                ("BEEDRILL", 25)],
         bag={"POTION": 4, "SUPER_POTION": 4, "ANTIDOTE": 2,
              "PARLYZ_HEAL": 2, "REVIVE": 1},
         note="Farfetch'd carries CUT because Erika and her last three "
              "trainers sit inside a bed with two bushes in it. "
              "VILEPLUME's SLEEP_POWDER is the attrition."),
    dict(name="fuchsia", map="FUCHSIA_GYM", leader="KOGA", ace=43,
         badges=4, door=(4, 17), puzzle=False, money=9000,
         party=[("CHARIZARD", 38), ("NIDORINO", 34), ("FARFETCHD", 30),
                ("EEVEE", 28),
                ("KADABRA", 34)],
         bag={"POTION": 3, "SUPER_POTION": 5, "FULL_HEAL": 2, "REVIVE": 2,
              "ANTIDOTE": 2},
         note="Two members badly under level and a room that poisons: "
              "bodies run out before HP does, which is what the revive "
              "rule is for."),
    dict(name="saffron", map="SAFFRON_GYM", leader="SABRINA", ace=43,
         badges=5, door=(9, 9), puzzle=True, money=11000,
         party=[("CHARIZARD", 41), ("NIDOKING", 38), ("FARFETCHD", 32),
                ("EEVEE", 30),
                ("BEEDRILL", 36)],
         bag={"SUPER_POTION": 4, "HYPER_POTION": 3, "FULL_HEAL": 2,
              "REVIVE": 2},
         note="ALAKAZAM against a poison type is the worst matchup in the "
              "list, and three heal tiers to choose between."),
    dict(name="cinnabar", map="CINNABAR_GYM", leader="BLAINE", ace=47,
         badges=6, door=(3, 4), puzzle=True, money=13000,
         party=[("CHARIZARD", 44), ("NIDOKING", 42), ("EEVEE", 34),
                ("FARFETCHD", 34),
                ("POLIWHIRL", 40)],
         bag={"SUPER_POTION": 3, "HYPER_POTION": 4, "FULL_HEAL": 2,
              "REVIVE": 2},
         note="Fire into fire: Charizard resists what ARCANINE throws and "
              "cannot burn it down either, so nobody sweeps."),
    dict(name="viridian", map="VIRIDIAN_GYM", leader="VIRIDIAN_GYM_GIOVANNI",
         ace=50, badges=7, door=(2, 2), puzzle=True, money=15000,
         party=[("CHARIZARD", 48), ("NIDOKING", 45), ("EEVEE", 38),
                ("FARFETCHD", 36),
                ("POLIWHIRL", 44)],
         bag={"SUPER_POTION": 2, "HYPER_POTION": 5, "FULL_HEAL": 3,
              "REVIVE": 2},
         note="RHYDON L50 hits a Charizard four times over with rock. The "
              "last gym, and the last arena before the league."),
]


def build(g: dict) -> dict:
    objs = room_objects(g["map"])
    leader_obj = next((i for i, n, _x, _y in objs
                       if g["leader"].replace("_", "") in n.replace("_", "")
                       or n.endswith(g["leader"])), None)
    lead_flag = "EVENT_BEAT_" + g["leader"]
    others = trainer_flags(g["map"])
    party = []
    for sp, lv in g["party"]:
        mv = natural_moves(sp, lv)
        if sp == "FARFETCHD" and can_learn(sp, "CUT"):
            mv = (mv[:3] + ["CUT"]) if "CUT" not in mv else mv
        party.append({"species": sp, "level": lv, "moves": mv,
                      "nickname": sp})
    # FACING MATTERS BECAUSE BOOTSTRAP MASHES A. A save resumes exactly
    # where it was written and bootstrap opens with six A presses to clear
    # the title ceremony; parked in front of a leader FACING HIM, those
    # presses talk to him and the fight starts during setup, which came
    # back as "bootstrap failed (stuck in mode=battle)" on all four puzzle
    # arenas. Gym leaders have no line of sight — they fight only when
    # interacted with (user, 2026-09-15) — so facing away is enough, and
    # the driver turns round and presses them itself.
    facing = "down" if g["puzzle"] else "up"
    spec = {"party": party, "bag": dict(g["bag"]), "money": g["money"],
            "start": {"map": g["map"], "x": g["door"][0], "y": g["door"][1],
                      "facing": facing}}
    if g["puzzle"]:
        # THE FIGHT, NOT THE MAZE. Parked in front of the leader with the
        # rest of the room already beaten, so the score is the one fight
        # and never the navigation.
        spec["clear_flags"] = [lead_flag]
        spec["set_flags"] = others
        spec["set_trainers"] = [f"{g['map']}_obj_{i}" for i, n, _x, _y in objs
                                if i != leader_obj]
    else:
        spec["clear_flags"] = [lead_flag] + others
        spec["clear_trainers"] = [f"{g['map']}_obj_{i}"
                                  for i, _n, _x, _y in objs]
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="say what would be built and stop")
    ap.add_argument("--only", default="", help="one arena by name")
    a = ap.parse_args()
    rc = 0
    for g in GYMS:
        if a.only and g["name"] != a.only:
            continue
        base = pick_base(g["badges"])
        spec = build(g)
        n_beat = len(spec.get("clear_flags") or [])
        print(f"\n=== {g['name']}  {g['map']}  "
              f"{'ONE FIGHT (puzzle room)' if g['puzzle'] else str(n_beat) + ' to beat'}"
              f"  leader's ace L{g['ace']}")
        print(f"    base {base.parent.name if base else 'MISSING'} "
              f"({len(badges_of(base)) if base else 0} badge(s))")
        for m in spec["party"]:
            print(f"    {m['species']:11s} L{m['level']:<3d} "
                  + "/".join(m["moves"]))
        print("    bag " + ", ".join(f"{k} x{v}"
                                     for k, v in spec["bag"].items()))
        print(f"    {g['note']}")
        if a.list:
            continue
        if not base:
            print(f"    SKIPPED: no base save with {g['badges']} badge(s)")
            rc = 1
            continue
        sp = REPO / f"plans/arena_{g['name']}.json"
        sp.write_text(json.dumps(spec, indent=2))
        out = REPO / f"run/arena_{g['name']}.lua"
        r = subprocess.run([sys.executable, str(REPO / "planner/gin_save.py"),
                            "--base", str(base), "--spec", str(sp),
                            "--out", str(out)],
                           capture_output=True, text=True)
        print("    " + (r.stdout.strip().replace("\n", "\n    ")
                        or r.stderr.strip()[:300]))
        rc = rc or r.returncode
    return rc


if __name__ == "__main__":
    sys.exit(main())

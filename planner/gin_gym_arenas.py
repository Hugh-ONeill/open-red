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
  * THREE POKEMON, AND UNDER THE LEADER. With four or five bodies and a
    lead level with the ace, eight of the nine arenas were swept by every
    candidate once the policies could lead and switch by type — the
    capability worked and the measurement stopped (2026-09-15, user: "we
    have to ensure each fight is still challenging, so we should either
    have less mons or lower levels until it essentially forces usage of
    items to not die"). Three is the smallest party that still holds a
    starter, a counter and one spare, and the lead sits three to five
    levels under the leader's ace. The calibration target is exact: a
    spec that can reach its medicine should take the room, and the SAME
    spec with its item rules stripped should not, and
    planner/calibrate_arenas.py asks exactly that, a verdict a room.
    FIRST MEASUREMENT, 2026-09-15: three right, three too hard, two too
    easy. The too-hard three were not short of BODIES, they were short of
    MEDICINE — Celadon carried 280 HP of healing across EIGHT fights with
    three Pokemon of 70-odd HP, about 35 a fight, when one Victreebel
    exchange costs more than that (user: "yeah do the medicine, keep them
    at 3"). So their bags roughly double and move a tier up, and the
    parties stay at three, which keeps the healing rather than the spare
    bodies as the thing that carries a room. The too-easy two come DOWN
    in level instead. Viridian is untouched and is the proof that room
    length is not the lever: one fight, and RHYDON L50 against a L45
    CHARIZARD bites where SABRINA L43 against a L39 does not.
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


_MOVE_POWER: dict = {}


def move_power(move: str) -> int:
    """The move's power off the engine's table; 0 for anything that does
    no damage. Read once per move."""
    if move not in _MOVE_POWER:
        b = _block((GEN / "moves.lua").read_text(errors="ignore"), move)
        m = re.search(r"\bpower = (\d+)", b) if b else None
        _MOVE_POWER[move] = int(m.group(1)) if m else 0
    return _MOVE_POWER[move]


HMS = ("CUT", "FLY", "SURF", "STRENGTH", "FLASH")


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


# ---------------------------------------------------------- the nine rooms
# level: the leader's ace, for reference when reading the party beside it.
#
# TWO PATHS THROUGH EVERY ROOM (user, 2026-09-15: "split it up into two
# paths like the elite four split, a realistic path with a team we build
# up from scratch and maintain that mirrors what weve already gotten in
# real games, and an ideal path where we actually have an ideal but
# underleveled team that has answers but needs items, then we can get two
# seperate comparisons ultimately and see if stuff performs better in one
# than the other"). The room is shared — map, door, leader, flags, route —
# and each path brings its own party, bag and money.
#
# THE REAL PATH IS THE RECORD, WORKSHOPPED. Its parties are read out of
# the journals of the two Hall of Fame runs that played on outlines the
# model wrote itself (executor_log.065231, Aug 28, and .061446, Sep 6):
# which species led each leader fight and what every species had last
# been seen at when the fight started. The two runs converged on the same
# core without consulting each other — Charmander's line, an ODDISH kept
# as GLOOM, a PIDGEOT, a DUGTRIO, one water, one wildcard — and led with
# the starter only until Surge. The levels sit AT the ace, not over it.
# Then the user's calls (2026-09-15): the Aug 28 run's JIGGLYPUFF is out
# ("i dont even remember a jigglypuff ever being caught its not in any
# of the plans"), the wildcard is the Dojo's HITMONLEE rather than the
# Aug 28 KABUTO, the water is a GYARADOS because "lapras is a rare get we
# skip it more often then not", and the GLOOM evolves once a Leaf Stone
# is on a shelf, which is Celadon, because the harness now presents
# stones properly. That is the Sep 6 run's roster with the stone, and
# from Vermilion on the rooms are what that run walked in with. The two
# early rooms hold a starter and a bird, then starter, ODDISH and bird
# ("i know i said too many earlier but now theres too little"). Slot
# order is the order the run led in.
#
# TMs ARE FAIR GAME, IF THE RUN HAD THEM BY THEN. The badge TM from every
# leader already beaten, plus the free ones on the route the runs are on
# record picking up (plans/outline.done: WATER_GUN and MEGA_PUNCH in Mt
# Moon, THUNDER_WAVE on Route 24, DIG in Cerulean, BODY_SLAM on the S.S.
# Anne, EARTHQUAKE in Silph Co). Shop TMs (ICE_BEAM off Celadon's shelf)
# on the ideal path only, from Celadon on. One or two a member, replacing
# a move that does no damage first, then the weakest attack that is not
# the room's HM. FIRE_BLAST stays off the real CHARIZARD: under the rule
# it would sit beside FLAMETHROWER, and the user was wary of it.
#
# THE REAL BAG IS THE HANDFUL A RUN HAS BEEN SEEN TO BUY. Every save on
# file walked into Koga, Sabrina, Blaine and Giovanni with NO medicine at
# all and $12k-$85k unspent; the counter question (executor._ask_buy,
# 2026-09-14) now buys, and what it has bought is five POTIONs at
# Cerulean with the bag empty. Run 17 walked into Lt. Surge with
# POTIONx3 + SUPER_POTIONx5 and into Erika with SUPER_POTIONx3 — those
# two rooms carry exactly that, on record. Elsewhere: five of the potion
# the last town's mart sells, no cures, no revives, because none has ever
# been in a run's bag. The point of the path is whether the policy turns
# THAT into fewer blackouts than the run had, which is what started this
# work: three SUPER_POTIONs in the bag, a CHARIZARD blacking out to Erika
# (07:18, 2026-09-15, the rule naming an item the bag did not hold).
#
# ...AND THE STARTER IS BULBASAUR'S LINE NOW (user, 2026-09-21: "revamp
# with pref bulba for ideal and def bulba for realistic"). Both paths were
# built around CHARMANDER because the runs on record carried one and the
# ideal path preferred its line. The starter question was decided by which
# ball was listed first until 2026-09-21, and BULBASAUR won 1 draw in 3 by
# the shuffle; asked to say what each ball answers before it names one, it
# takes BULBASAUR or SQUIRTLE 40 times out of 40. So the party a run brings
# to these rooms has changed, and the rooms had not. WHICH ROOMS ARE HARD
# MOVES WITH IT: CHARMANDER could not answer Brock or Misty, and those two
# borrowed a starter; BULBASAUR answers both and is answered itself by
# Sabrina and Blaine, where the borrowed answer now stands. Every level is
# the level the room was calibrated at — only the species moved — so the
# calibration has to be taken again (calibrate_arenas.py), and where a room
# comes back too easy it is the level or the bodies that want changing.
#
# THE IDEAL PATH HAS AS MANY BODIES AS THE LEADER, at a reasonable level
# — five under the ace — so that nothing but the medicine and the play
# decides it (user, 2026-09-15: "ideal should use the least amount of
# pokemon viable while still being at reasonable levels, medicine usage
# and good play is the descriminator"; then "for ideal i think it makes
# sense to have as many mons as the gym leader has, in the case of the
# elite four well stay with the six"). One starter per team, Charmander's
# line by preference, SQUIRTLE at Brock and IVYSAUR at Misty because
# those are the rooms a Charmander cannot answer; the starter and the
# one answer the room calls for, and bodies to the leader's count that
# are bodies, not second answers. The league's ideal party
# (plans/arena_e4_ideal.json, a hand file the user set to six at L50) is
# not rebuilt here.
#
# Older history, still true of the rooms: NONE OF THE FILLER MAY RESIST
# THE ROOM (a GRAVELER took Koga's poison at a quarter, a CHARIZARD
# resisted all of Blaine, PIDGEOT and GOLBAT were both immune to
# Giovanni's ground — and each room went to zero blackouts in both arms).
# The real path carries whatever the run carried, resistances and all,
# because that is the record; the ideal path chooses.
_LEAGUE_CLEAR_FLAGS = [
    "EVENT_BEAT_LORELEIS_ROOM_TRAINER_0", "EVENT_BEAT_BRUNOS_ROOM_TRAINER_0",
    "EVENT_BEAT_AGATHAS_ROOM_TRAINER_0", "EVENT_BEAT_LANCE",
    "EVENT_BEAT_CHAMPION_RIVAL", "EVENT_BEAT_LORELEI", "EVENT_BEAT_BRUNO",
    "EVENT_BEAT_AGATHA", "EVENT_BEAT_CHAMPION_RIVAL_THIS_RUN",
    "EVENT_LANCES_ROOM_LOCK_DOOR", "EVENT_AUTOWALKED_INTO_LORELEIS_ROOM",
    "EVENT_AUTOWALKED_INTO_BRUNOS_ROOM", "EVENT_AUTOWALKED_INTO_AGATHAS_ROOM",
    "EVENT_BEAT_LANCES_ROOM_TRAINER_0", "EVENT_STARTED_ELITE_4"]
_LEAGUE_CLEAR_TRAINERS = [
    "AGATHAS_ROOM_obj_1", "AGATHAS_ROOM_obj_2", "BRUNOS_ROOM_obj_1",
    "BRUNOS_ROOM_obj_2", "CHAMPIONS_ROOM_obj_1", "CHAMPIONS_ROOM_obj_2",
    "LANCES_ROOM_obj_1", "LANCES_ROOM_obj_2", "LORELEIS_ROOM_obj_1",
    "LORELEIS_ROOM_obj_2"]

# THE REAL PATH IS THE LAST REAL RUN (user, 2026-10-01: "should we alter the
# real roster to the last real roster?" — yes). plans/arena_real_doors.json
# holds run 19's state at each room's door, read from its own checkpoints:
# the party with the moves it had really learned and forgotten, the badges
# it held (each a stat boost in every fight), the whole bag and the money.
# A door is the last checkpoint before the run first STOOD in the room — its
# first crossing into it, or its first fight there — not its first attempt:
# Viridian's gym is locked below seven badges and run 19 "attempted"
# Giovanni at that door before beating Blaine (user: "viridian should have
# the volcano badge"), and its first two league attempts never reached
# Lorelei.
# Run 27's hand entries, which these replace, are in git history (32bd271).
_DOORS = json.loads((REPO / "plans/arena_real_doors.json").read_text())


def _door(room: str, note: str = "") -> dict:
    d = _DOORS[room]
    return dict(party=[dict(species=m["species"], level=m["level"], moves=m["moves"])
                       for m in d["party"]],
                bag=dict(d["bag"]), money=d["money"], badges=list(d.get("badges") or []),
                note=note or (f"Run 19 at the door: checkpoint {d['checkpoint']} "
                              f"(its last save before it first stood in this room, "
                              f"on {d['map']})."))


# THE IDEAL ROOMS ARE SET WHERE MEDICINE DECIDES THEM (2026-10-01; user: "part
# of what ideal is supposed to test is that proper item usage can carry an
# underleveled but well built team to victory"). tools/calibrate_ideal.py
# shifted each party's levels and scored a generic medicine reference
# against the same tactics bare (run/cal/results.jsonl); `shift` is the
# setting where the medicine arm wins and the bare one mostly does not:
# Pewter +2 (100%/25%), Cerulean -8 (67%/33%, a POTION-only bag), Vermilion
# -2 (100%/50%), Celadon -10 (88%/38%), Fuchsia -8 (86%/29%), Saffron -6
# (100%/80%). Cinnabar and Viridian stay as they were: a type-ideal party
# stomps those leaders at any level (user: "ideal is supposed to be ideal
# it just means that it should almost always stomp gio which it always
# has"), and the league's hand file moved -6 (90%/40%).
GYMS = [
    dict(name="pewter", map="PEWTER_GYM", leader="BROCK", ace=14,
         badges=0, door=(4, 13), puzzle=False,
         paths=dict(
             real=_door("pewter"),
             # THREE UNDER, MEASURED FROM BOTH SIDES. At 10 the room was
             # calibrated under v12 and lost under v13 with the bag full:
             # a 20-power BUBBLE against ONIX is a long fight, and a solo
             # cannot afford a spec that heals two a fight where another
             # heals three (user, 2026-09-15: "those two might need higher
             # leveled mons"). At 12 it was 8/8 in BOTH arms for BOTH
             # specs, and so was 11: the bag mattered at 10 and nowhere
             # above it, because BUBBLE and ONIX's chip are both slow. So
             # ten, the one level that separated v12 from v13 on their
             # per-fight caps (user, 2026-09-15: "put squirt back to 10").
             ideal=dict(shift=2, party=[("BULBASAUR", 10), ("NIDORAN_M", 10)],
                        bag={"POTION": 8}, money=2000,
                        note="SQUIRTLE's BUBBLE is the answer, four under "
                             "the ace, and alone: the starter IS the "
                             "answer here, so nothing else is needed "
                             "(user, 2026-09-15: \"if squirt for brock we "
                             "dont need mankey\")."))),
    dict(name="cerulean", map="CERULEAN_GYM", leader="MISTY", ace=21,
         badges=1, door=(4, 13), puzzle=False,
         paths=dict(
             real=_door("cerulean"),
             # FIVE UNDER WAS NOT REASONABLE ALONE. At 16 the room wiped
             # both arms, ten POTIONs and all: 4/6 with medicine, 4/6
             # without, STARMIE taking it every trial (2026-09-15). A
             # solo has no one to hand the turn to, so it needs to live
             # through a hit on its own; three under is the level.
             # ...AND HERE THE LEVEL STAYS. At 18 v12 took it 12/12 with
             # medicine and 9/12 with three blackouts without, which is
             # the calibration exactly; v13 lost every trial on its two-a-
             # fight cap, which is v13's to answer for. At 19 both specs
             # swept both arms. Eighteen, three under.
             ideal=dict(shift=-8, party=[("IVYSAUR", 18), ("PIDGEOTTO", 18)],
                        bag={"POTION": 10}, money=3000,
                        note="IVYSAUR resists water and VINE_WHIP hits it "
                             "double; alone, like the SQUIRTLE at Brock: "
                             "the starter is the answer and no PIKACHU "
                             "beside it (user, 2026-09-15). Three under "
                             "the ace: five under wiped it with the bag "
                             "full, two under is a free pass."))),
    # NOT A PUZZLE ROOM AFTER ALL. Surge's trash-can locks are two
    # FLAGS (EVENT_1ST_LOCK_OPENED / EVENT_2ND_LOCK_OPENED, and the
    # second is what swaps the door block), so setting them opens the
    # gym and the whole room is crossable from its door. The two gym
    # trainers are ELECTRIC, so fighting them is how the room tells the
    # lead rule what it is made of before Surge.
    dict(name="vermilion", map="VERMILION_GYM", leader="LT_SURGE", ace=24,
         badges=2, door=(4, 17), puzzle=False,
         open_flags=["EVENT_1ST_LOCK_OPENED", "EVENT_2ND_LOCK_OPENED"],
         paths=dict(
             real=_door("vermilion"),
             ideal=dict(shift=-2, party=[("DIGLETT", 19),
                               ("IVYSAUR", 20, ["BODY_SLAM"]),
                               ("PIDGEOTTO", 19)],
                        bag={"POTION": 5, "SUPER_POTION": 6,
                             "PARLYZ_HEAL": 3}, money=5000,
                        note="DIGLETT with DIG, which electricity cannot "
                             "touch, and the starter; VOLTORB's SONICBOOM "
                             "and RAICHU's paralysis are what the bag is "
                             "for."))),
    dict(name="celadon", map="CELADON_GYM", leader="ERIKA", ace=29,
         badges=3, needs_cut=True, door=(4, 17), puzzle=False,
         paths=dict(
             real=_door("celadon"),
             ideal=dict(shift=-10, party=[("FEAROW", 24),
                               ("IVYSAUR", 25, ["BODY_SLAM"]),
                               ("KADABRA", 25)],
                        hms=["FLY"],
                        bag={"SUPER_POTION": 8, "FULL_HEAL": 3,
                             "REVIVE": 2}, money=12000,
                        note="FEAROW with FLY off Route 16 is the flyer a "
                             "gen 1 route has for grass, and the starter "
                             "burns it and carries CUT. FULL_HEAL for "
                             "SLEEP_POWDER. Eight fights on two bodies."))),
    dict(name="fuchsia", map="FUCHSIA_GYM", leader="KOGA", ace=43,
         badges=4, door=(4, 17), puzzle=False,
         paths=dict(
             real=_door("fuchsia"),
             ideal=dict(shift=-8, party=[("KADABRA", 38),
                               ("VENUSAUR", 38, ["BODY_SLAM"]),
                               ("DUGTRIO", 38), ("FEAROW", 37, ["FLY"])],
                        bag={"SUPER_POTION": 10, "ANTIDOTE": 4,
                             "FULL_HEAL": 2, "REVIVE": 3}, money=20000,
                        note="Psychic into poison, five under the ace, "
                             "and the starter; Fuchsia's shelf tops out "
                             "at SUPER_POTION."))),
    dict(name="saffron", map="SAFFRON_GYM", leader="SABRINA", ace=43,
         # THE PADS DECIDE WHO YOU MEET. From the door, the prescribed
         # route (policy_author.APPROACH) crosses four chambers and their
         # trainers before her. Everyone is reset so they all fight; only
         # SABRINA is scored, because the route meets four of the seven.
         badges=5, door=(8, 17), puzzle=False,
         score_only=["EVENT_BEAT_SABRINA"], fights=5,
         paths=dict(
             real=_door("saffron"),
             ideal=dict(shift=-6, party=[("SNORLAX", 38, ["EARTHQUAKE"]),
                               ("VENUSAUR", 38, ["BODY_SLAM"]),
                               ("DUGTRIO", 38, ["EARTHQUAKE"]),
                               ("KADABRA", 38)],
                        bag={"HYPER_POTION": 8, "FULL_HEAL": 3,
                             "REVIVE": 3}, money=30000,
                        note="Nothing is super effective on a gen 1 "
                             "psychic that anyone carries, so the answer "
                             "is bulk and physical power: SNORLAX's "
                             "BODY_SLAM, with the starter beside it."))),
    # THE GATES STAY SHUT. A guardian only fights you if you answer his
    # quiz WRONG; the route answers each one wrong, which fights all six
    # and opens the gates the way playing it does. Only BLAINE's flag
    # scores (no numbered trainer events here), but the wearing down on
    # the way to him is the point.
    dict(name="cinnabar", map="CINNABAR_GYM", hms=["SURF"], leader="BLAINE",
         ace=47, badges=6, door=(16, 17), puzzle=False,
         paths=dict(
             real=_door("cinnabar"),
             ideal=dict(party=[("STARMIE", 42, ["BUBBLEBEAM", "THUNDERBOLT", "ICE_BEAM"]),
                               ("VENUSAUR", 42, ["BODY_SLAM"]),
                               ("DUGTRIO", 42),
                               ("SNORLAX", 42, ["EARTHQUAKE"])],
                        bag={"HYPER_POTION": 8, "BURN_HEAL": 3,
                             "REVIVE": 3}, money=40000,
                        note="STARMIE off the Super Rod with SURF, and "
                             "the starter, which resists the whole room: "
                             "an ideal pair at Blaine may read easy, and "
                             "the table will say so if it does."))),
    # THE FLAG THE FIGHT ACTUALLY SETS. This port sets EVENT_BEAT_GIOVANNI
    # on winning the gym battle (data/scripts/gyms.lua), not
    # EVENT_BEAT_VIRIDIAN_GYM_GIOVANNI. From the door the room holds eight
    # trainers and him; the floor is spin tiles, which the shim settles.
    dict(name="viridian", map="VIRIDIAN_GYM", hms=["SURF"], leader="GIOVANNI",
         ace=50, badges=7, door=(16, 17), puzzle=False,
         paths=dict(
             real=_door("viridian"),
             ideal=dict(party=[("STARMIE", 45, ["BUBBLEBEAM", "THUNDERBOLT", "ICE_BEAM"]),
                               ("VENUSAUR", 45, ["BODY_SLAM"]),
                               ("LAPRAS", 45), ("KADABRA", 45),
                               ("SNORLAX", 45, ["EARTHQUAKE"])],
                        bag={"HYPER_POTION": 8, "FULL_HEAL": 3,
                             "REVIVE": 3}, money=50000,
                        note="SURF into ground, quadruple on RHYDON, five "
                             "under the ace, and the starter; nine fights "
                             "on two bodies."))),
    # THE LEAGUE. Not a gym: no room objects to clear by name and no base
    # picked by badges — it is ginned on top of run/arena_e4.lua, the
    # savepoint parked at LORELEI's door, with the same flags and trainers
    # cleared that plans/arena_e4_ideal.json clears. Only the real path is
    # built here; e4_ideal is the user's hand file.
    dict(name="e4", map="LORELEIS_ROOM", leader="LORELEI", ace=62,
         league=True, base=REPO / "run/arena_e4.lua", door=(4, 11),
         puzzle=False, hms=["SURF"],
         paths=dict(
             real=_door("e4"),
             # THE LEAGUE AT ITS EDGE (2026-10-01). Run 19 as it walked in
             # loses to levels whatever the policy: every spec, the plain
             # baseline included, cleared 10-14 rooms of 30. After seven laps
             # (12:27) it reached the Champion on each of its next four and
             # lost there, then won from 13:14 a few levels on; a room parked
             # at that edge is decided by how it fights, which is what a
             # policy is scored on.
             late=_door("e4_late", note="Run 19 after seven lost laps of the "
                       "league: checkpoint leg_52_..20260930-122755 (it reached the "
                       "Champion on each of its next four laps and won from 13:14)"))),
]


def build(g: dict, path: str) -> dict:
    p = g["paths"][path]
    party = []
    for entry in p["party"]:
        if isinstance(entry, dict):
            # A RECORDED MEMBER CARRIES ITS OWN MOVES: what the run taught it
            # and what it chose to forget are the record, not a level table
            party.append({"species": entry["species"], "level": entry["level"],
                          "moves": list(entry["moves"]), "nickname": entry["species"],
                          "_tms": []})
            continue
        # the shift moves the LEVEL only: the build (its moves) stays the
        # one the room was designed and calibrated with
        sp, lv = entry[0], entry[1] + int(p.get("shift") or 0)
        party.append({"species": sp, "level": lv,
                      "moves": natural_moves(sp, entry[1]), "nickname": sp,
                      "_tms": list(entry[2]) if len(entry) > 2 else []})
    # A ROOM WITH A BUSH IN IT NEEDS SOMEBODY WHO CAN CUT (Celadon pens
    # Erika and her last three trainers inside a bed with two CUT_TREEs;
    # without a carrier the room capped at four of eight every trial with
    # no blackouts and no difference between full medicine and none,
    # 2026-09-15). AND A ROOM YOU CANNOT REACH WITHOUT AN HM IS A ROOM
    # WHOSE PARTY HAS IT: nobody stands in Cinnabar's gym without SURF,
    # and the same party still carries it at Viridian. The first member
    # in slot order who can learn it carries it, in its last slot.
    for hm in ((["CUT"] if g.get("needs_cut") else [])
               + list(g.get("hms") or []) + list(p.get("hms") or [])):
        if any(hm in m["moves"] for m in party):
            continue
        for m in party:
            if can_learn(m["species"], hm):
                m["moves"] = m["moves"][:3] + [hm]
                break
        else:
            sys.exit(f"{g['name']}_{path}: nobody in this party can learn {hm}")
    # THEN THE TMs THE RUN HAD BY THEN (see the rule above): a move that
    # does no damage goes first, then the weakest attack that is not the
    # room's HM; a member still short of four moves just gains it.
    for m in party:
        for tm in m.pop("_tms"):
            if tm in m["moves"]:
                continue
            if not can_learn(m["species"], tm):
                sys.exit(f"{g['name']}_{path}: {m['species']} cannot learn {tm}")
            if len(m["moves"]) < 4:
                m["moves"].append(tm)
                continue
            idx = next((i for i, mv in enumerate(m["moves"])
                        if move_power(mv) == 0 and mv not in HMS), None)
            if idx is None:
                cands = [(move_power(mv), i) for i, mv in enumerate(m["moves"])
                         if mv not in HMS]
                if not cands:
                    sys.exit(f"{g['name']}_{path}: no slot for {tm} on {m['species']}")
                idx = min(cands)[1]
            m["moves"][idx] = tm
    # FACING MATTERS BECAUSE BOOTSTRAP MASHES A: parked facing a leader,
    # the title-clearing presses talk to him and the fight starts during
    # setup. Leaders fight only when interacted with, so facing away is
    # enough, and the driver turns round and presses them itself.
    facing = "down" if g["puzzle"] else "up"
    spec = {"party": party, "bag": dict(p["bag"]), "money": p["money"],
            **({"badges": list(p["badges"]), "bag_exact": True}
               if p.get("badges") is not None else {}),
            "start": {"map": g["map"], "x": g["door"][0], "y": g["door"][1],
                      "facing": facing}}
    if g.get("league"):
        spec["clear_flags"] = list(_LEAGUE_CLEAR_FLAGS)
        spec["clear_trainers"] = list(_LEAGUE_CLEAR_TRAINERS)
        return spec
    objs = room_objects(g["map"])
    leader_obj = next((i for i, n, _x, _y in objs
                       if g["leader"].replace("_", "") in n.replace("_", "")
                       or n.endswith(g["leader"])), None)
    lead_flag = "EVENT_BEAT_" + g["leader"]
    others = trainer_flags(g["map"])
    extra = list(g.get("also_clear") or [])
    if g["puzzle"]:
        # THE FIGHT, NOT THE MAZE: parked in front of the leader with the
        # rest of the room already beaten.
        spec["clear_flags"] = [lead_flag] + extra
        spec["set_flags"] = others
        spec["set_trainers"] = [f"{g['map']}_obj_{i}" for i, n, _x, _y in objs
                                if i != leader_obj]
    else:
        spec["clear_flags"] = [lead_flag] + others + extra
        spec["clear_trainers"] = [f"{g['map']}_obj_{i}"
                                  for i, _n, _x, _y in objs]
    if g.get("fights"):
        spec["fights"] = int(g["fights"])
    if g.get("score_only"):
        spec["score_flags"] = list(g["score_only"])
    if g.get("open_flags"):
        spec["set_flags"] = sorted(set(spec.get("set_flags") or [])
                                   | set(g["open_flags"]))
    return spec


# ---------------------------------------------------------- the catch rooms
# A PATCH OF GRASS AND A WANT, NOT A GYM (user, 2026-09-16: "build the
# catch room"). The spec's `catch` block — which ball, when to throw, how
# many — was authored in every policy since v1 and never scored: every
# arena is a trainer fight and the catch branch runs only on a wild one,
# so v8 through v14 carried the same three numbers unexamined. A catch
# room parks the party ON a grass cell (grind paces grass without needing
# ground on screen, so a restored save can start at once), marks every
# trainer on the map beaten so nobody walks over, and names what the
# trial is hunting — by TYPE, the way the outline's own upkeep legs ask.
# The score is the wanted Pokemon caught of those met, and the balls it
# took.
#
# The grass cells come from the engine's own map and tileset tables
# (Map:isGrassCell): Route 24's west column is grass at x 4-5, y 18-31,
# with a trainer standing on (5,20); Viridian Forest's west strip at x 1-2,
# y 6-23, with a trainer at (2,18).
CATCHES = [
    # THREE KINDS OF CATCH (user, 2026-09-16: "instead of viridian forest
    # pika how about we go with weedle for the easy catch, keep abra for the
    # 'throw ball first' action because the ideal catch is to initially
    # throw a single ball for runners then weaken/status before throwing
    # more balls, and make a new arena with a harder catch target, electric
    # in the power plant with a status-causing vileplume in party").
    #
    # EASY. WEEDLE is nearly half of the Forest (45% of its slots) at L3-5
    # with catch rate 255; a L10 CHARMANDER has nothing to put it to sleep
    # and a SCRATCH that takes most of one.
    dict(name="catch_weedle", map="VIRIDIAN_FOREST", badges=1,
         start=(1, 10), want_species=["WEEDLE"], encounters=30, targets=3,
         party=[("CHARMANDER", 10)], bag={"POKE_BALL": 10, "POTION": 2},
         money=500,
         note="WEEDLE is 45% of the Forest at L3-5 (catch rate 255): the "
              "easy catch, and a fight that can still knock out what it "
              "came for."),
    # THROW FIRST. A wild ABRA knows only TELEPORT and leaves on its first
    # move; a ball goes before any move. The lead is a BUTTERFREE whose
    # STUN_SPORE and SLEEP_POWDER are exactly what a careful catch reaches
    # for first — and here that turn is the one the ABRA leaves on.
    dict(name="catch_abra", map="ROUTE_24", badges=2,
         start=(4, 26), want_species=["ABRA"], encounters=40, targets=3,
         party=[("BUTTERFREE", 20), ("CHARMELEON", 20)],
         bag={"POKE_BALL": 10, "POTION": 2}, money=1500,
         note="ABRA is 15% of Route 24 at L8-12 and leaves on its first "
              "move; a BUTTERFREE leads with STUN_SPORE and SLEEP_POWDER, "
              "so a spec that statuses first never throws."),
    # HARD. Every wild in the Power Plant is ELECTRIC — VOLTORB and
    # MAGNEMITE at L21-23 (catch rate 190), PIKACHU, and the rare MAGNETON
    # (60) and ELECTABUZZ (45) at L32-36 — and VOLTORB can SELFDESTRUCT. A
    # VILEPLUME resists electricity and carries both a sleep and a
    # paralysis move, so status, weakening and the throw threshold all have
    # something to do. The floor spawns on every tile (a FACILITY map).
    # POISON AS A SOFTENER (user, 2026-09-28). Gen 1's catch formula counts
    # poison like paralysis; the catch rule's status list held only sleep
    # and paralysis moves, so an IVYSAUR with POISONPOWDER threw at full
    # health. The lead here has POISONPOWDER and nothing that sleeps or
    # paralyses, and hits hard enough that nothing is a safe weakener; the
    # wanted are the Forest's non-poison kinds (WEEDLE and KAKUNA are
    # POISON types and cannot be poisoned).
    dict(name="catch_poison", map="VIRIDIAN_FOREST", badges=2,
         start=(1, 10), want_species=["CATERPIE", "METAPOD", "PIKACHU"],
         encounters=40, targets=3,
         party=[("IVYSAUR", 20, ["TACKLE", "LEECH_SEED", "VINE_WHIP",
                                 "POISONPOWDER"])],
         bag={"POKE_BALL": 10, "POTION": 2}, money=1500,
         note="An IVYSAUR with POISONPOWDER and no sleep or paralysis move, "
              "hunting CATERPIE, METAPOD and PIKACHU: whether poisoning first "
              "saves balls."),
    dict(name="catch_powerplant", map="POWER_PLANT", badges=6,
         start=(4, 21), want_types=["ELECTRIC"], encounters=20, targets=4,
         party=[("VILEPLUME", 40, ["SLEEP_POWDER", "STUN_SPORE", "ACID",
                                   "MEGA_DRAIN"])],
         bag={"POKE_BALL": 10, "GREAT_BALL": 5, "SUPER_POTION": 3},
         money=5000,
         note="Every wild here is ELECTRIC, VOLTORB can SELFDESTRUCT, and "
              "MAGNETON and ELECTABUZZ catch at 60 and 45: a VILEPLUME with "
              "SLEEP_POWDER, STUN_SPORE and MEGA_DRAIN is the tool, and "
              "GREAT_BALLs beside POKE_BALLs let the ball rule choose."),
]


def build_catch(c: dict) -> dict:
    party = []
    for entry in c["party"]:
        sp, lv = entry[0], entry[1]
        moves = list(entry[2]) if len(entry) > 2 else natural_moves(sp, lv)
        for mv in moves:
            if len(entry) > 2 and mv not in natural_moves(sp, lv) \
                    and not can_learn(sp, mv) \
                    and mv not in natural_moves("GLOOM", lv):
                sys.exit(f"{c['name']}: {sp} cannot have {mv}")
        party.append({"species": sp, "level": lv, "moves": moves,
                      "nickname": sp})
    objs = room_objects(c["map"])
    return {"party": party, "bag": dict(c["bag"]), "money": c["money"],
            "start": {"map": c["map"], "x": c["start"][0],
                      "y": c["start"][1], "facing": "down"},
            "set_flags": trainer_flags(c["map"]),
            "set_trainers": [f"{c['map']}_obj_{i}" for i, _n, _x, _y in objs],
            # read by the arena runner, ignored by gin_save
            "catch": {"want_types": list(c.get("want_types") or []),
                      "want_species": list(c.get("want_species") or []),
                      "encounters": int(c["encounters"]),
                      "targets": int(c["targets"])}}


# ------------------------------------------------------- the training rooms
# A PATCH OF WILD GROUND, A TRAINEE AND A LEVEL TO REACH (user, 2026-09-19:
# "should we have some kind of training-policy and create a few training
# rooms to see if we can promote the best behavior for training"). Two
# tactics raise a weak member and each is right in different fights: the
# trainee leads and switches out on turn one, keeping its share of the
# experience; or it simply fights, with no wasted turn, no split and no
# switch-in hit, and so fewer walks to a nurse. The spec's `train` block
# chooses per encounter, and nothing scored it: every other room is a
# trainer fight or a catch.
#
# A room is parked ON wild ground with every trainer on the map beaten,
# like a catch room. What it measures is the FLOW: how far toward its goal
# level the trainee got inside a fixed budget of STEPS, the walk to the
# nearest nurse and back charged whenever the party has to go
# (`heal_walk`, counted off the engine's own map tables from the start
# cell to the nurse: the room's geography, the same for every candidate).
#
# THREE ROOMS, ONE FOR EACH ANSWER.
TRAINS = [
    # PLOW. A L5 PIKACHU on Route 1 (PIDGEY and RATTATA, L2-5, one step in
    # ten): it wins every fight there by itself, so a switch is a wasted
    # turn and half the experience given to an IVYSAUR that has no use for
    # it. North grass (10-17, 6-9); Viridian's nurse is 34 steps off.
    dict(name="train_early", map="ROUTE_1", badges=1, start=(12, 7),
         party=[("IVYSAUR", 20), ("PIDGEOTTO", 18), ("PIKACHU", 5)],
         trainee=3, goal=10, steps=400, heal_walk=68,
         bag={"POTION": 3}, money=1500,
         note="PIKACHU L5 beats everything Route 1 has (L2-5): fighting for "
              "itself is the whole answer, and every switch is a turn and "
              "half the experience thrown away."),
    # PER ENCOUNTER. An ODDISH L13 in Rock Tunnel (L15-17, one step in
    # seventeen). ABSORB is four times effective on GEODUDE and ONIX and
    # it takes them; ZUBAT's LEECH_LIFE is four times effective on IT, and
    # MACHOP out-levels it with nothing to fear from a 20-power ABSORB.
    # Neither constant tactic is right here; the Route 10 nurse is outside
    # the north mouth.
    dict(name="train_mid", map="ROCK_TUNNEL_1F", badges=3, start=(15, 5),
         party=[("CHARMELEON", 28), ("PIDGEOTTO", 26), ("ODDISH", 13)],
         trainee=3, goal=20, steps=600, heal_walk=40,
         bag={"POTION": 3, "SUPER_POTION": 3}, money=3000,
         note="ODDISH L13 takes GEODUDE and ONIX (ABSORB x4) and loses to "
              "ZUBAT (LEECH_LIFE x4 on it) and MACHOP: the right call "
              "changes with what walks out of the dark."),
    # SWITCH. Run 27's own shape: a MACHOP L24 beside a party in the
    # fifties, in Victory Road 2F's pocket by the Route 23 mouth, the
    # Indigo Plateau lobby's nurse 67 steps off. Half of what lives here is
    # L36-43; MACHOP can take the L22-26 third and nothing else. It went
    # L22 -> L24 in four attempts of that run.
    dict(name="train_late", map="VICTORY_ROAD_2F", badges=8, start=(27, 8),
         party=[("LAPRAS", 55), ("KADABRA", 52), ("PIDGEOT", 50),
                ("VENUSAUR", 56), ("DUGTRIO", 50), ("MACHOP", 24)],
         trainee=6, goal=30, steps=800, heal_walk=134,
         bag={"HYPER_POTION": 5, "FULL_HEAL": 2}, money=20000,
         note="MACHOP L24 in a party of fifties: it can take the L22-26 "
              "wilds and must not meet the L36-43 ones, and the nurse is a "
              "long walk, so every faint is dear."),
    # OUTLEVELED. Run of record 3's own shape (2026-09-24/25): a GEODUDE
    # raised on Route 6, where ODDISH hits ROCK/GROUND x4 and MANKEY x2 —
    # sixty percent of the slots — and every wild is L10-16. It wins those
    # fights on levels long before its types stop losing them, and a rule
    # that reads types alone sends it out anyway: 161 times in that run,
    # 87 of them at twice the wild's level or more, and VENUSAUR took the
    # experience (L30 -> L54, the trainee stuck at 29). The room asks when
    # levels outrank types. Started ON the grass nearest the south edge,
    # (12,31): a room starts with empty books and grind walks only ground
    # it has seen, so from the edge itself, (8,35), a fenced lane, it found
    # no reachable grass and every trial walked 0 steps (first scoring,
    # 2026-09-25). The nurse is Vermilion's: the edge comes out at the
    # city's (18,0) (north offset 5 blocks), 11 cells to the Center door at
    # (11,3) and about 5 inside, plus about 8 from this grass to the edge:
    # about 28 each way, 56 there and back (estimated, not walked).
    dict(name="train_outleveled", map="ROUTE_6", badges=2, start=(12, 31),
         party=[("VENUSAUR", 34), ("RATICATE", 28), ("PIDGEOTTO", 28),
                ("GEODUDE", 22)],
         trainee=4, goal=30, steps=700, heal_walk=56,
         bag={"POTION": 3, "SUPER_POTION": 3}, money=5000,
         note="GEODUDE L22 against L10-16 ODDISH (x4 on it), MANKEY (x2) "
              "and PIDGEY: out-levels all of it and is weak to most of it. "
              "Whether levels or types decide is the whole question."),
]


def exp_between(species: str, lo: int, hi: int) -> int:
    """Experience from level lo to level hi on this species' own growth
    curve (the engine's tables, check-side: a room's denominator)."""
    import gin_save
    mon = gin_save.load_lua(gin_save.GEN / "pokemon.lua").get(species) or {}
    curve = gin_save.CURVES[mon["growthRate"]]
    return int(curve(hi) - curve(lo))


def build_train(c: dict) -> dict:
    party = []
    for n, entry in enumerate(c["party"], 1):
        sp, lv = entry[0], entry[1]
        moves = list(entry[2]) if len(entry) > 2 else natural_moves(sp, lv)
        party.append({"species": sp, "level": lv, "moves": moves,
                      "nickname": sp})
        if n == c["trainee"]:
            # ITS OWN DVs, so the slot check pinned to it can tell it from
            # the rest when the policy moves it to the front: a built party
            # is otherwise six Pokemon with one trainer id and DVs of 15
            party[-1]["dv"] = 8
    who = c["party"][c["trainee"] - 1]
    objs = room_objects(c["map"])
    return {"party": party, "bag": dict(c["bag"]), "money": c["money"],
            "start": {"map": c["map"], "x": c["start"][0],
                      "y": c["start"][1], "facing": "down"},
            "set_flags": trainer_flags(c["map"]),
            "set_trainers": [f"{c['map']}_obj_{i}" for i, _n, _x, _y in objs],
            # read by the arena runner, ignored by gin_save
            "train": {"trainee": int(c["trainee"]), "goal": int(c["goal"]),
                      "steps": int(c["steps"]),
                      "heal_walk": int(c["heal_walk"]),
                      "need_exp": exp_between(who[0], int(who[1]),
                                              int(c["goal"]))}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="say what would be built and stop")
    ap.add_argument("--only", default="",
                    help="one room by name (pewter ... viridian, e4)")
    ap.add_argument("--path", choices=["real", "ideal", "late", "both"],
                    default="both", help="which path's rooms to build")
    a = ap.parse_args()
    rc = 0
    for c in CATCHES:
        if a.only and c["name"] != a.only:
            continue
        base = pick_base(c["badges"])
        spec = build_catch(c)
        print(f"\n=== {c['name']}  {c['map']} at {c['start']}  hunting "
              f"{'/'.join((c.get('want_types') or []) + (c.get('want_species') or []))}")
        print(f"    base {base.parent.name if base else 'MISSING'}")
        for m in spec["party"]:
            print(f"    {m['species']:11s} L{m['level']:<3d} "
                  + "/".join(m["moves"]))
        print("    bag " + ", ".join(f"{k} x{v}" for k, v in spec["bag"].items()))
        print(f"    {c['note']}")
        if a.list:
            continue
        if not base or not Path(base).exists():
            print(f"    SKIPPED: no base save for {c['name']}")
            rc = 1
            continue
        sp = REPO / f"plans/arena_{c['name']}.json"
        sp.write_text(json.dumps(spec, indent=2))
        out = REPO / f"run/arena_{c['name']}.lua"
        r = subprocess.run([sys.executable, str(REPO / "planner/gin_save.py"),
                            "--base", str(base), "--spec", str(sp),
                            "--out", str(out)],
                           capture_output=True, text=True)
        print("    " + (r.stdout.strip().replace("\n", "\n    ")
                        or r.stderr.strip()[:300]))
        rc = rc or r.returncode
    for c in TRAINS:
        if a.only and c["name"] != a.only:
            continue
        base = pick_base(c["badges"])
        spec = build_train(c)
        who = spec["party"][c["trainee"] - 1]
        print(f"\n=== {c['name']}  {c['map']} at {c['start']}  raising "
              f"{who['species']} L{who['level']} to L{c['goal']} in "
              f"{c['steps']} steps (nurse and back: {c['heal_walk']})")
        print(f"    base {base.parent.name if base else 'MISSING'}")
        for m in spec["party"]:
            print(f"    {m['species']:11s} L{m['level']:<3d} "
                  + "/".join(m["moves"]))
        print("    bag " + ", ".join(f"{k} x{v}" for k, v in spec["bag"].items()))
        print(f"    {c['note']}")
        if a.list:
            continue
        if not base or not Path(base).exists():
            print(f"    SKIPPED: no base save for {c['name']}")
            rc = 1
            continue
        sp = REPO / f"plans/arena_{c['name']}.json"
        sp.write_text(json.dumps(spec, indent=2))
        out = REPO / f"run/arena_{c['name']}.lua"
        r = subprocess.run([sys.executable, str(REPO / "planner/gin_save.py"),
                            "--base", str(base), "--spec", str(sp),
                            "--out", str(out)],
                           capture_output=True, text=True)
        print("    " + (r.stdout.strip().replace("\n", "\n    ")
                        or r.stderr.strip()[:300]))
        rc = rc or r.returncode
    if a.only.startswith(("catch_", "train_")):
        return rc
    for g in GYMS:
        if a.only and g["name"] != a.only:
            continue
        for path in ((list(g["paths"]) if a.path == "both" else (a.path,))):
            p = g["paths"].get(path)
            if p is None:
                continue        # the league's ideal party is a hand file
            name = f"{g['name']}_{path}"
            base = g.get("base") or pick_base(g["badges"])
            spec = build(g, path)
            n_beat = len(spec.get("clear_flags") or [])
            print(f"\n=== {name}  {g['map']}  "
                  f"{'ONE FIGHT (puzzle room)' if g['puzzle'] else str(n_beat) + ' to beat'}"
                  f"  leader's ace L{g['ace']}")
            print(f"    base {base.parent.name if base else 'MISSING'} "
                  f"({len(badges_of(base)) if base else 0} badge(s))")
            for m in spec["party"]:
                print(f"    {m['species']:11s} L{m['level']:<3d} "
                      + "/".join(m["moves"]))
            print("    bag " + ", ".join(f"{k} x{v}"
                                         for k, v in spec["bag"].items())
                  + f"; money {spec['money']}")
            print(f"    {p['note']}")
            if a.list:
                continue
            if not base or not Path(base).exists():
                print(f"    SKIPPED: no base save for {name}")
                rc = 1
                continue
            sp = REPO / f"plans/arena_{name}.json"
            sp.write_text(json.dumps(spec, indent=2))
            out = REPO / f"run/arena_{name}.lua"
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

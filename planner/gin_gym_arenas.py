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

GYMS = [
    dict(name="pewter", map="PEWTER_GYM", leader="BROCK", ace=14,
         badges=0, door=(4, 13), puzzle=False,
         paths=dict(
             real=dict(party=[("CHARMANDER", 14), ("PIDGEY", 10)],
                       bag={"POTION": 5}, money=1600,
                       note="Both model-authored runs walked in with the "
                            "starter alone, L13-14, and blacked out four "
                            "times (Aug 28) and once (Sep 6) before the "
                            "badge; the bird is the user's call."),
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
             ideal=dict(party=[("SQUIRTLE", 10), ("NIDORAN_M", 10)],
                        bag={"POTION": 8}, money=2000,
                        note="SQUIRTLE's BUBBLE is the answer, four under "
                             "the ace, and alone: the starter IS the "
                             "answer here, so nothing else is needed "
                             "(user, 2026-09-15: \"if squirt for brock we "
                             "dont need mankey\")."))),
    dict(name="cerulean", map="CERULEAN_GYM", leader="MISTY", ace=21,
         badges=1, door=(4, 13), puzzle=False,
         paths=dict(
             real=dict(party=[("ODDISH", 19), ("CHARMELEON", 26),
                              ("PIDGEOTTO", 18)],
                       bag={"POTION": 5, "ANTIDOTE": 1}, money=2400,
                       note="The ODDISH led in both runs, caught for the "
                            "'WATER or GRASS' leg and sent out at 16-19 "
                            "against a L21 STARMIE. Five POTIONs is what "
                            "the counter question bought here, on "
                            "record."),
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
             ideal=dict(party=[("IVYSAUR", 18), ("PIDGEOTTO", 18)],
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
             real=dict(party=[("CHARIZARD", 37, ["BODY_SLAM"]),
                              ("PIDGEOTTO", 29), ("GLOOM", 25)],
                       bag={"POTION": 3, "SUPER_POTION": 5}, money=8000,
                       note="The Sep 6 run's room less its GYARADOS: that "
                            "run had one at 24 here, but a run gets its "
                            "water from an Old Rod MAGIKARP when it is "
                            "forced to find a SURF member for Cinnabar, "
                            "not before (user, 2026-09-15). The starter "
                            "thirteen over the ace. The bag is run 17's "
                            "at this door, on record."),
             ideal=dict(party=[("DIGLETT", 19),
                               ("CHARMELEON", 20, ["BODY_SLAM"]),
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
             real=dict(party=[("GLOOM", 36), ("CHARIZARD", 40, ["BODY_SLAM"]),
                              ("PIDGEOT", 41), ("DUGTRIO", 34)],
                       bag={"SUPER_POTION": 3}, money=13800,
                       note="GLOOM led (Aug 28), a PIDGEOTTO on Sep 6, so "
                            "the GLOOM stands first and carries CUT in "
                            "place of ACID (DUGTRIO cannot learn it, and "
                            "on the CHARIZARD it cost SLASH). Three "
                            "SUPER_POTIONs is the bag run 17 blacked out "
                            "with here."),
             ideal=dict(party=[("FEAROW", 24),
                               ("CHARMELEON", 25, ["BODY_SLAM"]),
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
             real=dict(party=[("PIDGEOT", 47, ["FLY"]),
                              ("VILEPLUME", 44, ["MEGA_DRAIN"]),
                              ("DUGTRIO", 46, ["EARTHQUAKE"]),
                              ("CHARIZARD", 46, ["BODY_SLAM"]),
                              ("HITMONLEE", 40)],
                       bag={"SUPER_POTION": 5}, money=12800,
                       note="PIDGEOT led (Aug 28), DUGTRIO on Sep 6. Both "
                            "outlines did Sabrina before Koga, so this "
                            "party is the Saffron one a few levels on, "
                            "and Silph's EARTHQUAKE is already had."),
             ideal=dict(party=[("KADABRA", 38),
                               ("CHARIZARD", 38, ["BODY_SLAM"]),
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
             real=dict(party=[("PIDGEOT", 45, ["FLY"]),
                              ("VILEPLUME", 43, ["MEGA_DRAIN"]),
                              ("DUGTRIO", 44, ["EARTHQUAKE"]),
                              ("CHARIZARD", 46, ["BODY_SLAM"]),
                              ("HITMONLEE", 35)],
                       bag={"HYPER_POTION": 5}, money=34500,
                       note="PIDGEOT led (Aug 28), DUGTRIO on Sep 6; the "
                            "HITMONLEE is fresh from the Dojo at 35, "
                            "since both outlines did this gym before "
                            "Koga."),
             ideal=dict(party=[("SNORLAX", 38, ["EARTHQUAKE"]),
                               ("CHARIZARD", 38, ["BODY_SLAM"]),
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
             real=dict(party=[("DUGTRIO", 47), ("VILEPLUME", 48, ["MEGA_DRAIN"]),
                              ("PIDGEOT", 50, ["FLY"]),
                              ("GYARADOS", 30, ["THUNDERBOLT"]),
                              ("HITMONLEE", 46),
                              ("CHARIZARD", 47, ["BODY_SLAM"])],
                       bag={"HYPER_POTION": 5}, money=57000,
                       note="DUGTRIO led (Aug 28), GLOOM on Sep 6. The "
                            "GYARADOS is the Old Rod MAGIKARP raised to "
                            "evolve and carry SURF for the crossing, so "
                            "it arrives low (user, 2026-09-15)."),
             ideal=dict(party=[("STARMIE", 42, ["BUBBLEBEAM", "THUNDERBOLT", "ICE_BEAM"]),
                               ("CHARIZARD", 42, ["BODY_SLAM"]),
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
             real=dict(party=[("DUGTRIO", 52), ("VILEPLUME", 46, ["MEGA_DRAIN"]),
                              ("PIDGEOT", 50, ["FLY"]),
                              ("GYARADOS", 36, ["THUNDERBOLT"]),
                              ("HITMONLEE", 48),
                              ("CHARIZARD", 47, ["BODY_SLAM"])],
                       bag={"HYPER_POTION": 5}, money=69000,
                       note="DUGTRIO led (Aug 28), HITMONLEE on Sep 6; the "
                            "Sep 6 roster at Giovanni with the late "
                            "GYARADOS six levels on. RHYDON L50 against "
                            "a L36 GYARADOS's SURF is the fight."),
             ideal=dict(party=[("STARMIE", 45, ["BUBBLEBEAM", "THUNDERBOLT", "ICE_BEAM"]),
                               ("CHARIZARD", 45, ["BODY_SLAM"]),
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
             real=dict(party=[("VILEPLUME", 54, ["MEGA_DRAIN"]),
                              ("HITMONLEE", 57),
                              ("PIDGEOT", 54, ["FLY"]),
                              ("CHARIZARD", 55, ["BODY_SLAM"]),
                              ("GYARADOS", 54, ["THUNDERBOLT"]),
                              ("DUGTRIO", 54)],
                       bag={"FULL_RESTORE": 5}, money=48500,
                       note="The Sep 6 run's first league attempt, with "
                            "the stone: GLOOM led, six at 54-57 against "
                            "a Lance at 58-62, and it fell to the "
                            "Champion. Four attempts in all."))),
]


def build(g: dict, path: str) -> dict:
    p = g["paths"][path]
    party = []
    for entry in p["party"]:
        sp, lv = entry[0], entry[1]
        party.append({"species": sp, "level": lv,
                      "moves": natural_moves(sp, lv), "nickname": sp,
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
    dict(name="catch_forest", map="VIRIDIAN_FOREST", badges=1,
         start=(1, 10), want_types=["ELECTRIC"], encounters=40, targets=3,
         party=[("CHARMANDER", 10)], bag={"POKE_BALL": 10, "POTION": 2},
         money=500,
         note="PIKACHU is 5% of the Forest at L3-5, against a CHARMANDER "
              "whose SCRATCH takes most of one: the throw has to come "
              "before the weakening does, and a ball spent on a full-HP "
              "PIKACHU lands about a quarter of the time (catch rate 190)."),
    # ABRA, NOT ODDISH (user, 2026-09-16: "maybe the rt24 one can be for
    # abra though, i think itd end up breaking things because it teleports
    # away and you need to just throw balls at it as soon as you see it").
    # A wild ABRA knows only TELEPORT and leaves on its first move, and a
    # ball goes before any move, so the throw on turn one is the only
    # throw there is: a spec that weakens first, or waits for a threshold,
    # catches nothing here. ODDISH walks the same grass as the thing to
    # run from.
    dict(name="catch_route24", map="ROUTE_24", badges=2,
         start=(4, 26), want_types=["PSYCHIC"], encounters=40, targets=3,
         party=[("CHARMELEON", 20), ("PIDGEOTTO", 18)],
         bag={"POKE_BALL": 10, "POTION": 2}, money=1500,
         note="ABRA is 15% of Route 24 at L8-12 and knows only TELEPORT: "
              "it leaves on its first move, and a ball is thrown before "
              "any move, so each ABRA met allows one throw at full HP "
              "(catch rate 200)."),
]


def build_catch(c: dict) -> dict:
    party = [{"species": sp, "level": lv, "moves": natural_moves(sp, lv),
              "nickname": sp} for sp, lv in c["party"]]
    objs = room_objects(c["map"])
    return {"party": party, "bag": dict(c["bag"]), "money": c["money"],
            "start": {"map": c["map"], "x": c["start"][0],
                      "y": c["start"][1], "facing": "down"},
            "set_flags": trainer_flags(c["map"]),
            "set_trainers": [f"{c['map']}_obj_{i}" for i, _n, _x, _y in objs],
            # read by the arena runner, ignored by gin_save
            "catch": {"want_types": list(c["want_types"]),
                      "encounters": int(c["encounters"]),
                      "targets": int(c["targets"])}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="say what would be built and stop")
    ap.add_argument("--only", default="",
                    help="one room by name (pewter ... viridian, e4)")
    ap.add_argument("--path", choices=["real", "ideal", "both"],
                    default="both", help="which path's rooms to build")
    a = ap.parse_args()
    rc = 0
    for c in CATCHES:
        if a.only and c["name"] != a.only:
            continue
        base = pick_base(c["badges"])
        spec = build_catch(c)
        print(f"\n=== {c['name']}  {c['map']} at {c['start']}  hunting "
              f"{'/'.join(c['want_types'])}")
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
    if a.only.startswith("catch_"):
        return rc
    for g in GYMS:
        if a.only and g["name"] != a.only:
            continue
        for path in (("real", "ideal") if a.path == "both" else (a.path,)):
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

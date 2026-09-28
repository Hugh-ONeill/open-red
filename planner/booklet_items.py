"""The instruction booklet's item tables, verbatim (audit PT-41, 2026-09-28).

Pokemon Red Version (USA) instruction booklet pp.40-43. Pamphlet tier by
definition: every player had these pages. The author used to get a
seven-line spelling aid; a run holding GOLD TEETH was told the name and left
to guess what it is for, which the booklet says outright. Nothing here says
WHERE an item is found.

Keys are the engine's item ids; values are the booklet's own words.
"""
from __future__ import annotations

TABLES = [
    ("TYPES OF BALLS", {
        "POKE_BALL": "This ball catches Pokemon. The cost is reasonable.",
        "GREAT_BALL": "This ball performs better than a Poke Ball.",
        "ULTRA_BALL": "This ball performs better than a Great Ball.",
        "SAFARI_BALL": "This special ball is for capturing Pokemon in Safari Zone.",
        "MASTER_BALL": "This ball can capture a Pokemon 100% of the time.",
    }),
    ("MYSTERY ITEMS", {
        "FIRE_STONE": "This stone has a connection to Fire Pokemon.",
        "THUNDER_STONE": "This stone has a connection to Electric Pokemon.",
        "WATER_STONE": "This stone has a connection to Water Pokemon.",
        "LEAF_STONE": "This stone has a connection to Grass Pokemon.",
        "MOON_STONE": "This stone has a connection to ? Pokemon.",
        "HELIX_FOSSIL": "You will need to find the secret of this item.",
        "DOME_FOSSIL": "You will need to find the secret of this item.",
        "OLD_AMBER": "You will need to find the secret of this item.",
    }),
    ("RECOVERY ITEMS", {
        "ANTIDOTE": "This removes poison from a Pokemon.",
        "BURN_HEAL": "This heals a Pokemon that is burned.",
        "ICE_HEAL": "This thaws a frozen Pokemon.",
        "AWAKENING": "This wakes up a sleeping Pokemon.",
        "PARLYZ_HEAL": "This heals a paralyzed Pokemon.",
        "FULL_HEAL": "This will heal all of the conditions stated above.",
        "POTION": "This will restore some HP.",
        "SUPER_POTION": "This will restore more HP than a POTION.",
        "HYPER_POTION": "This will restore more HP than a SUPER POTION.",
        "MAX_POTION": "This will restore HP to its maximum.",
        "FULL_RESTORE": "This will heal all conditions and fully restore HP.",
        "REVIVE": "This will revive a fainted Pokemon and restore 1/2 HP.",
        "MAX_REVIVE": "This will revive a fainted Pokemon and fully restore HP.",
    }),
    ("POKEMON POWER-UPS", {
        "RARE_CANDY": "Increases a Pokemon's level by 1.",
        "HP_UP": "HP level will increase.",
        "PROTEIN": "Attack power points will increase.",
        "IRON": "Defense power points will increase.",
        "CARBOS": "Speed points will increase.",
        "CALCIUM": "Special ability points will increase.",
        "X_ATTACK": "Available only in battle, attack power will increase.",
        "X_DEFEND": "Available only in battle, defense power will increase.",
        "X_SPEED": "Available only in battle, speed will increase.",
        "X_SPECIAL": "In battle, special ability will increase.",
        "GUARD_SPEC": "In battle, enemy Pokemon can't use special attack.",
        "DIRE_HIT": "In battle, your attacks will be more effective.",
        "X_ACCURACY": "In battle, your chance of hitting will increase.",
        "PP_UP": "PP level will increase.",
    }),
    ("FIELD MOVING", {
        "BICYCLE": "This is too expensive for a child to buy.",
        "ESCAPE_ROPE": "This rope can pull you out of a cave instantly.",
        "REPEL": "Spray on and weak Pokemon will avoid you for a while.",
        "SUPER_REPEL": "This spray lasts longer than REPEL.",
        "MAX_REPEL": "This spray lasts longer than SUPER REPEL.",
    }),
    ("SPECIAL ITEMS", {
        "POKEDEX": "Record Pokemon data in this high-tech index.",
        "TOWN_MAP": "This map will help you navigate the world of Pokemon.",
        "TM": "Get Technical Machines from many people.",
        "HM": "Get Hidden Machines from many people.",
    }),
    ("MISCELLANEOUS", {
        "NUGGET": "This item is not very effective unless you're after gold.",
        "GOLD_TEETH": "These belong to the warden of Safari Zone.",
        "S_S_TICKET": "A boarding ticket for the S.S. Anne.",
        "POKE_DOLL": "A popular doll. Try using it during battle.",
        "SILPH_SCOPE": "This allows you to identify a ghostly Pokemon.",
        "POKE_FLUTE": "It wakes up sleeping Pokemon. It's handy during battle.",
        "OLD_ROD": "Use this rod to fish for water Pokemon.",
        "GOOD_ROD": "This rod can catch Pokemon that the OLD ROD can't.",
        "SUPER_ROD": "The best rod. It catches Pokemon that the other rods can't.",
        "ITEMFINDER": "This handy machine helps you find items.",
        "EXP_ALL": "Share experience points with Pokemon who didn't fight.",
        "COIN": "Use these at the Game Corner.",
        "COIN_CASE": "Save a maximum of 9,999 coins in this.",
        "FRESH_WATER": "During battle, it will restore HP a little.",
        "SODA_POP": "During battle, it will restore HP a lot.",
        "LEMONADE": "During battle, it will restore HP a lot more.",
    }),
]
ITEMS = {k: v for _t, rows in TABLES for k, v in rows.items()}
# the tables whose items' purpose is not plain from the name alone
_JOBS = {"MYSTERY ITEMS", "FIELD MOVING", "SPECIAL ITEMS", "MISCELLANEOUS"}
JOBS = {k: v for t, rows in TABLES if t in _JOBS for k, v in rows.items()}


def tables_text() -> str:
    """Every table, for the author."""
    out = []
    for title, rows in TABLES:
        out.append(f"  {title}: " + "; ".join(f"{k}: {v}" for k, v in rows.items()))
    return "\n".join(out)


def jobs_for(bag) -> list:
    """(id, booklet line) for the held items whose job the booklet states."""
    out = []
    for k in sorted(bag or {}):
        k = str(k)
        line = JOBS.get(k)
        if line is None and k.startswith(("TM", "HM")) and k[2:3].isdigit():
            continue
        if line:
            out.append((k, line))
    return out

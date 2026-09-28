"""Event flags the game sets without a word on screen (audit 6a, 2026-09-28).

The test (user, 2026-09-28): a flag whose change the game announces in text
is on-screen knowledge, and showing it after it fires repeats the screen. A
flag set silently is not: EVENT_ROUTE22_RIVAL_WANTS_BATTLE is set by Oak's
lab script at the Pokedex hand-over and announces a fight on Route 22 that
has not happened. Sorted from the game's own scripts, not by name: every
`set_flag` step in gen1recomp data/scripts and every flag the engine sets
directly (src/, story*.lua) was read, and these are the ones with no message
of their own. Trainer wins, items, gifts, the Vermilion lock switches, the
boulder switches and the S.S. Anne sailing all print or show what happened.

Hidden from every prompt string and from the journal's `flag_fired` record
(logged as `flag_set_silently` instead). Predicates still read live RAM, and
flag COUNTS stay raw: they are stamped into saved records and compared
across restarts, and a silent-only change is rare.
"""
from __future__ import annotations

SILENT = frozenset({
    # arming a fight that has not happened (oaks_lab.lua:149-151; the second
    # pair re-armed later by the same kind of step)
    "EVENT_1ST_ROUTE22_RIVAL_BATTLE",
    "EVENT_2ND_ROUTE22_RIVAL_BATTLE",
    "EVENT_ROUTE22_RIVAL_WANTS_BATTLE",
    # script bookkeeping: a second copy of an announced flag, or a mark the
    # engine keeps about where the player walked (story2.lua:166-167, the
    # Bill / Mr. Fuji / Champion scripts, Lavender's purified zone, the
    # Elite Four entrance)
    "EVENT_FOLLOWED_OAK_INTO_LAB_2",
    "EVENT_MET_BILL_2",
    "EVENT_RESCUED_MR_FUJI_2",
    "EVENT_BEAT_CHAMPION_RIVAL_THIS_RUN",
    "EVENT_IN_PURIFIED_ZONE",
    "EVENT_LEFT_BILLS_HOUSE_AFTER_HELPING",
    "EVENT_STARTED_ELITE_4",
})


def announced(flags) -> list:
    """The flags a player was shown, in the order given."""
    return [f for f in (flags or []) if str(f) not in SILENT]

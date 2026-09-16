#!/usr/bin/env python3
"""What the outline still asks the party to BECOME, read for the wild in
front of you.

The outline carries the party's future as checkable states, in the
model's own words: "the party holds a GRASS or ELECTRIC type" before
Misty, "a GROUND type" before Surge, and so on (plans/outline.upkeep). Each
fires at a fixed spot in the list, and by then the local grass may not
hold the type: there is no ELECTRIC between Pewter and Misty, and the
Forest's PIKACHU is behind you, so the leg settles for whatever does (an
ODDISH on Route 24) — or, as run 18's leg 5 did, grinds three routes for
a WATER or GRASS type that none of them has (user, 2026-09-16:
"opportunistic catching where encounters trigger a catch if it can fill a
future catch goal, that way we have a chance to snag pikachu when walking
through the viridian forest").

This module only READS the list: which legs are still ahead, and which of
those a caught Pokemon would satisfy by its type or its species. The legs
are the model's sentences, the wild's type and species are on the battle
screen, and the party's are on its status pages. Nothing here names a
species the outline did not.
"""
from __future__ import annotations

import re
from pathlib import Path

TYPE_NAMES = {"NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK",
              "BUG", "GHOST", "FIRE", "WATER", "GRASS", "ELECTRIC",
              "PSYCHIC", "ICE", "DRAGON"}

# a leg about what a party member KNOWS or what LEVEL it is: a ball
# satisfies neither, whatever types its sentence happens to mention
_NOT_A_CATCH = re.compile(r"^\s*(a party pokemon knows|every party member|"
                          r"the party is fully evolved)\b", re.I)
# the verbs a catch answers. "Defeat the FIRE gym" and "Retrieve the
# Pokemon Flute" mention nothing a ball satisfies; "holds a WATER type",
# "catch a PIKACHU", "obtain a GROUND type Pokemon" do.
_CATCH_VERB = re.compile(r"\b(holds?|has|have|catch|catching|caught|capture|"
                         r"obtain|acquire|add|in the party|party member|"
                         r"join)\b", re.I)
_NOT_A_CATCH_WORD = re.compile(r"\b(defeat|beat|badge|gym|evolve[sd]?|"
                               r"evolution|trade[sd]?|level)\b", re.I)


def _key(word: str) -> str:
    """FARFETCH'D, Farfetch'd and FARFETCHD are one name."""
    return re.sub(r"[^A-Z0-9]", "", str(word).upper())


def legs_ahead(plans: Path, run: Path) -> list[tuple[int, str]]:
    """(1-based position, wording) of every leg after the run's high-water
    mark. A crossed-off leg is removed from the list (skip_legs.py), a
    pushed one is rewritten later in it, so the file is read fresh each
    time and never cached."""
    try:
        lines = [l.rstrip("\n") for l in (plans / "outline.txt").read_text()
                 .splitlines() if l.strip()]
    except OSError:
        return []
    try:
        mark = int((run / "outline_leg").read_text().strip() or 0)
    except (OSError, ValueError):
        mark = 0
    return [(i, l) for i, l in enumerate(lines, 1) if i > mark]


def goal_of(leg: str, species_names: set | None = None) -> dict | None:
    """The types and species a caught Pokemon would answer this leg with,
    or None when the leg is not that kind of thing."""
    if _NOT_A_CATCH.search(leg) or _NOT_A_CATCH_WORD.search(leg):
        return None
    if not _CATCH_VERB.search(leg):
        return None
    words = re.findall(r"[A-Za-z][A-Za-z'.]*", leg)
    types = {w.upper() for w in words if w.upper() in TYPE_NAMES}
    # "a FIRE type" is a type; "the Fire Stone" would be too without this
    if types and not re.search(r"\btypes?\b", leg, re.I):
        types = set()
    keyed = {_key(s): s for s in (species_names or ())}
    species = {keyed[_key(w)] for w in words if _key(w) in keyed}
    if not (types or species):
        return None
    return {"types": types, "species": species}


def catch_goals_ahead(plans: Path, run: Path, species_names: set | None,
                      party: list | None = None) -> list[dict]:
    """Legs ahead that a caught Pokemon satisfies by TYPE or SPECIES, less
    the ones the party in hand already meets — a second PIDGEY is not a
    catch toward "the party holds a FLYING type"."""
    have_t = {str(t).upper() for m in (party or [])
              for t in (m.get("types") or [])}
    have_s = {_key(m.get("species") or "") for m in (party or [])}
    out = []
    for pos, leg in legs_ahead(plans, run):
        g = goal_of(leg, species_names)
        if not g:
            continue
        if (g["types"] & have_t) or ({_key(s) for s in g["species"]} & have_s):
            continue
        out.append({"pos": pos, "leg": leg, **g})
    return out


def goals_met_by(goals: list[dict], species: str, types) -> list[dict]:
    """Which of these goals the Pokemon on screen would answer."""
    sp = _key(species or "")
    ty = {str(t).upper() for t in (types or [])}
    return [g for g in goals
            if sp and sp in {_key(s) for s in g["species"]}
            or (ty & g["types"])]

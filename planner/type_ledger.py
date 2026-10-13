#!/usr/bin/env python3
"""What the run KNOWS of a species' types, as a player could know it.

Gen 1's battle screen shows the foe's name, level and HP bar (booklet
p.34), never its types, and the Pokedex grid pictures species without
them. The shim read the foe's types out of the game's memory and every
consumer took them as seen: the move scorer, leads and switches, the catch
question ("THE WILD POKEMON: ONIX (ROCK/GROUND)"), type-goal catches (user,
2026-10-13: "yeah we have to make that change too to be accurate"). What a
player has is:

  * OWNED — a species the run has had in its party: the summary screen
    shows its types, and they are known from then on;
  * SEEN — what the game said after an attack landed on it: "It's super
    effective!", "It's not very effective...", "It doesn't affect" — one
    move type against one species at a time (2x and 4x read the same);
  * SAID — the model's own word, asked once the first time a species is
    met (Executor._ask_types). The model may know Pokemon; the harness
    may not. A wrong answer is the model's, and what was SEEN for a move
    type overrides it.

Bridge.obs() lays this over every observation (scrub), so nothing reads the
memory's types for a foe. Persisted with the run's memory (explored.json
"type_ledger").
"""
from __future__ import annotations

import re

TYPES = ("NORMAL", "FIRE", "WATER", "ELECTRIC", "GRASS", "ICE", "FIGHTING",
         "POISON", "GROUND", "FLYING", "PSYCHIC_TYPE", "BUG", "ROCK", "GHOST",
         "DRAGON")

OWNED: dict = {}     # species -> [types], from the party's summary screens
SAID: dict = {}      # species -> [types], the model's word
SEEN: dict = {}      # "SPECIES|MOVETYPE" -> 0.0 / 0.5 / 1.0 / 2.0


def reset() -> None:
    OWNED.clear()
    SAID.clear()
    SEEN.clear()


def load(d: dict | None) -> None:
    reset()
    d = d or {}
    OWNED.update(d.get("owned") or {})
    SAID.update(d.get("said") or {})
    SEEN.update({k: float(v) for k, v in (d.get("seen") or {}).items()})


def dump() -> dict:
    return {"owned": OWNED, "said": SAID, "seen": SEEN}


def norm_type(t) -> str | None:
    t = str(t or "").upper().strip().replace(" ", "_")
    if t == "PSYCHIC":
        t = "PSYCHIC_TYPE"
    return t if t in TYPES else None


def note_party(obs: dict | None) -> None:
    """Every party member's types are on its summary screen."""
    for m in (obs or {}).get("party") or []:
        if isinstance(m, dict) and m.get("species") and m.get("types"):
            ts = [x for x in (norm_type(t) for t in m["types"]) if x]
            if ts:
                OWNED[str(m["species"])] = ts


def believed(species) -> tuple[list | None, str | None]:
    """(types, where from) — owned, else the model's word, else nothing."""
    sp = str(species or "")
    if sp in OWNED:
        return list(OWNED[sp]), "owned"
    if sp in SAID:
        return list(SAID[sp]), "said"
    return None, None


def seen_for(species) -> dict:
    """{move type: multiplier} the game has said for this species."""
    pre = f"{species}|"
    return {k[len(pre):]: v for k, v in SEEN.items() if k.startswith(pre)}


_SUPER = re.compile(r"super effective", re.I)
_NOT_VERY = re.compile(r"not very effective", re.I)
_NONE = re.compile(r"(doesn.t|didn.t|does not|did not) affect", re.I)


def note_hit(species, move_type, text: str, landed: bool) -> float | None:
    """File what the game said after OUR move of `move_type` hit `species`.
    `landed`: the bar moved (or it fainted). A miss says nothing."""
    mt = norm_type(move_type)
    if not species or not mt:
        return None
    t = str(text or "")
    if _NONE.search(t):
        x = 0.0
    elif _SUPER.search(t):
        x = 2.0
    elif _NOT_VERY.search(t):
        x = 0.5
    elif landed:
        x = 1.0
    else:
        return None
    SEEN[f"{species}|{mt}"] = x
    return x


def scrub(obs: dict | None) -> dict | None:
    """The foe's types as the run knows them, not as the memory holds them.

    battle.foe.types becomes the believed types (absent when none), with
    `types_from` ("owned" / "said") and `eff_seen` ({move type: x})."""
    if not isinstance(obs, dict):
        return obs
    note_party(obs)
    b = obs.get("battle")
    if isinstance(b, dict) and isinstance(b.get("foe"), dict):
        foe = dict(b["foe"])
        ts, src = believed(foe.get("species"))
        foe.pop("types", None)
        if ts:
            foe["types"] = ts
            foe["types_from"] = src
        foe["eff_seen"] = seen_for(foe.get("species"))
        obs["battle"] = dict(b, foe=foe)
    return obs

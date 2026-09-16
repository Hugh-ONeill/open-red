#!/usr/bin/env python3
"""Battle policy: choose a battle action from the observation.

The policy is driven by a SPEC (a dict of rules/params) — "rules as data"
per CLAIM_RULES v1, so it is the model-authorable artifact. This file is
the deterministic INTERPRETER; the rules/values come from the spec. The
hand-seeded DEFAULT_SPEC exists for spine/oracle validation only; the
record run requires a model-authored spec (policy_author.py).

SPEC DSL v1 (all keys optional; unknown keys are validation errors):
  name: str
  stab: float 1.0-2.0        same-type attack bonus weight in move scoring
  accuracy_weight: bool      weight move score by accuracy
  prefer_ko: bool            a move OBSERVED to KO wins over raw score
  ko_margin: float >= 1.0    trust a KO only if the least damage this move
                             has been SEEN to do (this species, our level)
                             >= foe hp*margin — empirical, no formulas
  avoid_status_moves: bool   never pick 0-power moves by score
  setup: [ { move: str       deliberate status-move use, e.g. TAIL_WHIP
             max_uses: int      per battle (default 1)
             first_turns: int   only in the battle's first N turns (def. 2)
             min_hp_frac: float only while own hp/max >= this (default 0.5)
             vs: "trainer"|"wild"|"any" (default "trainer")
             only_if_best_physical: bool  only when our best damage move is
                physical (e.g. TAIL_WHIP helps TACKLE, not BUBBLE) } ]
  switch: [ { to: int|str      bring in this party slot MID-BATTLE, or
                             name an ORDER and let it pick: "resists",
                             "best_matchup", "healthiest", "first_alive".
                             A raw slot number is a POSITION and means a
                             different Pokemon in every party; an order
                             means the same thing always. The foe IS on
                             screen here, so unlike `lead` the type
                             orders have something to read.
              first_turns: int   only in the battle's first N turns (def. 1)
              max_uses: int      per battle (default 1)
              vs: "trainer"|"wild"|"any" (default "any")
              hp_below: float|null  only when the ACTIVE mon's hp frac is
                 below this — omit to switch regardless of health
              only_if_lead: int|null  only when the mon that STARTED this
                 battle was that slot } ]
            A switch costs the turn and the foe gets a free hit. Whether
            that price is worth paying, and what for, is yours to decide
            and to write down as conditions.
  flee_wild: { when_traversal: bool   flee wilds during traversal subgoals
               hp_below: float|null } flee ANY wild when own hp frac below
  battle_items: [ { item: str, target: "self"|"fainted" (def self)
                                       use a healing item IN battle (costs
                    hp_below: float    the turn) when own hp frac < this
                    prefer: str        which one, when `item` is a CLASS
                    max_uses: int      per battle (default 2)
                    max_uses_run: int  across EVERY battle since the party
                                       was last made whole (a Center, a
                                       blackout, an arena trial); no cap
                                       unless written
                    reserve: int       never fire if it would leave fewer
                                       than this many of the item (of the
                                       whole class, for a class) in the
                                       bag (default 0)
                    max_share: float } ] in ONE battle, spend at most this
                                       share of what the bag held of it
                                       when the battle began (rounded
                                       down, never below one); a cap that
                                       fits five FULL_RESTOREs and ten
                                       POTIONs at once
  field_heal: { item: str, hp_below: float, prefer: str,
                reserve: int } | null
                             after a battle ends, if own hp frac < this and
                             the item is in the bag, use it in the field
                             (no turn cost) before travel resumes
  field_cure: [ { status: "PSN"|"PAR"|"BRN"|"SLP"|"FRZ", item: str,
                  prefer: str } ]
                             after a battle: cure the listed status with
                             the item if any party mon has it (field item
                             rules cover the WHOLE party, neediest first)

  AN ITEM NAME IS A STAGE OF THE GAME; A CLASS IS A DECISION. Anywhere a
  rule names an item it may name a CLASS instead, in lower case, and the
  interpreter resolves it against the bag AT THE MOMENT THE RULE FIRES:
      heal    POTION, SUPER_POTION, HYPER_POTION, MAX_POTION, FULL_RESTORE
      revive  REVIVE, MAX_REVIVE
      cure    the dedicated cure for that rule's status, then FULL_HEAL,
              then FULL_RESTORE. In `field_cure` the status is the rule's
              own; in `battle_items` it is whatever the ACTIVE mon is
              suffering, and the rule does not fire on a clean one (its
              hp_below is ignored: the status is the condition)
      ball    POKE_BALL, GREAT_BALL, ULTRA_BALL
  Each ladder runs weakest first. `prefer` says which rung is taken:
      weakest_sufficient  (default) the smallest one that covers the HP
                          missing; the largest held when none covers it.
                          For a cure, every rung cures, so this is the
                          dedicated one and the FULL_RESTORE is saved.
      best_available      the strongest one held
      weakest_available   the weakest one held, whatever the deficit
  A class rule cannot go inert the way a named one does: it dies only when
  the bag holds nothing of that kind at all. MASTER_BALL and SAFARI_BALL
  are outside the `ball` ladder on purpose — one of a kind and zone-bound
  are not choices a ladder should make for you; name them by hand.
  A class rule's max_uses counts USES OF THE RULE, not of each item it
  reaches for in turn.

  catch: { ball: str          a ball or the class "ball" (weakest held
           prefer: str          first) thrown at WILD mons during a CATCH
           first_ball: bool     (true: one ball on the first turn, before
                                any status move or weakening)
           throw_at_hp_frac:  subgoal. A wild that is not the named want is
             float (def 0.7)  run from; a sleep/paralysis move goes first on
           max_balls: int }   an unstatused foe; it weakens only with a move
                              whose damage has been SEEN and is under 45% of
                              the foe's current hp; it throws at or under
                              throw_at_hp_frac of the hp the foe appeared
                              with (capped at 0.4 with a named want) or when
                              nothing safe remains; after max_balls throws
                              with a named want it runs and leaves it alive.
                              ctx["ball_cap"] may lower max_balls (a throw
                              toward a later objective keeps a reserve).
  lead: { order: "healthiest"|"first_alive"|"highest_level"|"most_hp"|
                 "resists"|"best_matchup",
          vs: "trainer"|"wild"|"any" (default "trainer"),
          min_hp_frac: float }
                             WHO WALKS IN. Slot 1 starts every battle and
                             nothing outside a faint prompt reorders the
                             party, so a lead chewed up by the last fight
                             leads the next one too. This is settled in
                             the OVERWORLD, before the press, and costs no
                             turn — unlike `switch`, which costs the turn
                             and a free hit. There is no foe on screen
                             yet: the health and level orders read your
                             side only, and the TYPE orders read what
                             THIS ROOM has been seen to send out — a
                             gym's trainers all use its type and you
                             fight past them to reach its leader. A room
                             never fought is silent and they fall back to
                             health.
  replacement: { order: "healthiest"|"first_alive"|"resists"|
                          "best_matchup",
                 min_hp_frac: float }
                             when the active mon faints with a backup
                             alive, which party slot comes in.
                             resists      = takes least from the foe's own
                                            types; best_matchup = hits it
                                            hardest for what it takes.
                             Both read the foe's TYPES, not its moves,
                             which are not on screen until used, and the
                             bench member's OWN types, because a benched
                             mon's moves reach the observation without
                             theirs. min_hp_frac keeps a rule from sending
                             in something nearly dead; if nobody clears it,
                             it is ignored rather than obeyed.
                             Outside a fight there is no foe to read, and
                             the type orders fall back to healthiest.

choose(obs, spec, ctx) -> op dict for the executor. ctx carries per-battle
state the executor owns: {"turn": n, "used": {move: count},
"intent": "fight"|"traversal"}. Reads only battle-visible fields.
"""

from __future__ import annotations

import json
from pathlib import Path

_CHART = json.loads((Path(__file__).parent / "type_chart.json").read_text())

# hand-seeded starting spec; a model authors/tunes this for the record run.
DEFAULT_SPEC = {
    "name": "typed_v0",
    "stab": 1.5,
    "accuracy_weight": True,
    "prefer_ko": True,
    "ko_margin": 1.0,
    "avoid_status_moves": True,
    "setup": [],
    "switch": [],
    "flee_wild": {"when_traversal": True, "hp_below": None},
    "battle_items": [],
    "field_heal": None,
    "field_cure": [],
    # functional placeholder so the plan's catch subgoal works under the
    # baseline spec too; the record run's values come from the model
    "catch": {"ball": "POKE_BALL", "throw_at_hp_frac": 0.7, "max_balls": 3},
    "replacement": {"order": "healthiest"},
    "lead": None,
}

_SPEC_KEYS = set(DEFAULT_SPEC) | {"name", "provenance"}   # provenance = metadata


# Moves that put a wild Pokemon to sleep or paralyse it: the two statuses the
# catch formula rewards most, and neither hurts the foe. Poison, burn and
# confusion are left out on purpose.
CATCH_STATUS_MOVES = {"SLEEP_POWDER", "STUN_SPORE", "THUNDER_WAVE", "HYPNOSIS",
                      "SING", "SPORE", "LOVELY_KISS", "GLARE"}

# ------------------------------------------------------------- item classes
# A RULE NAMING AN ITEM IS ONLY EVER RIGHT FOR ONE STAGE OF THE GAME. v1
# was authored in the Pewter arena, where POTION is what a party holds, and
# it named POTION in both of its healing rules; by Celadon the bag held
# three SUPER_POTIONs and neither rule could fire, so CHARIZARD walked into
# Erika at 17 of 116 hp and the run blacked out (2026-09-15). v6 was
# authored at the Elite Four and names HYPER_POTION, which no early party
# has ever seen; it would fail at Brock the same way, in the other
# direction. The decision the model is making — heal below this fraction,
# spend at most this many — is not stage-specific at all. Only the NAMES
# are. So a rule may name the kind and let the bag supply the name (user,
# 2026-08-24: "ONE BATTLE POLICY ACROSS STAGES, not one per stage").
#
# Each ladder is ordered WEAKEST FIRST, and holds only the items a player
# restocks. MASTER_BALL and SAFARI_BALL are left out: one of a kind and
# zone-bound, they are not a rung any ladder should climb on its own.
HEAL_LADDER = ("POTION", "SUPER_POTION", "HYPER_POTION", "MAX_POTION",
               "FULL_RESTORE")
REVIVE_LADDER = ("REVIVE", "MAX_REVIVE")
BALL_LADDER = ("POKE_BALL", "GREAT_BALL", "ULTRA_BALL")
CURE_LADDERS = {
    "PSN": ("ANTIDOTE", "FULL_HEAL", "FULL_RESTORE"),
    "PAR": ("PARLYZ_HEAL", "FULL_HEAL", "FULL_RESTORE"),
    "BRN": ("BURN_HEAL", "FULL_HEAL", "FULL_RESTORE"),
    "SLP": ("AWAKENING", "FULL_HEAL", "FULL_RESTORE"),
    "FRZ": ("ICE_HEAL", "FULL_HEAL", "FULL_RESTORE"),
}
ITEM_CLASSES = {"heal": HEAL_LADDER, "revive": REVIVE_LADDER,
                "ball": BALL_LADDER, "cure": ()}   # cure reads the status

# What the item says on its own description screen. MAX_POTION and
# FULL_RESTORE say "fully restores", which no deficit can exceed.
FULL = 10 ** 6
HEAL_AMOUNT = {"POTION": 20, "SUPER_POTION": 50, "HYPER_POTION": 200,
               "MAX_POTION": FULL, "FULL_RESTORE": FULL}

PREFERENCES = ("weakest_sufficient", "best_available", "weakest_available")
DEFAULT_PREFER = "weakest_sufficient"


# WHAT THIS RUN HAS ALREADY SPENT. `max_uses` is per battle and starts
# over with every trainer, and a gauntlet is five trainers on one bag:
# the real-path league (2026-09-15) spent all five FULL_RESTOREs on
# LORELEI's DEWGONG and BRUNO's ONIX — three and two, in every trial —
# and walked into LANCE with fainted bodies and nothing to use, exactly
# like the run it was copied from. Both rooms were won by the arm with
# NO items at all. Nothing in the spec could say "keep some" or "five
# for the whole way", so no authored spec could ration, whatever the
# model had learned. This dict is the run's ledger: the executor hands
# it to every battle and clears it when the party is made whole (a
# Center heal, a blackout), the arena runner clears it at every trial.
RUN_BUDGET: dict = {}


def reset_run_budget() -> None:
    """The party has been made whole: the run's item ledger starts over."""
    RUN_BUDGET.clear()


def bag_holds(name, bag, status=None) -> int:
    """How many of this item the bag holds — or, for a class, how many of
    every rung of its ladder together. What a `reserve` is measured
    against."""
    n = str(name or "")
    bag = bag or {}
    if not n:
        return 0
    if not is_item_class(n):
        return int(bag.get(n, 0) or 0)
    return sum(int(bag.get(i, 0) or 0) for i in class_ladder(n, status))


def is_item_class(name) -> bool:
    return str(name or "") in ITEM_CLASSES


def class_ladder(name, status=None) -> tuple:
    """The items a class stands for, weakest first."""
    n = str(name or "")
    if n == "cure":
        return CURE_LADDERS.get(str(status or "").upper(), ())
    return ITEM_CLASSES.get(n, ())


def resolve_item(name, bag, prefer=DEFAULT_PREFER, *, status=None,
                 missing=None) -> str:
    """The item this rule actually reaches for, given the bag RIGHT NOW.

    A literal name resolves to itself when carried and to "" when not —
    exactly what the call sites used to check by hand. A class resolves to
    a rung of its ladder, or "" when the bag holds no rung at all."""
    n = str(name or "")
    bag = bag or {}
    if not n:
        return ""
    if not is_item_class(n):
        return n if bag.get(n, 0) > 0 else ""
    held = [i for i in class_ladder(n, status) if bag.get(i, 0) > 0]
    if not held:
        return ""
    if prefer == "best_available":
        return held[-1]
    if prefer == "weakest_available":
        return held[0]
    # weakest_sufficient. With no deficit to measure — a revive, a cure,
    # anything whose rungs all do the whole job — the weakest rung IS the
    # sufficient one, and the strong medicine is kept for when it is not.
    if not missing:
        return held[0]
    for i in held:
        if HEAL_AMOUNT.get(i, FULL) >= missing:
            return i
    return held[-1]


def _prefer_problems(rule: dict, where: str) -> list:
    """`prefer` is only a choice where there is a ladder to choose on. A
    rule naming one item and preferring `best_available` is not wrong so
    much as confused about what it wrote, and saying so is cheaper than
    letting it believe the bag is being searched."""
    pref = rule.get("prefer")
    if pref is None:
        return []
    if pref not in PREFERENCES:
        return [f"{where}.prefer must be one of " + "/".join(PREFERENCES)]
    if not is_item_class(rule.get("item")):
        return [f"{where}.prefer only means something when the item is a "
                f"CLASS ({'/'.join(sorted(ITEM_CLASSES))}); "
                f"{rule.get('item')} names one item"]
    return []


def validate_spec(spec) -> list:
    """Return a list of problems (empty = valid)."""
    probs = []
    if not isinstance(spec, dict):
        return ["spec is not an object"]
    for k in spec:
        if k not in _SPEC_KEYS:
            probs.append(f"unknown key '{k}'")
    if "stab" in spec and not (isinstance(spec["stab"], (int, float))
                               and 1.0 <= spec["stab"] <= 2.0):
        probs.append("stab must be a number in [1.0, 2.0]")
    if "ko_margin" in spec and not (isinstance(spec["ko_margin"], (int, float))
                                    and spec["ko_margin"] >= 1.0):
        probs.append("ko_margin must be a number >= 1.0")
    for k in ("accuracy_weight", "prefer_ko", "avoid_status_moves"):
        if k in spec and not isinstance(spec[k], bool):
            probs.append(f"{k} must be true/false")
    if "switch" in spec:
        if not isinstance(spec["switch"], list):
            probs.append("switch must be a list")
        else:
            for i, r in enumerate(spec["switch"]):
                if not isinstance(r, dict) or not (
                        isinstance(r.get("to"), int)
                        or isinstance(r.get("to"), str)):
                    probs.append(f"switch[{i}] needs to=<party slot 1-6, "
                                 "or an order name>")
                    continue
                if isinstance(r["to"], int) and not (1 <= r["to"] <= 6):
                    probs.append(f"switch[{i}].to must be a slot in [1,6]")
                if r.get("vs") not in (None, "trainer", "wild", "any"):
                    probs.append(f"switch[{i}].vs must be trainer/wild/any")
                for fk, lo, hi in (("max_uses", 1, 6), ("first_turns", 1, 8),
                                   ("only_if_lead", 1, 6)):
                    if fk in r and r[fk] is not None and not (
                            isinstance(r[fk], int) and lo <= r[fk] <= hi):
                        probs.append(f"switch[{i}].{fk} must be int "
                                     f"in [{lo},{hi}]")
                if r.get("hp_below") is not None and not (
                        isinstance(r["hp_below"], (int, float))
                        and 0.0 <= r["hp_below"] <= 1.0):
                    probs.append(f"switch[{i}].hp_below must be 0.0-1.0")
                if r.get("out_of_pp") not in (None, True, False):
                    probs.append(f"switch[{i}].out_of_pp must be true/false")
    if "setup" in spec:
        if not isinstance(spec["setup"], list):
            probs.append("setup must be a list")
        else:
            for i, r in enumerate(spec["setup"]):
                if not isinstance(r, dict) or not r.get("move"):
                    probs.append(f"setup[{i}] needs a move name")
                    continue
                if r.get("vs") not in (None, "trainer", "wild", "any"):
                    probs.append(f"setup[{i}].vs must be trainer/wild/any")
                if "only_if_best_physical" in r and not isinstance(
                        r["only_if_best_physical"], bool):
                    probs.append(f"setup[{i}].only_if_best_physical must "
                                 "be true/false")
                for fk, lo, hi in (("max_uses", 1, 6), ("first_turns", 1, 8)):
                    if fk in r and not (isinstance(r[fk], int)
                                        and lo <= r[fk] <= hi):
                        probs.append(f"setup[{i}].{fk} must be int "
                                     f"in [{lo},{hi}]")
                if "min_hp_frac" in r and not (
                        isinstance(r["min_hp_frac"], (int, float))
                        and 0.0 <= r["min_hp_frac"] <= 1.0):
                    probs.append(f"setup[{i}].min_hp_frac must be in [0,1]")
    for i, r in enumerate(spec.get("switch") or []):
        if isinstance(r, dict) and isinstance(r.get("to"), str) \
                and r["to"] not in ("resists", "best_matchup",
                                    "healthiest", "first_alive"):
            probs.append(f"switch[{i}].to must be a slot 1-6 or one of "
                         "resists/best_matchup/healthiest/first_alive")
    if "battle_items" in spec:
        if not isinstance(spec["battle_items"], list):
            probs.append("battle_items must be a list")
        else:
            for i, r in enumerate(spec["battle_items"]):
                if not isinstance(r, dict) or not r.get("item"):
                    probs.append(f"battle_items[{i}] needs an item name")
                    continue
                probs += _prefer_problems(r, f"battle_items[{i}]")
                hb = r.get("hp_below")
                if hb is not None and not (isinstance(hb, (int, float))
                                           and 0.0 <= hb <= 1.0):
                    probs.append(f"battle_items[{i}].hp_below in [0,1]")
                if "max_uses" in r and not (isinstance(r["max_uses"], int)
                                            and 1 <= r["max_uses"] <= 6):
                    probs.append(f"battle_items[{i}].max_uses int in [1,6]")
                if "target" in r and r["target"] not in ("self", "fainted"):
                    probs.append(f"battle_items[{i}].target must be "
                                 "self/fainted")
                if "max_uses_run" in r and not (
                        isinstance(r["max_uses_run"], int)
                        and 1 <= r["max_uses_run"] <= 30):
                    probs.append(f"battle_items[{i}].max_uses_run int in "
                                 "[1,30]")
                if "reserve" in r and not (isinstance(r["reserve"], int)
                                           and 0 <= r["reserve"] <= 30):
                    probs.append(f"battle_items[{i}].reserve int in [0,30]")
                if "max_share" in r and not (
                        isinstance(r["max_share"], (int, float))
                        and not isinstance(r["max_share"], bool)
                        and 0.0 < r["max_share"] <= 1.0):
                    probs.append(f"battle_items[{i}].max_share in (0,1]")
    if "field_heal" in spec and spec["field_heal"] is not None:
        fh = spec["field_heal"]
        if not isinstance(fh, dict) or not fh.get("item"):
            probs.append("field_heal must be null or {item, hp_below}")
        else:
            probs += _prefer_problems(fh, "field_heal")
            hb = fh.get("hp_below")
            if hb is not None and not (isinstance(hb, (int, float))
                                       and 0.0 <= hb <= 1.0):
                probs.append("field_heal.hp_below in [0,1]")
            if "reserve" in fh and not (isinstance(fh["reserve"], int)
                                        and 0 <= fh["reserve"] <= 30):
                probs.append("field_heal.reserve int in [0,30]")
    if "field_cure" in spec:
        if not isinstance(spec["field_cure"], list):
            probs.append("field_cure must be a list")
        else:
            for i, r in enumerate(spec["field_cure"]):
                if not isinstance(r, dict) or not r.get("item") \
                        or r.get("status") not in ("PSN", "PAR", "BRN",
                                                   "SLP", "FRZ"):
                    probs.append(f"field_cure[{i}] needs status "
                                 "PSN/PAR/BRN/SLP/FRZ and an item")
                else:
                    probs += _prefer_problems(r, f"field_cure[{i}]")
    if "catch" in spec and spec["catch"] is not None:
        ca = spec["catch"]
        if not isinstance(ca, dict) or not ca.get("ball"):
            probs.append("catch must be null or {ball, throw_at_hp_frac, "
                         "max_balls}")
        else:
            probs += _prefer_problems({"item": ca.get("ball"),
                                       "prefer": ca.get("prefer")}, "catch")
            th = ca.get("throw_at_hp_frac")
            if th is not None and not (isinstance(th, (int, float))
                                       and 0.0 < th <= 1.0):
                probs.append("catch.throw_at_hp_frac in (0,1]")
            if "max_balls" in ca and not (isinstance(ca["max_balls"], int)
                                          and 1 <= ca["max_balls"] <= 10):
                probs.append("catch.max_balls int in [1,10]")
            if "first_ball" in ca and not isinstance(ca["first_ball"], bool):
                probs.append("catch.first_ball true or false")
    if "lead" in spec and spec["lead"] is not None:
        ld = spec["lead"]
        if not isinstance(ld, dict) or ld.get("order") not in LEAD_ORDERS:
            probs.append("lead must be null or {order, vs, min_hp_frac} "
                         "with order one of " + "/".join(LEAD_ORDERS))
        else:
            if ld.get("vs") not in (None, "trainer", "wild", "any"):
                probs.append("lead.vs must be trainer/wild/any")
            f = ld.get("min_hp_frac")
            if f is not None and not (isinstance(f, (int, float))
                                      and 0.0 <= float(f) <= 1.0):
                probs.append("lead.min_hp_frac float in [0,1]")
    if "replacement" in spec and spec["replacement"] is not None:
        rp = spec["replacement"]
        if not isinstance(rp, dict) or rp.get("order") not in (
                None, "healthiest", "first_alive", "resists", "best_matchup"):
            probs.append("replacement.order must be healthiest / first_alive "
                         "/ resists / best_matchup")
        elif rp.get("min_hp_frac") is not None:
            f = rp.get("min_hp_frac")
            if not (isinstance(f, (int, float)) and 0.0 <= float(f) <= 1.0):
                probs.append("replacement.min_hp_frac float in [0,1]")
    if "flee_wild" in spec:
        fw = spec["flee_wild"]
        if not isinstance(fw, dict):
            probs.append("flee_wild must be an object")
        else:
            if set(fw) - {"when_traversal", "hp_below"}:
                probs.append("flee_wild keys: when_traversal, hp_below")
            if "when_traversal" in fw and not isinstance(
                    fw["when_traversal"], bool):
                probs.append("flee_wild.when_traversal must be true/false")
            hb = fw.get("hp_below")
            if hb is not None and not (isinstance(hb, (int, float))
                                       and 0.0 <= hb <= 1.0):
                probs.append("flee_wild.hp_below must be null or in [0,1]")
    return probs


def load_spec(path) -> dict:
    spec = json.loads(Path(path).read_text())
    probs = validate_spec(spec)
    if probs:
        raise ValueError(f"invalid spec {path}: {probs}")
    return spec


def effectiveness(move_type: str, foe_types) -> float:
    mult = 1.0
    for t in foe_types or []:
        mult *= _CHART.get(move_type, {}).get(t, 1.0)
    return mult


def incoming(foe_types, mine_types) -> float:
    """Worst multiplier the FOE's own types would land on this defender.

    The same chart `effectiveness` already reads, pointed the other way.
    It uses the foe's TYPES, not its moves, because a foe's moveset is not
    on screen until it uses them — STAB is the honest proxy and the spec
    prices it, the way it prices everything else."""
    return max((effectiveness(str(t).upper(), mine_types)
                for t in (foe_types or [])), default=1.0)


def outgoing(mon_or_types, foe_types) -> float:
    """Best multiplier this member could actually LAND on the foe.

    THE MOVES IT HOLDS, not the type it happens to be. GYARADOS is the
    right lead into LORELEI because it carries THUNDERBOLT, which is
    double against her WATER half; by typing alone WATER/FLYING reads
    neutral into ICE/WATER and it looks like nobody special (user,
    2026-09-12: "it should be considering the moves it has not just the
    types"). A move's type and power are on the SUMMARY screen for every
    party member, so this is eyesight, not inference — the shim publishes
    them for the bench as of the same day.

    Takes a party member, or a bare list of types for callers that have
    only those. A move with no power is not an attack and cannot land
    anything, so it is skipped; if NO move has a type (an older
    observation, or a mon whose moves have not been read), the member's
    own types stand in, which is what this did before.
    """
    if isinstance(mon_or_types, dict):
        mon, mine_types = mon_or_types, mon_or_types.get("types") or []
        best, seen = 0.0, False
        for mv in (mon.get("moves") or []):
            if not isinstance(mv, dict):
                continue
            t = mv.get("type")
            if not t:
                continue
            seen = True
            if (mv.get("power") or 0) <= 0:
                continue           # a status move lands no multiplier
            best = max(best, effectiveness(str(t).upper(), foe_types))
        if seen:
            return best
    else:
        mine_types = mon_or_types
    return max((effectiveness(str(t).upper(), foe_types)
                for t in (mine_types or [])), default=1.0)


def journal_key(move_id: str, species: str, level) -> tuple:
    return (move_id, species, level)


def observed_min_damage(journal: dict | None, move_id: str,
                        species: str, level) -> float | None:
    """Least damage this move has been SEEN to do to this species at our
    current level — the player's remembered experience (HP bars are on
    screen; no computed internals). None until observed."""
    obs = (journal or {}).get(journal_key(move_id, species, level))
    return min(obs) if obs else None


def _hp_frac(mon: dict) -> float:
    # The shim spells this TWO ways: party mons carry `max_hp` (shim.lua:206),
    # battle sides carry `maxhp` (shim.lua:649). Reading only `max_hp` here
    # meant every in-battle mon came back 1.0 — full health, always — so the
    # POTION rule, the HP flee and setup.min_hp_frac never once fired in
    # 64,218 logged battle turns. Read both; the whole log corpus, and every
    # replay run against it, uses the battle spelling.
    hp = mon.get("hp") or 0
    mx = mon.get("max_hp") or mon.get("maxhp") or 0
    return hp / mx if mx else 1.0


def punch(mon_or_types, foe_types) -> float:
    """What this member could actually DO to the foe: its best damaging
    move's power, with STAB and the chart, on a scale where a 100-power
    neutral hit without STAB is 1.0.

    THE MULTIPLIER ALONE PICKED THE WRONG LEAD. `outgoing` ranks the best
    chart multiplier a member can land, so KABUTOPS read "double" into
    LORELEI's DEWGONG on the strength of a 20-power ABSORB, tied LAPRAS,
    and kept the lead by standing first in line — then Hydro-Pumped a
    Water type for forty turns while Dewgong Rested (2026-09-15, every
    trial of the real-path league). Power and STAB are on the same summary
    screen the move's type is on. Falls back to `outgoing` for a bare
    type list or a bench whose moves carry no power."""
    if not isinstance(mon_or_types, dict):
        return outgoing(mon_or_types, foe_types)
    mon = mon_or_types
    mine = [str(t).upper() for t in (mon.get("types") or [])]
    best, seen = 0.0, False
    for mv in (mon.get("moves") or []):
        if not isinstance(mv, dict):
            continue
        power, mtype = mv.get("power") or 0, mv.get("type")
        if not power or not mtype:
            continue
        seen = True
        eff = effectiveness(str(mtype).upper(), foe_types)
        stab = 1.5 if str(mtype).upper() in mine else 1.0
        best = max(best, power / 100.0 * eff * stab)
    return best if seen else outgoing(mon, foe_types)


def score_move(mv: dict, me: dict, foe: dict, spec: dict,
               journal: dict | None = None) -> dict:
    mtype = mv.get("type")
    power = mv.get("power") or 0
    eff = effectiveness(mtype, foe.get("types"))
    stab = spec.get("stab", 1.5) if mtype in (me.get("types") or []) else 1.0
    acc = (mv.get("accuracy") or 100) / 100.0
    score = power * eff * stab
    if spec.get("accuracy_weight", True):
        score *= acc
    # KO detection is EMPIRICAL (pamphlet standard, no computed internals):
    # the least damage this move has been observed to do to this species at
    # our level, gated by the spec's ko_margin. Unseen matchup -> no KO call.
    seen = observed_min_damage(journal, mv.get("id"),
                               foe.get("species"), me.get("level"))
    kos = (seen is not None
           and seen >= (foe.get("hp") or 1e9) * spec.get("ko_margin", 1.0))
    return {
        "index": mv.get("index"), "id": mv.get("id"),
        "power": power, "eff": eff, "stab": stab,
        "damage": seen, "acc": acc, "score": score, "kos": kos,
    }


def should_field_heal(obs: dict,
                      spec: dict | None = None) -> tuple[str, int] | None:
    """After a battle: spec-rule field heal (no turn cost) for the NEEDIEST
    party mon below the threshold. Returns (item, slot) or None."""
    spec = spec or DEFAULT_SPEC
    fh = spec.get("field_heal")
    if not fh:
        return None
    if (obs or {}).get("mode") != "overworld":
        return None
    bag = (obs or {}).get("bag") or {}
    if not bag:
        return None
    # WHO NEEDS IT DECIDES WHAT IS REACHED FOR, so the neediest mon is
    # found first and the item resolved against ITS deficit.
    worst, slot, missing = 1.0, None, 0
    for i, mon in enumerate((obs or {}).get("party") or []):
        if (mon.get("hp") or 0) <= 0:
            continue
        f = _hp_frac(mon)
        if f < fh.get("hp_below", 0.5) and f < worst:
            worst, slot = f, i + 1
            missing = max(0, (mon.get("max_hp") or mon.get("maxhp") or 0)
                          - (mon.get("hp") or 0))
    if not slot:
        return None
    item = resolve_item(fh.get("item"), bag, fh.get("prefer")
                        or DEFAULT_PREFER, missing=missing)
    if item and bag_holds(fh.get("item"), bag) - 1 < int(fh.get("reserve") or 0):
        return None
    return (item, slot) if item else None


def should_field_cure(obs: dict,
                      spec: dict | None = None) -> tuple[str, int] | None:
    """After a battle: cure a statused party mon per the spec's rules.
    Returns (item, slot) or None."""
    spec = spec or DEFAULT_SPEC
    if (obs or {}).get("mode") != "overworld":
        return None
    bag = (obs or {}).get("bag") or {}
    if not bag:
        return None
    for i, mon in enumerate((obs or {}).get("party") or []):
        if (mon.get("hp") or 0) <= 0:
            continue
        status = mon.get("status")
        if status in (None, "", "0", "NONE", "OK"):
            continue
        for rule in spec.get("field_cure") or []:
            if rule.get("status") != status:
                continue
            item = resolve_item(rule.get("item"), bag,
                                rule.get("prefer") or DEFAULT_PREFER,
                                status=status)
            if item:
                return (item, i + 1)
    return None


def choose_replacement(obs: dict, spec: dict | None = None) -> int | None:
    """The active mon fainted: which party slot comes in (1-based).

    THE SPEC COULD ONLY EVER SAY "healthiest" OR "first_alive", and neither
    is about the fight. Run 16 replaced a fainted mon 86 times and every
    one of them was the healthiest rule; of 101 party reorders the model
    made itself, 96 said in their own words they were putting a low-level
    member in front to TRAIN it and none were about the matchup (user,
    2026-09-12: "it only switches around the team to put mons in first to
    train them"). Part of that is the round economy, which is not ours to
    fix here — but part was that the language had no words for it. The
    type chart has been in this file all along, read one way, for scoring
    our moves. `resists` and `best_matchup` read it the other way.

    Which order to use is the model's, as ever. This knows only how to
    carry out the four it can name.
    """
    spec = spec or DEFAULT_SPEC
    rp = spec.get("replacement") or {}
    order = rp.get("order", "healthiest")
    party = (obs or {}).get("party") or []
    alive = [(i + 1, m) for i, m in enumerate(party) if (m.get("hp") or 0) > 0]
    if not alive:
        return None
    if order == "first_alive":
        return alive[0][0]
    # A FLOOR, AND NEVER AN EMPTY BENCH. min_hp_frac stops a resist rule
    # sending in the one thing that walls the foe on 4% health — but if
    # nobody clears the floor, the floor is not a reason to send nobody.
    floor = rp.get("min_hp_frac")
    try:
        floor = float(floor) if floor is not None else 0.0
    except (TypeError, ValueError):
        floor = 0.0
    pool = [(n, m) for n, m in alive if _hp_frac(m) >= floor] or alive
    foe = (((obs or {}).get("battle") or {}).get("foe") or {})
    foe_types = foe.get("types") or []
    # ...AND A TYPE RULE WITH NOBODY TO READ falls back to health rather
    # than to an arbitrary slot. There is no foe on screen when the party
    # is being arranged outside a fight.
    if order in ("resists", "best_matchup") and not foe_types:
        order = "healthiest"

    def key(n_m):
        n, m = n_m
        types = [str(t).upper() for t in (m.get("types") or [])]
        f = _hp_frac(m)
        if order == "resists":
            # least damage taken; health breaks the tie
            return (-incoming(foe_types, types), f)
        if order == "best_matchup":
            # the MON, so outgoing can read the moves it actually holds
            # hits hardest for what it takes; health breaks the tie.
            # AN IMMUNITY IS BETTER THAN A DOUBLE RESIST, so the divisor
            # floors BELOW the chart's smallest real multiplier (0.25)
            # rather than at it — clamping 0 to 0.25 would price a mon the
            # foe cannot touch at all exactly like one it can hurt a
            # little. The floor exists to keep the ratio finite, nothing
            # more; gen 1's ladder is 0, 0.25, 0.5, 1, 2, 4.
            return (punch(m, foe_types)
                    / max(0.125, incoming(foe_types, types)), f)
        return (f, 0.0)

    return max(pool, key=key)[0]


LEAD_ORDERS = ("healthiest", "first_alive", "highest_level", "most_hp",
               "resists", "best_matchup")


def choose_lead(obs: dict, spec: dict | None = None,
                kind: str = "trainer", foe_types=None) -> int | None:
    """Which party slot should be in front when the next fight starts, or
    None to leave the party as it is.

    SLOT 1 STARTS EVERY BATTLE. Nothing outside a faint prompt reorders
    the party, so the mon the last fight chewed up leads the next one too
    — through a gym's whole chain of trainers and into its leader. The
    policy's only answer was `switch`, which costs the turn and hands the
    foe a free hit for it, and v7 spent 200 of them doing exactly that
    (2026-09-15, user: "before facing a gym leader or elite four member it
    should be pausing and choosing who to put first").

    This is settled in the overworld before the press, so it costs
    nothing — and it means there is no foe on screen. The health and
    level orders read your own side only. The TYPE orders read what this
    ROOM has been seen to send out: a gym's trainers all use its type,
    the run fights its way past them to reach the leader, and by then it
    has been told what the room is made of seven times over. A room never
    fought is silent and they fall back to health, the same rule
    `replacement` follows when there is no foe.

    Which order, and whether to have one at all, is the model's."""
    spec = spec or DEFAULT_SPEC
    ld = spec.get("lead")
    if not ld:
        return None
    vs = str(ld.get("vs") or "trainer")
    if vs != "any" and vs != kind:
        return None
    party = (obs or {}).get("party") or []
    alive = [(i + 1, m) for i, m in enumerate(party) if (m.get("hp") or 0) > 0]
    if len(alive) < 2:
        return None                 # nobody to choose between
    order = ld.get("order")
    if order == "first_alive":
        return alive[0][0]
    # A FLOOR, AND NEVER AN EMPTY BENCH — the same rule replacement uses:
    # if nobody clears it, it is ignored rather than obeyed into leading
    # with nobody.
    try:
        floor = float(ld.get("min_hp_frac") or 0.0)
    except (TypeError, ValueError):
        floor = 0.0
    pool = [(n, m) for n, m in alive if _hp_frac(m) >= floor] or alive
    ft = [str(t).upper() for t in (foe_types or [])]
    if order in ("resists", "best_matchup"):
        if not ft:
            order = "healthiest"        # nothing learned here yet
        elif order == "resists":
            return max(pool, key=lambda n_m: (
                -incoming(ft, [str(t).upper()
                               for t in (n_m[1].get("types") or [])]),
                _hp_frac(n_m[1])))[0]
        else:
            return max(pool, key=lambda n_m: (
                punch(n_m[1], ft)
                / max(0.125, incoming(ft, [str(t).upper()
                                           for t in (n_m[1].get("types")
                                                     or [])])),
                _hp_frac(n_m[1])))[0]
    if order == "highest_level":
        key = lambda n_m: (n_m[1].get("level") or 0, _hp_frac(n_m[1]))
    elif order == "most_hp":
        key = lambda n_m: (n_m[1].get("hp") or 0, _hp_frac(n_m[1]))
    else:
        key = lambda n_m: (_hp_frac(n_m[1]), n_m[1].get("level") or 0)
    return max(pool, key=key)[0]


def should_switch(obs: dict, spec: dict | None = None,
                  ctx: dict | None = None) -> int | None:
    """Spec-driven mid-battle switch: which party slot comes in, or None.

    The policy could only ever fight with whoever was sent out, so the one
    lever on who fights was party order, and a Pokemon too weak to survive
    a turn could never be in a battle at all. That rules out a whole class
    of play the game itself supports.

    WHAT THE HARNESS SUPPLIES IS THE VERB. This asks the spec — which the
    model writes (policy_author.py, CLAIM_RULES) — and does what it says.
    No rule here knows why a switch might be worth a turn; the reasons are
    the model's, and it has to write them down as conditions to get them.

    A switch costs the turn and gives the foe a free hit. That is a fact
    about the game, not a rule about play, and the model prices it.
    """
    spec = spec or DEFAULT_SPEC
    ctx = ctx or {}
    b = (obs or {}).get("battle") or {}
    me = b.get("me") or {}
    kind = b.get("kind") or "wild"
    party = (obs or {}).get("party") or []
    used = ctx.setdefault("switched", {})
    for n, rule in enumerate(spec.get("switch") or []):
        # A SLOT NUMBER IS A POSITION, NOT A POKEMON. `to: 3` is a
        # different animal in every party and at every hour of the same
        # run — v7 named slot 3 and it was a PIDGEY at Pewter, a
        # PIDGEOTTO at Vermilion and a FARFETCH'D at Celadon, so one rule
        # meant three unrelated things and could not be RIGHT about any
        # of them. The same mistake as naming POTION instead of a heal.
        # Mid-fight the foe IS on screen, which is exactly when the type
        # orders have something to read: `to: "best_matchup"` finds the
        # counter on the bench whoever it is and wherever it sits.
        to = rule.get("to")
        if isinstance(to, str):
            to = choose_replacement(obs, {"replacement": {
                "order": to, "min_hp_frac": rule.get("min_hp_frac")}})
        if not isinstance(to, int) or not (1 <= to <= len(party)):
            continue
        if used.get(n, 0) >= rule.get("max_uses", 1):
            continue
        # ...AND A RULE ABOUT RUNNING DRY CANNOT LIVE ON TURN 1. The turn
        # gate defaults to the first turn only, which is right for a lead
        # swap and fatal for a condition that by its nature arrives late:
        # "switch when I am out of PP" would have read correctly and
        # never fired once. An explicit first_turns is still obeyed.
        _gate = rule.get("first_turns")
        if _gate is None and not rule.get("out_of_pp"):
            _gate = 1
        if _gate is not None and (ctx.get("turn") or 1) > _gate:
            continue
        vs = rule.get("vs", "any")
        if vs != "any" and vs != kind:
            continue
        hb = rule.get("hp_below")
        if hb is not None and _hp_frac(me) >= hb:
            continue
        # A POKEMON WITH NOTHING LEFT TO THROW IS NOT IN THE FIGHT. When
        # every move is at 0 PP the game gives you Struggle, Struggle is
        # NORMAL, and NORMAL does nothing at all to a GHOST. VAPOREON ran
        # dry against AGATHA's GENGAR and the two of them stood there:
        # gen 1 enemies do not Struggle either (user, 2026-09-15: "i
        # forgot that enemy mons dont use struggle in gen1"), so the foe
        # stopped taking turns entirely and neither side could move a
        # point of HP. Fifty minutes, foe HP frozen at 74/151. The bench
        # was five deep and one of them was untouched.
        if rule.get("out_of_pp"):
            if any((m.get("pp") or 0) > 0 for m in (me.get("moves") or [])):
                continue
        lead = rule.get("only_if_lead")
        if lead is not None and ctx.get("started_as") != lead:
            continue
        cand = party[to - 1]
        # switching to a fainted slot is not a decision, it is a no-op the
        # game refuses — and a refused input burns the turn without ticking
        # anything, the DISABLE deadlock all over again
        if (cand.get("hp") or 0) <= 0:
            continue
        if cand.get("species") == me.get("species"):
            continue        # already out
        used[n] = used.get(n, 0) + 1
        return to
    return None


def should_flee(obs: dict, spec: dict | None = None,
                ctx: dict | None = None) -> bool:
    """Spec-driven wild-flee decision. Trainers can never be fled."""
    spec = spec or DEFAULT_SPEC
    ctx = ctx or {}
    b = obs.get("battle") or {}
    if b.get("kind") != "wild":
        return False
    fw = spec.get("flee_wild") or {}
    if fw.get("when_traversal") and ctx.get("intent") == "traversal":
        return True
    hb = fw.get("hp_below")
    if hb is not None and _hp_frac(b.get("me") or {}) < hb:
        return True
    return False


def choose(obs: dict, spec: dict | None = None,
           ctx: dict | None = None) -> dict:
    """Return a battle op. Falls back to slot-1 fight if no data."""
    spec = spec or DEFAULT_SPEC
    ctx = ctx or {}
    b = obs.get("battle") or {}
    me, foe = b.get("me") or {}, b.get("foe") or {}
    kind = b.get("kind") or "wild"
    # DISABLE makes a slot unselectable. Choosing it anyway is not a wasted
    # turn — the game refuses the input, so the turn never resolves and the
    # disable counter never ticks down: a permanent deadlock. pure26 sat in
    # one trainer battle re-picking a disabled SCRATCH against a 9 HP foe,
    # no EXP, HP frozen, for thousands of logged "turns". Play anything
    # legal (even GROWL) and Disable expires on its own.
    dis = me.get("disabledSlot") or 0
    moves = [m for m in (me.get("moves") or [])
             if (m.get("pp") or 0) > 0 and m.get("index") != dis]
    if not moves:
        # nothing legal left: Struggle, but never by re-picking the
        # disabled slot, which would deadlock again
        alt = next((m.get("index") for m in (me.get("moves") or [])
                    if m.get("index") != dis), 1)
        return {"op": "battle_move", "index": alt}
    # in-battle item rules come first: spending the turn to heal beats
    # fainting (the model's rule decides the threshold and budget)
    bag = obs.get("bag") or {}
    items_used = ctx.setdefault("items_used", {})
    # WHAT THE BAG HELD WHEN THIS BATTLE BEGAN, for max_share: a count
    # per fight cannot be right for five FULL_RESTOREs and ten POTIONs
    # at once (two a fight rationed the league and starved a lone
    # IVYSAUR at Misty, 2026-09-15); a share of the bag can.
    bag0 = ctx.setdefault("bag_at_start", dict(bag))
    for _i, rule in enumerate(spec.get("battle_items") or []):
        # A CLASS RULE SPENDS ITS BUDGET ON ITSELF, not on each rung it
        # reaches for in turn: `heal` with max_uses 3 is three heals, not
        # three POTIONs and then three SUPER_POTIONs. A rule naming one
        # item keeps counting by that name, so two rules naming the same
        # item still share a budget the way they always have.
        budget_key = (f"#{_i}:{rule.get('item')}"
                      if is_item_class(rule.get("item"))
                      else str(rule.get("item") or ""))
        if items_used.get(budget_key, 0) >= rule.get("max_uses", 2):
            continue
        # ...AND A RUN SPENDS ITS BUDGET ACROSS EVERY BATTLE IN IT. The
        # ledger is shared by every battle until the party is made whole
        # (see RUN_BUDGET); a rule without max_uses_run is uncapped there,
        # as every rule was before.
        run_used = ctx.get("items_used_run")
        if run_used is None:
            run_used = ctx["items_used_run"] = RUN_BUDGET
        _cap = rule.get("max_uses_run")
        if _cap and run_used.get(budget_key, 0) >= int(_cap):
            continue
        # A REVIVE IS FOR SOMEONE ELSE. Every rule gated on the ACTIVE
        # mon's HP and the op then targeted whoever was first in the
        # party, so "bring a fainted one back" could not be written at
        # all — and a party that loses bodies in a five-room gauntlet has
        # no other way to keep them (user, 2026-08-24: "its gotta use
        # those revives if it wants to win"). `target: "fainted"` fires
        # while ANY party member is down; the harness picks which.
        target = str(rule.get("target") or "self")
        missing = None
        # A CURE IN A FIGHT READS THE ACTIVE MON'S OWN STATUS. The class
        # existed only for `field_cure`, where the rule carries a status
        # to resolve against; written into `battle_items` it had none, so
        # it resolved to nothing and sat there dead however full the bag
        # was. The first spec authored with classes wrote exactly that
        # rule (v7, 2026-09-15) — it is the obvious thing to mean, and a
        # rule that can never fire whatever you carry is the bug this
        # whole DSL change exists to kill.
        _status = None
        if str(rule.get("item") or "") == "cure":
            # the status IS the condition here; hp_below is not read
            _status = str((me or {}).get("status") or "").upper()
            if _status in ("", "0", "NONE", "OK"):
                continue
        elif target == "fainted":
            if not any((p.get("hp") or 0) <= 0
                       for p in (obs.get("party") or [])):
                continue
        elif _hp_frac(me) >= rule.get("hp_below", 0.3):
            continue
        else:
            # A TURN SPENT HEALING 20 OF 180 IS A TURN GIVEN AWAY. The
            # deficit is what the ladder is measured against.
            missing = max(0, (me.get("max_hp") or me.get("maxhp") or 0)
                          - (me.get("hp") or 0))
        _share = rule.get("max_share")
        if _share:
            _held0 = bag_holds(rule.get("item"), bag0, _status)
            _allowed = max(1, int(float(_share) * _held0)) if _held0 else 0
            if items_used.get(budget_key, 0) >= _allowed:
                continue
        item = resolve_item(rule.get("item"), bag,
                            rule.get("prefer") or DEFAULT_PREFER,
                            status=_status, missing=missing)
        if not item:
            continue
        # A RESERVE IS WHAT YOU DO NOT SPEND HERE. The bag count is on
        # the screen; how many to hold back for the rooms ahead is the
        # rule's own number.
        if bag_holds(rule.get("item"), bag, _status) - 1 < int(rule.get("reserve") or 0):
            continue
        items_used[budget_key] = items_used.get(budget_key, 0) + 1
        run_used[budget_key] = run_used.get(budget_key, 0) + 1
        return {"op": "battle_item", "item": item, "target": target,
                "_why": (f"revive with {item}" if target == "fainted"
                         else f"cure {_status} with {item}" if _status
                         else f"heal with {item}")}
    scored = [score_move(m, me, foe, spec, ctx.get("journal")) for m in moves]
    damaging = [s for s in scored if (s["power"] or 0) > 0]
    # CATCH intent on a wild foe: run from what is not wanted, sleep or
    # paralyse first, weaken only with a seen move under 45% of current hp,
    # then throw (gen1 catch odds scale with missing hp and with status).
    # The foe's first-seen hp stands in for its max.
    ca = spec.get("catch")
    if ctx.get("intent") == "catch" and kind == "wild" and ca:
        # IS THIS EVEN THE THING WE CAME FOR? The catch branch checked only
        # that the foe was wild and a ball was in the bag, so a subgoal
        # reading "the party holds a WATER or GRASS type" threw at whatever
        # walked into it — a WEEDLE joined the party and the objective it
        # was authored for stayed unmet, with the balls meant for an Oddish
        # spent on bugs. `want` comes from the subgoal's own done_when
        # (species from has_species, types from party_type, read through
        # any_of); a goal that just wants MORE Pokemon sends None and
        # nothing changes. Run rather than fight: knocking it out is a
        # wasted battle either way, and the grass will offer another.
        want = ctx.get("want")
        if want:
            sp = str(foe.get("species") or "").upper()
            ty = {str(t).upper() for t in (foe.get("types") or [])}
            if not ((want.get("species") and sp in want["species"])
                    or (want.get("types") and ty & want["types"])):
                return {"op": "battle_run",
                        "_why": f"{sp or 'this'} is not what this subgoal "
                                f"is for"}
        hp0 = ctx.setdefault("foe_hp0", foe.get("hp") or 1)
        frac = (foe.get("hp") or 0) / max(1, hp0)
        balls = ctx.get("balls", 0)
        bag = obs.get("bag") or {}
        have_ball = resolve_item(ca.get("ball"), bag,
                                 ca.get("prefer") or DEFAULT_PREFER)
        # ...AND NEVER PAST THE RESERVE. A throw toward a LATER objective
        # (executor: _catch_ahead) may spend only the balls above what the
        # run keeps for the goal in hand; that number rides in ctx.
        _cap = ca.get("max_balls", 3)
        if ctx.get("ball_cap") is not None:
            _cap = min(_cap, int(ctx["ball_cap"]))
        if have_ball and balls < _cap:
            # A BALL LANDS ON A WEAKENED, SLEEPING OR PARALYSED POKEMON FAR
            # MORE OFTEN THAN ON A FRESH ONE. With a target named, this used
            # to clear every weakening move ("a wasted ball is recoverable
            # and a corpse is not" — the KO prediction was a guess) and threw
            # at full health: five Poke Balls at a 100% Doduo, none landed,
            # and the Spearows after it met an empty bag (run 16, 2026-09-08;
            # user: "i would be suprised if it weakened before throwing").
            # The corpse worry stands, so weakening is allowed only with a
            # move whose damage has been SEEN and is under half the foe's
            # current HP (a critical hit doubles, so still short of a KO); a
            # sleep or paralysis move comes first when the foe carries no
            # status (poison and burn are left alone: they chip toward a
            # faint). Nothing safe, or low enough already: throw.
            cur_hp = foe.get("hp") or 0
            # ONE BALL BEFORE ANYTHING ELSE, WHEN THE SPEC SAYS SO. A wild
            # ABRA knows only TELEPORT and leaves on its first move; a ball
            # goes before any move, so the throw on turn one is the only
            # throw there is, and a sleep move spent first catches nothing
            # (user, 2026-09-16: "the ideal catch is to initially throw a
            # single ball for runners then weaken/status before throwing
            # more balls"). Whether a runner is worth that ball is the
            # spec's call, so it is a rule the model writes, not a default.
            if ca.get("first_ball") and balls == 0:
                ctx["balls"] = 1
                return {"op": "throw_ball", "ball": have_ball,
                        "_why": "first_ball: one ball before anything else"}
            if not foe.get("status") and not ctx.get("status_tried"):
                st = [mv for mv in moves
                      if str(mv.get("id") or "").upper() in CATCH_STATUS_MOVES]
                if st:
                    ctx["status_tried"] = True
                    return {"op": "battle_move", "index": st[0]["index"],
                            "_why": f"{st[0]['id']} first — a sleeping or "
                                    f"paralysed Pokemon is far easier to catch"}
            safe = [s for s in damaging
                    if not s["kos"] and s.get("damage") is not None
                    and s["damage"] <= 0.45 * max(1, cur_hp)]
            safe.sort(key=lambda s: s["score"])
            throw_at = ca.get("throw_at_hp_frac", 0.7)
            if ctx.get("want"):
                throw_at = min(throw_at, ca.get("throw_at_hp_frac_wanted", 0.4))
            if frac <= throw_at or not safe:
                ctx["balls"] = balls + 1
                return {"op": "throw_ball", "ball": have_ball,
                        "_why": f"throw (foe at {frac:.0%}"
                                + (", nothing safe to weaken it with"
                                   if frac > throw_at else "") + ")"}
            return {"op": "battle_move", "index": safe[0]["index"],
                    "_why": f"weaken with {safe[0]['id']} (foe at {frac:.0%})"}
        # THE BALLS FOR THIS BATTLE ARE SPENT — AND KILLING IT IS THE ONE
        # OUTCOME THAT HELPS NOTHING. Falling through to normal move
        # selection meant a L32 CHARMELEON knocking out the very ODDISH the
        # subgoal was authored to catch, so the wild that finally matched
        # was destroyed and the hunt started over. Leave it alive: the
        # grass will offer another, and the party keeps its balls for it.
        # Only when a target was NAMED — a party_size goal that will take
        # anything has nothing to protect.
        if ctx.get("want") and have_ball is not None:
            return {"op": "battle_run",
                    "_why": "out of balls for this one; leave it alive"}
    by_index = {m.get("index"): m for m in moves}
    best_dmg = max(damaging, key=lambda s: s["score"]) if damaging else None
    best_is_physical = bool(
        best_dmg
        and (by_index.get(best_dmg["index"]) or {}).get("category")
        != "special")
    # deliberate setup-move rules come before damage ranking
    used = ctx.setdefault("used", {})
    for rule in spec.get("setup") or []:
        mid = rule.get("move")
        mv = next((m for m in moves if m.get("id") == mid), None)
        if not mv:
            continue
        if used.get(mid, 0) >= rule.get("max_uses", 1):
            continue
        if (ctx.get("turn") or 1) > rule.get("first_turns", 2):
            continue
        if _hp_frac(me) < rule.get("min_hp_frac", 0.5):
            continue
        vs = rule.get("vs", "trainer")
        if vs != "any" and vs != kind:
            continue
        if rule.get("only_if_best_physical") and not best_is_physical:
            continue
        used[mid] = used.get(mid, 0) + 1
        return {"op": "battle_move", "index": mv["index"],
                "_why": f"setup {mid} (use {used[mid]})"}
    pool = damaging or scored     # only status moves left -> use them
    if spec.get("avoid_status_moves", True) and damaging:
        pool = damaging
    if spec.get("prefer_ko", True):
        kos = [s for s in pool if s["kos"]]
        if kos:
            kos.sort(key=lambda s: -s["acc"])   # surest KO
            return {"op": "battle_move", "index": kos[0]["index"],
                    "_why": f"KO with {kos[0]['id']}"}
    pool.sort(key=lambda s: -s["score"])
    best = pool[0]
    return {"op": "battle_move", "index": best["index"],
            "_why": f"{best['id']} score={best['score']:.1f} eff={best['eff']}"}


SPECS = {"typed_v0": DEFAULT_SPEC}


if __name__ == "__main__":
    # smoke: score Squirtle's Tackle/Bubble vs a Rock/Ground Geodude
    demo = {"battle": {
        "kind": "trainer",
        "me": {"level": 10, "species": "SQUIRTLE", "types": ["WATER"],
               "hp": 20, "maxhp": 30,   # battle-side spelling, as the shim emits
               "stats": {"attack": 20, "special": 25, "defense": 18},
               "moves": [
                   {"index": 1, "id": "TACKLE", "type": "NORMAL", "power": 35,
                    "category": "physical", "accuracy": 95, "pp": 30},
                   {"index": 2, "id": "BUBBLE", "type": "WATER", "power": 20,
                    "category": "special", "accuracy": 100, "pp": 30}]},
        "foe": {"level": 10, "species": "GEODUDE",
                "types": ["ROCK", "GROUND"], "hp": 30,
                "stats": {"defense": 25, "special": 15}}}}
    print("cold (score only):", choose(demo))
    seen = {journal_key("BUBBLE", "GEODUDE", 10): [34, 31]}
    print("after observations:", choose(demo, ctx={"journal": seen}))
    tw = {"battle": dict(demo["battle"],
                         me=dict(demo["battle"]["me"], moves=demo["battle"]["me"]["moves"] + [
                             {"index": 3, "id": "TAIL_WHIP", "type": "NORMAL",
                              "power": 0, "category": "status",
                              "accuracy": 100, "pp": 30}]))}
    spec = dict(DEFAULT_SPEC,
                setup=[{"move": "TAIL_WHIP", "max_uses": 1, "vs": "any"}])
    ctx = {"turn": 1, "intent": "fight"}
    print(choose(tw, spec, ctx), "then", choose(tw, spec, dict(ctx, turn=2)))

#!/usr/bin/env python3
"""Model-authored battle policy: the model writes the SPEC, the game
referees it.

CLAIM_RULES: the battle-policy artifact must be authored by the local open
model. This driver runs that authoring loop:
  1. the model writes a spec in the battle_policy DSL (its Pokemon
     knowledge -> deterministic rules; knowledge-in-decisions-out),
  2. each candidate is evaluated LIVE on the run's decisive fights via
     RESEEDED checkpoint trials (the L5 rival fight; the forest gauntlet
     through Pewter Gym to Brock),
  3. results (win rates, blackouts, oracle agreement/damage-gap) feed back
     for revision. The oracle referees; it never plays.
The best spec is saved with provenance for executor.py --policy-spec.

Owns its own game process (fresh_run pattern). Usage:
  policy_author.py --rounds 4 --out plans/policy_model_v1.json
"""

from __future__ import annotations

import argparse
import atexit
import json
import re
import os
import re as _re
import signal
import subprocess
import sys
import time
from pathlib import Path

import battle_policy
import brock_probe
import executor as ex_mod
from bridge import Bridge, RUN

REPO = Path(__file__).resolve().parent.parent
LOG = RUN / "executor_log.jsonl"

DSL_DOC = """SPEC DSL (JSON object; every key optional; no other keys):
  name: short string naming your policy
  stab: number 1.0-2.0 — weight for same-type (STAB) moves in scoring
  accuracy_weight: true/false — weight move scores by accuracy
  prefer_ko: true/false — pick a move estimated to KO over raw score
  ko_margin: number >= 1.0 — only trust a KO if est. damage >= foe hp*this
  avoid_status_moves: true/false — never pick 0-power moves by score
  setup: list of deliberate status-move rules, each:
      {"move": "TAIL_WHIP", "max_uses": 1-6, "first_turns": 1-8,
       "min_hp_frac": 0.0-1.0, "vs": "trainer"|"wild"|"any",
       "only_if_best_physical": true/false}
    (use the move up to max_uses times, only in the battle's first
     first_turns turns, only while own hp fraction >= min_hp_frac,
     only against that battle kind; only_if_best_physical limits the rule
     to fights where our best damage move is PHYSICAL — a Defense-drop
     like TAIL_WHIP does nothing for a special move like BUBBLE)
  switch: list of mid-battle switch rules, each:
      {"to": 1-6, "first_turns": 1-8, "max_uses": 1-6,
       "vs": "trainer"|"wild"|"any", "hp_below": null or 0.0-1.0,
       "only_if_lead": null or 1-6}
    (bring party slot `to` in, in the battle's first `first_turns` turns,
     up to max_uses times, only against that battle kind, only while the
     ACTIVE mon's hp fraction is below hp_below if given, and only when
     the mon that STARTED the battle was slot only_if_lead. A switch
     costs the turn and the foe gets a free hit — whether that price is
     worth paying, and what you would be paying it FOR, is yours)
  flee_wild: {"when_traversal": true/false, "hp_below": null or 0.0-1.0}
    (when_traversal: flee wild battles while traveling to save HP;
     hp_below: also flee ANY wild when own hp fraction is below this.
     Trainers can never be fled. Fleeing can fail; after 3 fails we fight.)
  ITEM CLASSES — read this before writing any rule that names an item.
    Anywhere a rule takes an item you may write a CLASS in lower case
    instead, and the bag is searched when the rule FIRES:
      "heal"    POTION, SUPER_POTION, HYPER_POTION, MAX_POTION,
                FULL_RESTORE
      "revive"  REVIVE, MAX_REVIVE
      "cure"    the dedicated cure for that rule's status, then FULL_HEAL,
                then FULL_RESTORE
      "ball"    POKE_BALL, GREAT_BALL, ULTRA_BALL
    Add "prefer" to say which one is taken:
      "weakest_sufficient" (the default) the smallest one that covers the
        HP missing right now, the largest held when none covers it; for a
        cure, the dedicated one, saving the FULL_RESTORE
      "best_available"     the strongest one in the bag
      "weakest_available"  the weakest one in the bag, whatever is missing
    NAMING ONE ITEM IS HOW A RULE DIES. This policy plays the WHOLE game,
    from a bag of POTIONs to a bag of FULL_RESTOREs. v1 named POTION and
    by the Elite Four carried none, so `battle_item` fired ONCE in 6041
    battle turns while three MAX_REVIVEs sat in the bag; it named POTION
    again for the field and walked into Erika at 17 of 116 hp past three
    SUPER_POTIONs. v6 named HYPER_POTION, which no early party has ever
    seen, and would die at Brock the other way round. Your THRESHOLDS are
    the decision and they travel; the item names do not. Name a class.
  battle_items: list of in-battle heal rules, each:
      {"item": "heal", "prefer": "weakest_sufficient",
       "hp_below": 0.0-1.0, "max_uses": 1-6}
    (use the item — costing the turn — when own hp fraction is below
     hp_below; at most max_uses per battle, counted per RULE; only if the
     bag has something the rule can reach.
     A rule may add "target": "fainted" — then it fires while ANY party
     member is DOWN and brings one back ("revive") instead of firing on
     the active mon's own HP. A gauntlet with no Pokemon Center in it is
     lost by running out of BODIES, not only out of HP.)
  field_heal: null or {"item": "heal", "hp_below": 0.0-1.0,
                       "prefer": ...}
    (one rule only here — so a class, not a name you may run out of)
    (after a battle ends while traveling: if own hp fraction is below
     hp_below and the bag has something the rule can reach, use it in the
     FIELD — no turn cost — before walking on)
  field_cure: list of {"status": "PSN"|"PAR"|"BRN"|"SLP"|"FRZ",
                       "item": "cure"}
    (after a battle: cure that status if the bag has something for it —
     poison keeps draining HP every few steps until cured. Field item
     rules cover the WHOLE party, neediest mon first.)
  catch: {"ball": "ball", "throw_at_hp_frac": 0.0-1.0,
          "max_balls": 1-10}
    (during a CATCH task: weaken the wild mon with the gentlest non-KO
     move until it is below that fraction of the hp it appeared with,
     then throw — gen1 catch odds scale with missing hp)
  replacement: {"order": "healthiest"|"first_alive"|"resists"|"best_matchup",
                "min_hp_frac": 0.0-1.0}
    (when your active mon faints and a backup lives, which one comes in —
     a replacement instead of a blackout, which would HALVE your money.
     "resists" sends the one the foe's own types hurt least; "best_matchup"
     the one that hits it hardest for what it takes. Both weigh TYPES: the
     foe's, because its moves are not visible until it uses them, and on your
     side THE MOVES THAT MEMBER HOLDS -- a GYARADOS carrying THUNDERBOLT is
     the answer to a WATER foe that its own WATER/FLYING typing calls
     neutral. A move with no power lands nothing, and a member whose moves
     carry no type falls back to its own typing. "min_hp_frac" stops a type rule sending in something nearly
     dead — if nobody clears the floor it is ignored, never obeyed into
     sending nobody. Outside a fight there is no foe to read and the type
     orders fall back to healthiest.)"""

# ------------------------------------------------------- context, from evidence
# WHAT USED TO BE HERE. A hand-written CONTEXT block that told the model
# Brock's roster and levels, that Onix is Rock/Ground and weak to water, the
# rival's moveset, the Viridian Forest encounter table, and which items
# Viridian stocks versus Pewter and in what order to buy them. Per
# fresh_run.sh the spec authored under that prompt fights EVERY BATTLE OF THE
# RECORD RUN, which made it the widest claim breach in the runtime path: the
# open model was supposed to bring the Pokemon knowledge, and we were
# handing it the answers to the two fights the early game turns on.
#
# It was also, by then, describing a different run. It opened "Squirtle
# lead"; this run has led with a Charmander since the first morning.
#
# Everything below is assembled from the run's own battle log — foes it has
# actually met, damage it has actually watched land, deaths it has actually
# died. The model still brings the type chart, the mechanics and the
# judgment. We bring what happened.

_MOVE_RE = _re.compile(r"\b([A-Z][A-Z_]{2,})\b")


def _move_of(why: str):
    """The move a battle_turn line played. `why` is the policy's own reason
    string — "SCRATCH score=40.0 eff=1.0", "KO with BUBBLE", "setup
    TAIL_WHIP (use 1)" — and the move id is the one SHOUTED token in it."""
    m = _MOVE_RE.search(why or "")
    return m.group(1) if m else None


def battle_evidence(log_path: Path = None) -> dict:
    """Read the run's battle log into facts. Nothing here is knowledge about
    Pokemon Red; it is a transcript of this party's fights."""
    log_path = Path(log_path or LOG)
    foes: dict = {}          # species -> {"n", "lv_min", "lv_max"}
    dealt: dict = {}         # (move, foe species) -> [damage, ...]
    taken: dict = {}         # foe species -> [damage, ...]
    blackouts: list = []
    turns: list = []
    cur = None
    if not log_path.exists():
        return {"foes": foes, "dealt": dealt, "taken": taken,
                "blackouts": blackouts, "turns": turns, "battles": 0}
    battles = 0
    with open(log_path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            k = d.get("kind")
            if k == "battle_start":
                battles += 1
                sp, _, lv = (d.get("foe") or "").rpartition(" L")
                try:
                    lv = int(lv)
                except ValueError:
                    lv = None
                if sp:
                    e = foes.setdefault(sp, {"n": 0, "lv_min": lv,
                                             "lv_max": lv})
                    e["n"] += 1
                    if lv is not None:
                        e["lv_min"] = min(e["lv_min"] or lv, lv)
                        e["lv_max"] = max(e["lv_max"] or lv, lv)
                # OUR level too, or a damage range is unreadable: "EMBER vs
                # GEODUDE: 5-42" is one move at L9 and the same move at L33,
                # and a rule written off the top of that range walks into
                # fights it cannot win.
                mlv = (d.get("me") or "").split(" L")
                try:
                    mlv = int(mlv[1].split()[0]) if len(mlv) > 1 else None
                except ValueError:
                    mlv = None
                cur = {"foe": sp, "fhp": None, "mhp": None, "mv": None,
                       "mlv": mlv}
            elif k == "battle_turn" and cur:
                fhp, mhp = d.get("foe_hp"), d.get("me_hp")
                # ONLY THE MON THAT STARTED. battle_start names one level,
                # but a switch or a faint replacement puts a different
                # Pokemon on the field — and then GUST, which only PIDGEY
                # knows, gets filed under CHARMELEON's level. A switch op or
                # an HP bar that RISES means the active mon changed; from
                # there the level is unknown and gets recorded as such.
                # A faint replacement is logged as `pick_party`, not
                # `battle_switch` — that one omission filed sixteen PIDGEY
                # GUSTs under a level-19 CHARMELEON.
                if d.get("op") in ("battle_switch", "pick_party") or (
                        cur["mhp"] is not None and mhp is not None
                        and mhp > cur["mhp"]):
                    cur["mlv"] = None
                if cur["mv"] and cur["fhp"] is not None and fhp is not None:
                    dmg = cur["fhp"] - fhp
                    if dmg > 0:
                        dealt.setdefault((cur["mv"], cur["foe"]),
                                         []).append((dmg, cur["mlv"]))
                if cur["mhp"] is not None and mhp is not None:
                    hurt = cur["mhp"] - mhp
                    if hurt > 0:
                        taken.setdefault(cur["foe"], []).append(hurt)
                cur["fhp"], cur["mhp"] = fhp, mhp
                # only a MOVE can be credited with damage: "heal with POTION"
                # and "throw POKE_BALL" both carry a shouted token too
                cur["mv"] = (_move_of(d.get("why"))
                             if d.get("op") == "battle_move" else None)
            elif k == "battle_done":
                if d.get("turns"):
                    turns.append(d["turns"])
                cur = None
            elif k == "blackout":
                blackouts.append((d.get("subgoal"), d.get("respawn"),
                                  d.get("op")))
    return {"foes": foes, "dealt": dealt, "taken": taken,
            "blackouts": blackouts, "turns": turns, "battles": battles}


def evidence_context(obs: dict | None = None,
                     log_path: Path = None) -> str:
    """The brief the policy author is given: this run's own record."""
    ev = battle_evidence(log_path)
    out = ["THE RUN THIS POLICY PLAYS. Everything below is what this party "
           "has already been through — read out of its own battle log, not "
           "out of a book. The Pokemon knowledge is yours to bring."]

    party = (obs or {}).get("party") or []
    if party:
        out.append("\nYOUR PARTY AS IT STANDS:")
        for i, m in enumerate(party, 1):
            mv = ", ".join(str(x.get("id")) for x in (m.get("moves") or []))
            out.append(f"  {i}. {m.get('species')} L{m.get('level')} "
                       f"{m.get('hp')}/{m.get('max_hp')}hp"
                       + (f" — {mv}" if mv else ""))
    bag = (obs or {}).get("bag") or {}
    if bag:
        out.append("\nWHAT IS IN THE BAG (a rule that spends an item you do "
                   "not carry never fires): "
                   + ", ".join(f"{k} x{v}" for k, v in sorted(bag.items())))

    if ev["foes"]:
        top = sorted(ev["foes"].items(), key=lambda kv: -kv[1]["n"])[:14]
        rows = ", ".join(
            f"{sp} L{e['lv_min']}"
            + (f"-{e['lv_max']}" if e["lv_max"] != e["lv_min"] else "")
            + f" ({e['n']}x)" for sp, e in top)
        out.append(f"\nWHAT YOU HAVE ACTUALLY FOUGHT, most often first "
                   f"({ev['battles']} battles on record): {rows}.")
    if ev["turns"]:
        t = sorted(ev["turns"])
        med = t[len(t) // 2]
        out.append(f"A battle has run {med} turn{'' if med == 1 else 's'} at "
                   f"the median and {t[-1]} at the longest.")

    if ev["dealt"]:
        rows = sorted(ev["dealt"].items(), key=lambda kv: -len(kv[1]))[:14]
        out.append("\nDAMAGE YOUR MOVES HAVE BEEN SEEN TO DO (the HP bar is "
                   "on screen; this is what it moved by):")
        for (mv, sp), v in rows:
            dmg = [x for x, _l in v]
            lv = [l for _x, l in v if l is not None]
            span = (f" at your L{min(lv)}" + (f"-{max(lv)}"
                    if max(lv) != min(lv) else "")) if lv else ""
            out.append(f"  {mv} vs {sp}: {min(dmg)}-{max(dmg)} over "
                       f"{len(v)} use(s){span}")
    if ev["taken"]:
        rows = sorted(ev["taken"].items(),
                      key=lambda kv: -max(kv[1]))[:8]
        out.append("\nDAMAGE THEY HAVE DONE TO YOU, worst hitters first: "
                   + ", ".join(f"{sp} up to {max(v)}" for sp, v in rows)
                   + ".")

    if ev["blackouts"]:
        where: dict = {}
        for sg, respawn, _op in ev["blackouts"]:
            where[sg or "?"] = where.get(sg or "?", 0) + 1
        rows = ", ".join(f"{k} ({v}x)" for k, v in
                         sorted(where.items(), key=lambda kv: -kv[1])[:6])
        out.append(f"\nHOW THIS PARTY HAS DIED: {len(ev['blackouts'])} "
                   f"blackout(s) on record, during — {rows}. A blackout "
                   f"ends the leg wherever it happens.")
    else:
        out.append("\nThis party has no blackouts on record.")
    return "\n".join(out)


SYS_HEAD = ("You AUTHOR a Pokemon Red battle policy as a JSON SPEC in the "
            "DSL below. A deterministic interpreter executes your rules; "
            "you are writing the decision rules, not playing turns. Use "
            "your knowledge of gen-1 mechanics. Reply with ONLY the JSON "
            "spec object.\n\n")


def sys_prompt(obs: dict | None = None, log_path: Path = None) -> str:
    return SYS_HEAD + DSL_DOC + "\n\n" + evidence_context(obs, log_path)


def _parse_spec(text: str):
    dec = json.JSONDecoder()
    idx = text.find("{")
    while idx != -1:
        try:
            val, _ = dec.raw_decode(text, idx)
        except json.JSONDecodeError:
            idx = text.find("{", idx + 1)
            continue
        if isinstance(val, dict):
            return val
        idx = text.find("{", idx + 1)
    return None


# ------------------------------------------------------------- eval harness
class Gym:
    """Boots the game, replays the plan to capture eval checkpoints, then
    scores candidate specs with reseeded restore trials."""

    def __init__(self, plan_path: Path, run_id: str, model: str = "",
                 from_save: Path | None = None, arena: str = "brock",
                 trials: int = 3, arena_spec: Path | None = None):
        self.arena_spec = arena_spec
        self.plan_path = plan_path
        self.trials = max(1, int(trials))
        self.run_id = run_id
        self.model = model
        self.game = None
        self.rival_ok = False
        # THE ARENA HAS TO BE THE FIGHT YOU CARE ABOUT. This gym replays
        # plans/brock.json and scores candidates on the L5 rival and the
        # walk to the Boulder Badge, which is why v1 came back healing with
        # POTION below 30% — true of a Charmander, useless to a level-50
        # party carrying hyper potions, and `battle_item` fired ONCE in
        # 6041 battle turns as a result (user, 2026-08-24: "yeah we never
        # did make that policy v2"). `--from-save` boots an ISOLATED copy
        # of a real save — never the campaign's own game — and `--arena e4`
        # scores a candidate on the Elite Four instead.
        self.from_save = from_save
        self.arena = arena
        self.run_dir = RUN

    def _load_plan(self):
        self.plan = json.loads(self.plan_path.read_text())
        self.sgs = {s["id"]: s for s in self.plan["subgoals"]}

    def boot(self):
        self._load_plan()   # fresh copy: setup escalation mutates in-memory
        if (RUN / "obs.json").exists():
            (RUN / "obs.json").unlink()
        if self.from_save:
            # contract.py's isolation: own love identity, own bridge dir,
            # a COPY of the save. The campaign's game is untouchable.
            sys.path.insert(0, str(REPO / "tests"))
            from contract import start_game            # noqa: E402
            self.run_dir = REPO / "run/policyarena"
            self.game = start_game(self.run_dir, self.from_save, "200")
            os.environ["RED_BRIDGE_DIR"] = str(self.run_dir)
        else:
            self.game = subprocess.Popen(
                [str(REPO / "run.sh"), "200"], cwd=REPO,
                start_new_session=True)
        atexit.register(self.shutdown)
        for _ in range(60):
            if (self.run_dir / "obs.json").exists():
                break
            time.sleep(1)
        else:
            raise RuntimeError("game did not come up")
        self.b = Bridge(self.run_dir) if self.from_save else Bridge()
        ex_mod.SCORE_BATTLES = True
        # escalation available during SETUP only (plan_path=None: authored
        # fixes stay in-memory, the plan file is never touched by eval)
        self.ex = ex_mod.Executor(self.b, plan=self.plan, plan_path=None,
                                  can_escalate=bool(self.model),
                                  model=self.model, run_id=self.run_id)
        ex_mod.bootstrap(self.b, cont=bool(self.from_save))

    def shutdown(self):
        if self.game and self.game.poll() is None:
            try:
                os.killpg(self.game.pid, signal.SIGTERM)
            except Exception:
                pass

    # ------------------------------------------------------ the E4 arena
    E4_ROOMS = ["LORELEIS_ROOM", "BRUNOS_ROOM", "AGATHAS_ROOM",
                "LANCES_ROOM", "CHAMPIONS_ROOM"]
    # THE SCORE IS THE FLAGS. Counting map arrivals raced the champion's
    # win against Oak's Hall of Fame walk-in (the observation has no map
    # inside a screen), so a trial that beat all five could score 3. The
    # save's own beaten flags are in every observation, in every mode.
    E4_FLAGS = ["EVENT_BEAT_LORELEIS_ROOM_TRAINER_0",
                "EVENT_BEAT_BRUNOS_ROOM_TRAINER_0",
                "EVENT_BEAT_AGATHAS_ROOM_TRAINER_0",
                "EVENT_BEAT_LANCE", "EVENT_BEAT_CHAMPION_RIVAL"]

    def prepare_arena(self):
        """Checkpoint the save exactly as it stands, and score from there.

        THE SAVEPOINT IS THE CONTROL SURFACE (user, 2026-08-24: "can we
        just control everything from a savepoint?"). The first version of
        this walked back down the room chain and healed, which bakes an
        assumption about where the save sits into the gym; park the save
        where you want the trial to begin instead and this stays four
        lines. Whatever the save holds — which room, what HP, which party
        — is the arena, restored fresh for every candidate.
        """
        obs = self.ex.settle()
        here = ((obs or {}).get("map") or {}).get("id")
        party = [f"{p.get('species')} L{p.get('level')} "
                 f"{p.get('hp')}/{p.get('max_hp')}"
                 for p in (obs.get("party") or [])]
        print(f"[gym] arena: {here}")
        for p in party:
            print(f"[gym]   {p}")
        # ...AND KEPT, because a score is unreadable without the party that
        # produced it. v3 cleared EIGHT Elite Four rooms with no battle_items
        # rule and no field_heal at all, which reads as "healing is
        # unnecessary" until you see that the arena party leads with a
        # CHARIZARD L71 against a league that tops out in the low sixties —
        # it swept, and the spec was credited (user, 2026-09-12: "we must
        # have given it overlevelled mons if it was able to solve it without
        # item usage"). The number was never wrong; it was never legible.
        self.arena_party = list(party)
        self.arena_map = here
        # A GYM IS ONE ROOM WITH N TRAINERS IN IT, which is neither shape
        # the gym knew: `brock` replays a plan and `e4` walks room to room
        # by map id. The room's own objects are the list of fights in it,
        # counted here so a score can be read as a fraction of what was
        # standing when the trial started.
        # ...FROM THE ROOM'S OWN TABLE, not from the observation, which a
        # restored save has seen none of: `map.objects` comes back empty
        # at the door and a scorer reading it presses nobody and reports
        # 0 of 1. The trainers nearest the door come first, which is the
        # order a player crosses a gym in.
        self.arena_fights = [n for n, _x, _y in
                             sorted(room_roster(self.arena_map),
                                    key=lambda t: -t[2])]
        # WHAT WAS STANDING IS WHAT THE SAVE CLEARED. The gin spec that
        # built this arena lists exactly the beat-flags it reset, leader
        # included, so that list is both the denominator and the set of
        # flags a trial is allowed to score on — a gym guide in the
        # roster is someone to press, never someone to beat.
        self.arena_flags = []
        if self.arena_spec:
            try:
                _sp = json.loads(Path(self.arena_spec).read_text())
                self.arena_flags = [f for f in (_sp.get("clear_flags") or [])
                                    if str(f).startswith("EVENT_BEAT_")]
            except (OSError, ValueError) as e:
                print(f"[gym] arena spec unreadable ({e})")
        if self.arena == "gym":
            print(f"[gym] {len(self.arena_flags)} to beat, "
                  f"{len(self.arena_fights)} to press: "
                  + ", ".join(self.arena_fights))
        self.b.send("checkpoint_capture", token="eval_e4")
        self.rival_ok = False

    # A FLAG THAT FLIPPED IS A FIGHT THAT WAS WON, and the save keeps that
    # record itself in every observation, in every mode. Counting map
    # arrivals or trainer sprites cannot tell a win from a walk past.
    @staticmethod
    def _ok(r) -> bool:
        return bool(((r or {}).get("result") or {}).get("ok"))

    @staticmethod
    def _mid_sequence(r) -> bool:
        """A refusal that waiting fixes: the world is mid-sequence, not
        blocked. Nothing in the observation says so — mode reads
        overworld, ui is null, recent_text is None — only the op's own
        refusal does."""
        d = str(((r or {}).get("result") or {}).get("detail") or "")
        return "not in overworld" in d or "stuck in a menu" in d

    @staticmethod
    def _beaten(obs) -> set:
        return {f for f in ((obs or {}).get("flags") or [])
                if str(f).startswith("EVENT_BEAT_")}

    def eval_spec_gym(self, spec: dict, k: int = 3) -> dict:
        """One room, everyone in it. Press each trainer in turn and fight;
        the score is how many of the room's beat-flags come up.

        The leader is behind the others in most gym layouts, so the order
        the objects come in IS the order of the room, and a trial that
        cannot reach the back of it simply scores what it beat."""
        ex_mod.set_active_spec(spec)
        res = {"arena": "gym",
               "rival_wins": 0, "rival_trials": 0, "pewter": 0, "badge": 0,
               "gauntlet_trials": 0, "blackouts": 0, "agree": 0,
               "scored": 0, "dmg_gap": 0.0, "rival_detail": [],
               "gauntlet_detail": [], "beaten": 0, "bodies": 0.0,
               "standing": len(getattr(self, "arena_flags", []) or [])
               or len(getattr(self, "arena_fights", []) or []) or 1}
        for _ in range(k):
            r = self.b.send("checkpoint_restore", token="eval_e4",
                            reseed=True, force=True)
            rr = (r or {}).get("result") or {}
            if not rr.get("ok"):
                raise RuntimeError(f"arena restore failed: {rr.get('detail')}")
            res["gauntlet_trials"] += 1
            start = LOG.stat().st_size
            obs = self._ride(self.ex.settle())
            before = self._beaten(obs)
            # A RESTORED SAVE HAS SEEN NOTHING OF THE ROOM IT IS PARKED
            # IN, and a walk only paths through ground that has been on
            # screen — so every press failed with "no reachable tile
            # adjacent to target" and the first run of this scored 0/8
            # without a punch thrown. Crossing the room is the job: press
            # whoever is reachable, and when nobody is, walk to the
            # nearest edge of what has been seen so more of it comes into
            # view. A trainer whose line of sight the walk crosses starts
            # the fight without being pressed at all, which is most of
            # them.
            pressed, cut = set(), set()
            want = set(self.arena_flags)
            try:
                for _ in range(6 * len(self.arena_fights) + 8):
                    obs = self._ride(self.ex.settle())
                    here = ((obs or {}).get("map") or {}).get("id")
                    # A MAP WITH NO NAME IS NOT A MAP YOU LEFT. Pressing
                    # Pewter's gym guide left the observation mid-speech
                    # with map.id None, this read it as "carried out of
                    # the arena", broke on step 1 and scored the trial a
                    # blackout with two Pokemon standing and no punch
                    # thrown. Unnamed is unsettled; wait it out.
                    if here is None:
                        # A QUESTION LEFT OPEN IS NOT A WORLD MID-STEP.
                        # Pewter's gym guide offers to walk you to the
                        # top; the press came back ok with the box still
                        # up, `tap a` only reopened it, and the trial sat
                        # in that prompt for every iteration it had.
                        # Nobody in an arena wants an escort: say no.
                        if (obs or {}).get("mode") == "ui":
                            self.b.send("menu", index=2)
                        else:
                            self.b.send("wait", frames=30)
                        continue
                    if here != self.arena_map:
                        break        # blacked out, or carried out of it
                    if want and want <= self._beaten(obs):
                        break        # the room is beaten
                    hit = busy = False
                    for who in self.arena_fights:
                        if who in pressed:
                            continue
                        r = self.b.send("interact", name=who, answer="no")
                        if self._ok(r):
                            pressed.add(who)
                            hit = True
                            break
                        if self._mid_sequence(r):
                            busy = True
                            break
                    if busy:
                        # A TRAINER WHO HAS SPOTTED YOU IS ALREADY WALKING
                        # OVER, and until they arrive every op is refused
                        # "stuck in a menu/dialog" while the observation
                        # still reads a clean overworld with no box in it.
                        # The first version of this loop read that refusal
                        # as a wall, gave up at step 0 and scored the room
                        # 0/8 with the challenge pending on screen. It is
                        # not a wall; it is the fight starting.
                        self.b.send("wait", frames=30)
                        continue
                    if hit:
                        continue
                    fr = sorted(((obs.get("map") or {}).get("frontier")
                                 or []), key=lambda c: c.get("d") or 99)
                    for c in fr:
                        w = self.b.send("walk_to", x=c.get("x"),
                                        y=c.get("y"))
                        if self._ok(w):
                            hit = True
                            break
                        if self._mid_sequence(w):
                            busy = True
                            break
                    if not hit and not busy:
                        # ...AND THE BACK OF THIS ROOM IS BEHIND A BUSH.
                        # Celadon's gym pens its leader and her last three
                        # trainers inside a bed with two CUT_TREEs in it:
                        # every press came back "no reachable tile
                        # adjacent to target", the frontier was empty
                        # because everything reachable HAD been seen, and
                        # the trial stopped at 4 of 8 with Erika never
                        # fought — the one fight the arena exists for.
                        for o in ((obs.get("map") or {}).get("objects")
                                  or []):
                            if o.get("kind") != "cut_tree" \
                                    or not o.get("reachable") \
                                    or (o.get("x"), o.get("y")) in cut:
                                continue
                            cut.add((o.get("x"), o.get("y")))
                            c2 = self.b.send("field_move", move="CUT",
                                             x=o.get("x"), y=o.get("y"))
                            if self._ok(c2):
                                hit = True
                                break
                            if self._mid_sequence(c2):
                                busy = True
                                break
                    if busy:
                        self.b.send("wait", frames=30)
                        continue
                    if not hit:
                        break        # nobody in reach and nowhere to look
            except TimeoutError:
                pass
            obs = self._ride(self.ex.settle())
            for _ in range(6):
                if ((obs.get("map") or {}).get("id")):
                    break
                self.b.send("wait", frames=30)
                obs = self._ride(self.ex.settle())
            won = self._beaten(obs) - before
            if self.arena_flags:
                won &= set(self.arena_flags)
            alive = [p for p in (obs.get("party") or [])
                     if (p.get("hp") or 0) > 0]
            end = ((obs.get("map") or {}).get("id"))
            if end and end != self.arena_map:
                res["blackouts"] += 1
            res["beaten"] += len(won)
            # ...AND WITH HOW MUCH OF THE PARTY LEFT. Both specs swept
            # this room; one finished it with three bodies up and one
            # with two, which is the whole of what a healing rule buys
            # and is invisible in "8/8". It breaks ties, it never
            # outranks the objective.
            # A BLACKOUT HEALS THE PARTY, so the bodies left after one
            # read 5/5 — full marks for dying, the same trap the E4
            # arena's room counting fell into. A trial that ended
            # outside the arena left nobody standing in it.
            res["bodies"] += (0.0 if (end and end != self.arena_map) else
                              len(alive) / max(1, len(obs.get("party")
                                                      or [])))
            res["gauntlet_detail"].append(
                f"beat {len(won)}/{res['standing']} in {self.arena_map} "
                f"with {len(alive)}/{len(obs.get('party') or [])} standing"
                + ("" if end in (None, self.arena_map)
                   else f" (ended in {end})"))
            for d in self._log_delta(start):
                if d.get("kind") == "blackout":
                    res["blackouts"] += 1
                elif d.get("kind") == "oracle_score":
                    res["scored"] += 1
                    res["agree"] += 1 if d.get("agree") else 0
                    res["dmg_gap"] += d.get("dmg_gap") or 0.0
        return res

    def _ride(self, obs):
        """Fight until the overworld: an observation in battle carries no
        map, and the champion attacks on entry ("stopped in None")."""
        while (obs or {}).get("mode") == "battle":
            obs = self.ex.handle_battle({"id": "e4", "done_when": {}}, obs)
            obs = self.ex.settle()
        return obs

    def eval_spec_e4(self, spec: dict, k: int = 3) -> dict:
        """How far up the Elite Four does this policy get, from healed?"""
        ex_mod.set_active_spec(spec)
        res = {"arena": "e4",
               "rival_wins": 0, "rival_trials": 0, "pewter": 0, "badge": 0,
               "gauntlet_trials": 0, "blackouts": 0, "agree": 0,
               "scored": 0, "dmg_gap": 0.0, "rival_detail": [],
               "gauntlet_detail": [], "rooms": 0, "bodies": 0.0}
        for _ in range(k):
            r = self.b.send("checkpoint_restore", token="eval_e4",
                            reseed=True, force=True)
            rr = (r or {}).get("result") or {}
            if not rr.get("ok"):
                raise RuntimeError(f"arena restore failed: {rr.get('detail')}")
            res["gauntlet_trials"] += 1
            start = LOG.stat().st_size
            got = 0
            cleared = 0
            try:
                for _ in range(len(self.E4_ROOMS)):
                    obs = self._ride(self.ex.settle())
                    here = ((obs or {}).get("map") or {}).get("id")
                    if here not in self.E4_ROOMS:
                        break            # blacked out, or fell out of the run
                    got = max(got, self.E4_ROOMS.index(here) + 1)
                    # THE LEADER IS AN NPC AND YOU CANNOT WALK ONTO ONE.
                    # This walked to (5,2), which is exactly where Bruno
                    # STANDS, so the walk failed, no fight started, and
                    # every trial scored "reached room 2" without a single
                    # punch thrown. Press him instead.
                    boss = next((o.get("name") for o in
                                 ((obs.get("map") or {}).get("objects") or [])
                                 if o.get("kind") in ("trainer", "npc")
                                 and o.get("name")), None)
                    if boss:
                        self.b.send("interact", name=boss)
                        obs = self.ex.settle()
                    obs = self._ride(obs)
                    # the champion has no next room: he counts when his
                    # flag is up and the party still stands
                    if here == self.E4_ROOMS[-1]:
                        if "EVENT_BEAT_CHAMPION_RIVAL" in (obs.get("flags") or []):
                            cleared += 1
                        break
                    # beaten? the north door opens. A ROOM IS CLEARED ONLY
                    # BY WALKING INTO THE NEXT ONE. Counting any map change
                    # counted DYING as progress: a blackout warps the party
                    # to the lobby and heals it, so the policy with
                    # `battle_items: []` — no healing at all — scored 8/15
                    # while every trial ended "in INDIGO_PLATEAU_LOBBY with
                    # 6/6 standing" from an arena that starts with two
                    # fainted (2026-08-24). Fastest to die, highest score.
                    want = self.E4_ROOMS[self.E4_ROOMS.index(here) + 1] \
                        if here != self.E4_ROOMS[-1] else None
                    # every E4 room exits at (4,0)/(5,0) except Lance's,
                    # whose north warps sit at (5,0)/(6,0) (story.lua): with
                    # a fixed (4,0) a beaten Lance never counted (2026-08-24)
                    self.b.send("use_warp", x=5, y=0)
                    obs = self._ride(self.ex.settle())
                    nxt = ((obs or {}).get("map") or {}).get("id")
                    if not want or nxt != want:
                        break            # the leader stands, or we were
                        # carried out of the gauntlet altogether
                    cleared += 1
            except TimeoutError:
                pass
            obs = self._ride(self.ex.settle())
            alive = [p for p in (obs.get("party") or [])
                     if (p.get("hp") or 0) > 0]
            flags = set(obs.get("flags") or [])
            cleared = sum(1 for f in self.E4_FLAGS if f in flags)
            champion = self.E4_FLAGS[-1] in flags
            # ...AND LANDING OUTSIDE THE ROOMS IS A LOSS, not a finish
            # (a blackout warps to the lobby); the champion's win ends in
            # the Hall of Fame, which is a screen, not a map
            _end = ((obs.get("map") or {}).get("id"))
            if not champion and _end not in self.E4_ROOMS:
                res["blackouts"] += 1
            res["rooms"] += cleared
            res["bodies"] += (0.0 if (not champion
                                      and _end not in self.E4_ROOMS)
                              else len(alive)
                              / max(1, len(obs.get("party") or [])))
            res["gauntlet_detail"].append(
                f"beat {cleared}/5 ({'CHAMPION' if champion else 'stopped in ' + str(_end)}) "
                f"with {len(alive)}/{len(obs.get('party') or [])} standing")
            for d in self._log_delta(start):
                if d.get("kind") == "blackout":
                    res["blackouts"] += 1
                elif d.get("kind") == "oracle_score":
                    res["scored"] += 1
                    res["agree"] += 1 if d.get("agree") else 0
                    res["dmg_gap"] += d.get("dmg_gap") or 0.0
        return res

    def prepare(self):
        """Replay the plan, capturing eval checkpoints at the two decisive
        fights. Stops before reach_pewter_city."""
        for sg in self.plan["subgoals"]:
            if sg["id"] == "battle_rival_lab":
                self.b.send("checkpoint_capture", token="eval_rival")
            if sg["id"] == "reach_pewter_city":
                self.b.send("checkpoint_capture", token="eval_gate")
                break
            ok = self.ex.run_subgoal(sg)
            if not ok and self.model:
                print(f"[gym] setup: escalating {sg['id']}")
                success, ops = self.ex.escalate(sg)
                if success:
                    if ops:              # in-memory only; [] is not a route
                        sg["macro"] = ops
                    ok = True
            if not ok:
                raise RuntimeError(f"setup failed at {sg['id']}")
        # verify the rival fight re-arms after a reseeded restore: some
        # event state may not be in the checkpoint
        self.b.send("checkpoint_restore", token="eval_rival", reseed=True)
        obs = self.ex.settle()
        flags = obs.get("flags") or []
        self.rival_ok = "EVENT_BATTLED_RIVAL_IN_OAKS_LAB" not in flags
        # leave the game parked on the gate checkpoint between candidates
        self.b.send("checkpoint_restore", token="eval_gate", reseed=True)

    def _log_delta(self, start: int):
        out = []
        with open(LOG) as f:
            f.seek(start)
            for line in f:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return out

    def _lead(self, obs):
        return ((obs or {}).get("party") or [{}])[0]

    def _run_or_author(self, sg) -> bool:
        """Mirror record-config behavior inside eval trials: replay the
        macro; on failure, escalate ONCE per eval session (in-memory) —
        e.g. the shop leg ends inside the mart and the next subgoal's
        macro assumes the street (itemauthor5: every trial died 'entering
        the gym')."""
        ok = self.ex.run_subgoal(sg)
        if not ok and self.model and not sg.get("_esc_tried"):
            sg["_esc_tried"] = True
            succ, ops = self.ex.escalate(sg)
            if succ:
                # AN EMPTY SEQUENCE IS NOT A ROUTE — same rule as
                # Executor.distill. Escalation can succeed having proposed
                # nothing (the pathfinder walked it, a fight settled it),
                # and writing that back makes trials 2 and 3 replay a macro
                # of no ops, which changes nothing and then fails.
                if ops:
                    sg["macro"] = ops
                ok = True
        return ok

    def score(self, spec: dict) -> dict:
        """Whichever arena this gym was built for."""
        if self.arena == "gym":
            return self.eval_spec_gym(spec, k=self.trials)
        if self.arena == "e4":
            return self.eval_spec_e4(spec, k=self.trials)
        return self.eval_spec(spec)

    def eval_spec(self, spec: dict, k_rival: int = 6,
                  k_gauntlet: int = 3) -> dict:
        ex_mod.set_active_spec(spec)
        res = {"arena": "brock", "rival_wins": 0, "rival_trials": 0,
               "pewter": 0, "badge": 0, "gauntlet_trials": 0,
               "blackouts": 0, "agree": 0, "scored": 0, "dmg_gap": 0.0,
               "rival_detail": [], "gauntlet_detail": []}
        if self.rival_ok:
            for _ in range(k_rival):
                self.b.send("checkpoint_restore", token="eval_rival",
                            reseed=True)
                res["rival_trials"] += 1
                try:
                    self.ex.run_subgoal(self.sgs["battle_rival_lab"])
                except TimeoutError:
                    res["rival_detail"].append("timeout")
                    continue
                lead = self._lead(self.ex.settle())
                won = (lead.get("level") or 0) >= 6
                res["rival_wins"] += 1 if won else 0
                res["rival_detail"].append(
                    f"{'W' if won else 'L'} (ended {lead.get('hp')}/"
                    f"{lead.get('max_hp')} hp)")
        for _ in range(k_gauntlet):
            self.b.send("checkpoint_restore", token="eval_gate", reseed=True)
            res["gauntlet_trials"] += 1
            start = LOG.stat().st_size
            stopped = None
            try:
                if self._run_or_author(self.sgs["reach_pewter_city"]):
                    res["pewter"] += 1
                    shop = self.sgs.get("buy_pewter_potions")
                    if shop:
                        self._run_or_author(shop)
                    if self._run_or_author(self.sgs["enter_pewter_gym"]):
                        if not self._run_or_author(self.sgs["defeat_brock"]):
                            stopped = "the BROCK fight"
                    else:
                        stopped = "entering the gym"
                else:
                    stopped = "the forest crossing"
            except TimeoutError:
                stopped = "a timeout"
            obs = self.ex.settle()
            lead = self._lead(obs)
            badge = "BOULDERBADGE" in ((obs or {}).get("badges") or [])
            res["badge"] += 1 if badge else 0
            res["gauntlet_detail"].append(
                ("BADGE" if badge else f"FAILED at {stopped}")
                + f" (lead ended {lead.get('hp')}/{lead.get('max_hp')} hp)")
            for d in self._log_delta(start):
                if d.get("kind") == "blackout":
                    res["blackouts"] += 1
                elif d.get("kind") == "oracle_score":
                    res["scored"] += 1
                    res["agree"] += 1 if d.get("agree") else 0
                    res["dmg_gap"] += d.get("dmg_gap") or 0.0
        return res


def feedback_text(name: str, r: dict) -> str:
    ag = f"{r['agree']}/{r['scored']}" if r["scored"] else "n/a"
    if r.get("arena") == "gym" or r.get("standing"):
        n = max(1, r.get("gauntlet_trials", 1))
        out = (f"{name}: beat {r.get('beaten', 0)}/"
               f"{n * (r.get('standing') or 1)} of the room across "
               f"{n} trial(s), blackouts {r['blackouts']}; oracle "
               f"agreement {ag}, damage left on the table {r['dmg_gap']:.0f}")
        for i, g in enumerate(r.get("gauntlet_detail") or []):
            out += f"\n  trial {i+1}: {g}"
        return out
    rv = (f"{r['rival_wins']}/{r['rival_trials']}" if r["rival_trials"]
          else "not evaluable")
    if r.get("rooms") or r.get("gauntlet_detail") and not r.get("pewter") \
            and not r.get("rival_trials"):
        # the E4 arena measures one thing: how far up the rooms it got
        n = max(1, r.get("gauntlet_trials", 1))
        out = (f"{name}: Elite Four rooms cleared "
               f"{r.get('rooms', 0)}/{n * 5} across {n} trial(s), "
               f"blackouts {r['blackouts']}; oracle agreement {ag}, "
               f"damage left on the table {r['dmg_gap']:.0f}")
        for i, g in enumerate(r.get("gauntlet_detail") or []):
            out += f"\n  trial {i+1}: {g}"
        return out
    out = (f"{name}: rival wins {rv}; gauntlet: reached Pewter "
           f"{r['pewter']}/{r['gauntlet_trials']}, Boulder Badge "
           f"{r['badge']}/{r['gauntlet_trials']}, blackouts "
           f"{r['blackouts']}; oracle agreement {ag}, damage left on "
           f"the table {r['dmg_gap']:.0f}")
    if r.get("rival_detail"):
        out += "\n  rival trials: " + "; ".join(r["rival_detail"])
    for i, g in enumerate(r.get("gauntlet_detail") or []):
        out += f"\n  gauntlet trial {i+1}: {g}"
    return out


def rank_key(r: dict):
    # ROOMS is the E4 arena's own measure and is absent from a brock run,
    # so it simply sorts first when it is there.
    return (r.get("rooms", 0), r.get("beaten", 0), r["badge"], r["pewter"],
            r["rival_wins"] / max(1, r["rival_trials"]),
            -r["blackouts"], -r["dmg_gap"])


# ------------------------------------------------ one spec, the whole game
# THE ARENAS MEASURE DIFFERENT THINGS AND CANNOT BE ADDED AS THEY STAND:
# rooms cleared, trainers beaten, a badge, six rival fights. Each is turned
# into the FRACTION OF ITS OWN OBJECTIVE the spec reached, and those add.
# A spec scored in three arenas can therefore be compared with one scored
# in three others, and a spec that wins one arena by dying fast in the rest
# cannot hide behind a number that only that arena produces.
def arena_fraction(r: dict) -> float:
    t = max(1, r.get("gauntlet_trials") or 0)
    a = r.get("arena") or ("e4" if "rooms" in r else "brock")
    if a == "gym":
        return r.get("beaten", 0) / (t * max(1, r.get("standing") or 1))
    if a == "e4":
        return r.get("rooms", 0) / (t * 5)
    # the Brock arena runs two trials of different kinds and they weigh
    # the same: the badge at the end of the walk, and the rival
    badge = r.get("badge", 0) / t
    rival = r.get("rival_wins", 0) / max(1, r.get("rival_trials") or 1)
    return (badge + rival) / 2


def cross_key(rows) -> tuple:
    """rows: [(arena name, result)]. Higher is better."""
    return (round(sum(arena_fraction(r) for _, r in rows), 6),
            -sum(r.get("blackouts", 0) for _, r in rows),
            round(sum((r.get("bodies") or 0.0)
                      / max(1, r.get("gauntlet_trials") or 1)
                      for _, r in rows), 4),
            -sum(r.get("dmg_gap", 0.0) for _, r in rows))


def cross_text(name: str, rows) -> str:
    out = [f"{name}: fit across {len(rows)} arena(s), "
           f"total {sum(arena_fraction(r) for _, r in rows):.2f} of "
           f"{len(rows)}.00"]
    for an, r in rows:
        out.append(f"  {an}: {arena_fraction(r):.0%} of that arena, "
                   f"blackouts {r.get('blackouts', 0)}, party left "
                   f"{(r.get('bodies') or 0.0) / max(1, r.get('gauntlet_trials') or 1):.0%}")
        for g in (r.get("gauntlet_detail") or []):
            out.append(f"    {g}")
        if r.get("rival_detail"):
            out.append("    rival: " + "; ".join(r["rival_detail"]))
    return "\n".join(out)


# THE ARENAS, BY NAME. Each is a savepoint parked where the fight starts
# (plans/arena_midgame.README.md has how they were built and what is on
# each shelf); `brock` is the one that replays a plan from a new game.
ARENAS = {
    "brock": ("brock", None, None),
    # The Pewter tier as a ROOM, not as a replay: `brock` replays a plan
    # from a new game and writes into the campaign's own run directory,
    # which is not a thing to do while a checkpoint is sitting in it.
    # Same party, same gym, in its own bridge dir like the others.
    "pewter": ("gym", REPO / "run/arena_brock_gym.lua",
               REPO / "plans/arena_brock_gym.json"),
    "erika": ("gym", REPO / "run/arena_erika.lua",
              REPO / "plans/arena_erika.json"),
    "koga": ("gym", REPO / "run/arena_koga.lua",
             REPO / "plans/arena_koga.json"),
    "e4": ("e4", REPO / "run/arena_e4.lua", None),
}


# WHO IS STANDING IN THE ROOM IS NOT IN THE OBSERVATION. A restored save
# has SEEN nothing of the room it is parked in, so `map.objects` comes
# back empty and a scorer reading it presses nobody and reports 0/1. The
# room's own object table is in the engine's map data, and `interact`
# resolves a name against the LIVE npc list, not against what has been
# seen — so the roster can be read here and pressed by name. Check-side
# only: this never reaches a prompt, and nothing the model plays with is
# told where anyone stands.
def room_roster(map_id: str) -> list:
    """[(name, x, y)] for one map, from the engine's own map table."""
    src = Path.home() / "Developer/gen1recomp/data/generated/maps.lua"
    try:
        txt = src.read_text(errors="ignore")
    except OSError:
        return []
    m = re.search(r"\n  " + re.escape(str(map_id)) + r" = \{", txt)
    if not m:
        return []
    i, depth = m.end() - 1, 0
    for j in range(i, len(txt)):
        if txt[j] == "{":
            depth += 1
        elif txt[j] == "}":
            depth -= 1
            if depth == 0:
                break
    blk = txt[i:j + 1]
    o = re.search(r"objects = \{", blk)
    if not o:
        return []
    i2, depth = o.end() - 1, 0
    for j2 in range(i2, len(blk)):
        if blk[j2] == "{":
            depth += 1
        elif blk[j2] == "}":
            depth -= 1
            if depth == 0:
                break
    out = []
    for e in re.finditer(r"\{(.*?)\}", blk[i2:j2 + 1], re.S):
        body = e.group(1)
        nm = re.search(r'name = "([A-Z0-9_]+)"', body)
        # `index = 1` ends in "x = 1"; the coordinate needs its own word
        x = re.search(r"\bx = (\d+)", body)
        y = re.search(r"\by = (\d+)", body)
        if nm and x and y:
            out.append((nm.group(1), int(x.group(1)), int(y.group(1))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--out", type=Path,
                    default=REPO / "plans/policy_model_v1.json")
    ap.add_argument("--plan", type=Path, default=REPO / "plans/brock.json")
    ap.add_argument("--model", default="gemma4:31b-it-q4_K_M")
    ap.add_argument("--run-id", default="policyauthor")
    ap.add_argument("--eval-only", type=Path, default=None,
                    help="skip authoring: evaluate this spec artifact (plus "
                         "the baseline) and report")
    ap.add_argument("--from-save", type=Path, default=None,
                    help="boot an ISOLATED COPY of this save and use it as "
                         "the arena, instead of replaying --plan. Make one "
                         "with planner/make_savepoint.py")
    ap.add_argument("--arena", default="brock",
                    choices=("brock", "e4", "gym"),
                    help="brock: the L5 rival and the Boulder Badge run. "
                         "e4: how far up the Elite Four a candidate gets "
                         "from the savepoint. gym: one room, everyone in "
                         "it, from the savepoint")
    ap.add_argument("--arenas", default=None,
                    help="score every candidate in EACH of these, comma "
                         "separated (" + "/".join(ARENAS) + "), and pick "
                         "the one that fits them all best. The first is "
                         "where the authoring rounds iterate.")
    ap.add_argument("--trials", type=int, default=3,
                    help="restore trials per candidate per savepoint arena")
    args = ap.parse_args()

    # ONE POLICY ACROSS STAGES, not one per stage (user, 2026-08-24). A
    # spec authored in one arena names that arena's items and dies
    # everywhere else: v1 named POTION at Pewter and could not heal at
    # Celadon; v6 named HYPER_POTION at the league and would not survive
    # Brock. Scoring a candidate in every arena is what makes "fits the
    # whole game" a number rather than a hope.
    names = [n.strip() for n in (args.arenas or args.arena).split(",")
             if n.strip()]
    for n in names:
        if n not in ARENAS and n not in ("brock", "e4", "gym"):
            sys.exit(f"unknown arena {n}; known: {', '.join(ARENAS)}")

    def build(name: str) -> Gym:
        kind, save, aspec = ARENAS.get(name, (name, args.from_save, None))
        if name == names[0] and args.from_save:
            save = args.from_save          # an explicit save still wins
        g = Gym(args.plan, args.run_id, model=args.model,
                from_save=save, arena=kind, trials=args.trials,
                arena_spec=aspec)
        for attempt in (1, 2):
            try:
                print(f"[gym] booting the {name} arena (attempt {attempt})...")
                g.boot()
                if kind in ("e4", "gym"):
                    g.prepare_arena()
                else:
                    g.prepare()
                return g
            except Exception as e:
                print(f"[gym] setup attempt {attempt} failed: {e}")
                g.shutdown()
                if attempt == 2:
                    raise
                time.sleep(3)

    gym = build(names[0])
    print(f"[gym] ready (rival fight re-armable: {gym.rival_ok})")
    # The brief is assembled AFTER the boot, so the party and bag in it are
    # the ones this spec will actually be handed. It used to be a module
    # constant written months ago describing a Squirtle that never existed
    # in this run.
    _ex = getattr(gym, "ex", None)
    sys_msg = sys_prompt(_ex.settle() if _ex else None)
    print(f"[gym] evidence brief: {len(sys_msg)} chars")

    if args.eval_only:
        spec = battle_policy.load_spec(args.eval_only)
        print(f"[eval-only] {spec.get('name')}")
        r = gym.score(spec)
        print(feedback_text(spec.get("name", "artifact"), r))
        base = gym.score(battle_policy.DEFAULT_SPEC)
        print(feedback_text("baseline typed_v0", base))
        gym.shutdown()
        return

    candidates = []   # (spec, results)
    feedback = "This is your first attempt."
    for rnd in range(1, args.rounds + 1):
        user = (f"Author battle-policy spec candidate #{rnd}.\n"
                f"FEEDBACK ON PREVIOUS CANDIDATES:\n{feedback}\n"
                "Author the spec now (JSON only).")
        reply = brock_probe.chat(
            [{"role": "system", "content": sys_msg},
             {"role": "user", "content": user}], args.model)
        spec = _parse_spec(reply)
        probs = battle_policy.validate_spec(spec) if spec else ["no JSON"]
        if probs:
            print(f"[round {rnd}] invalid spec: {probs}")
            feedback += f"\ncandidate #{rnd}: INVALID ({probs}) — fix these."
            continue
        spec.setdefault("name", f"model_r{rnd}")
        print(f"[round {rnd}] evaluating {spec['name']}: "
              f"{json.dumps(spec, separators=(',', ':'))[:200]}")
        r = gym.score(spec)
        candidates.append((spec, r))
        fb = feedback_text(f"candidate #{rnd} ({spec['name']})", r)
        print(f"[round {rnd}] {fb}")
        feedback = "\n".join(
            feedback_text(f"candidate #{i+1} ({s['name']})", rr)
            for i, (s, rr) in enumerate(candidates)) + (
            "\nImprove on the best so far; change what the results "
            "suggest is losing fights.")

    if not candidates:
        sys.exit("no valid candidates authored")
    # baseline for reference (not a candidate): the hand-seeded spec
    print("[baseline] evaluating hand-seeded typed_v0 for reference...")
    base = gym.score(battle_policy.DEFAULT_SPEC)
    print("[baseline] " + feedback_text("typed_v0", base))

    # ---------------------------------------- the rest of the game
    # The authoring rounds iterate in ONE arena, because feedback has to
    # arrive between rounds and a boot per arena per round is hours. The
    # candidates that come out of it are then carried to every other
    # arena and scored there, and the winner is the one that holds up
    # across all of them.
    across = {s["name"]: [(names[0], r)] for s, r in candidates}
    primary_map = getattr(gym, "arena_map", None)
    primary_party = getattr(gym, "arena_party", [])
    for an in names[1:]:
        gym.shutdown()
        print(f"\n[gym] carrying {len(candidates)} candidate(s) to {an}")
        gym = build(an)
        for spec, _ in candidates:
            rr = gym.score(spec)
            across[spec["name"]].append((an, rr))
            print(f"[{an}] " + feedback_text(spec["name"], rr))

    if len(names) > 1:
        print("\n[across] one spec, the whole game:")
        for s, _ in candidates:
            print(cross_text(s["name"], across[s["name"]]))
        best_spec = max(candidates,
                        key=lambda c: cross_key(across[c[0]["name"]]))[0]
        best_r = across[best_spec["name"]][0][1]
    else:
        best_spec, best_r = max(candidates, key=lambda c: rank_key(c[1]))
    artifact = dict(best_spec)
    artifact["provenance"] = {
        "authored_by": args.model, "run": args.run_id,
        "via": "policy_author", "rounds": len(candidates),
        # WHICH ARENA JUDGED IT, said outright. pick_policy.py has to
        # know, because `rooms` exists only for the gauntlet and
        # `badge`/`rival_wins` only for Brock — rank them on one scale
        # and every gauntlet spec beats every Brock spec for free. It
        # was inferable from the shape of the score and now it is not
        # guessed (2026-09-12).
        "eval": dict(best_r, arena=gym.arena if len(names) == 1
                     else "+".join(names),
                     arena_map=primary_map,
                     arena_party=primary_party,
                     # ...AND WHAT IT DID IN EACH. A spec fit across the
                     # game is not the same artifact as a spec fit to one
                     # room, and pick_policy has to be able to tell.
                     arenas=({an: rr for an, rr
                              in across[best_spec["name"]]}
                             if len(names) > 1 else None),
                     cross_total=(round(cross_key(
                         across[best_spec["name"]])[0], 4)
                         if len(names) > 1 else None)),
        "baseline_typed_v0": base,
    }
    args.out.write_text(json.dumps(artifact, indent=2))
    print(f"\nBEST: {best_spec['name']} -> {args.out}")
    if len(names) > 1:
        print(cross_text(best_spec["name"], across[best_spec["name"]]))
    else:
        print(feedback_text(best_spec["name"], best_r))
    gym.shutdown()


if __name__ == "__main__":
    main()

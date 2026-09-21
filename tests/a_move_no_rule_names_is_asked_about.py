#!/usr/bin/env python3
"""A no-power move in the party that no policy rule names gets a rule of
the run's own, written by the model and played back to it.

The battle policy never picks a 0-power move while a damaging move has PP:
it scores 0. The only way one is ever used is a `setup` rule that NAMES it
— and the policy is authored OFFLINE, by a model that cannot know what the
party will hold. v13 names CONFUSE_RAY and SLEEP_POWDER; three fresh draws
of the block each named the same six moves and never LEECH_SEED. So run 29
reached BROCK holding BULBASAUR's LEECH_SEED, PIKACHU's THUNDER_WAVE and
GROWL, PIDGEY's SAND_ATTACK and RATTATA's TAIL_WHIP, and not one of them
could ever be chosen; it lost to an ONIX its TACKLE could not dent and won
the rematch (user, 2026-09-21: "its preventing good ol bulba from leeching
and winning first thing without a rematch").

So the run asks, once per move, when it first sees one: here is the move,
who knows it, what else that Pokemon has, and what your policy already
rules on. Write the rule or say null. WRITTEN ONE AT A TIME THEY DO NOT ADD
UP — in a hand run two GROWLs stood ahead of a LEECH_SEED whose window is
two turns, so the seed was never reached — so what the rules together make
each Pokemon DO is computed by playing the policy itself, said back once,
and the model revises. Nothing here says a move is good.

Pinned: only no-power moves, only ones no rule names, once each; a refused
rule is not kept; null is an answer and is not asked again; the move name
is the harness's, not the model's; the rules lay over the policy in the
model's own order and re-lay cleanly; the echo plays the real policy and
takes a revision; the arena and RED_SETUP_ASK=0 turn it off; nothing in
the question names a move or says one is worth using. Synthetic."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def mv(i, power, mtype="NORMAL", pp=20):
    return {"id": i, "power": power, "type": mtype, "max_pp": pp, "pp": pp}


PARTY = [
    {"species": "BULBASAUR", "level": 14, "hp": 38, "max_hp": 38,
     "types": ["GRASS", "POISON"],
     "moves": [mv("TACKLE", 35), mv("GROWL", 0), mv("LEECH_SEED", 0, "GRASS"),
               mv("VINE_WHIP", 35, "GRASS")]},
    {"species": "PIKACHU", "level": 12, "hp": 34, "max_hp": 34,
     "types": ["ELECTRIC"],
     "moves": [mv("THUNDERSHOCK", 40, "ELECTRIC"), mv("GROWL", 0),
               mv("THUNDER_WAVE", 0, "ELECTRIC")]},
]
SEEN = {}


def run(replies, party=PARTY, spec=None, env=None, model="m"):
    """Ask with a scripted model. replies: list of strings, in order."""
    tmp = Path(tempfile.mkdtemp(prefix="setup_"))
    E.RUN = tmp
    E.set_active_spec(spec if spec is not None else dict(
        B.DEFAULT_SPEC, setup=[{"move": "SLEEP_POWDER", "max_uses": 1}]))
    said = []

    def chat(msgs, m, **kw):
        said.append(msgs[1]["content"])
        SEEN["sys"] = msgs[0]["content"]
        return replies[min(len(said) - 1, len(replies) - 1)]
    E.brock_probe.chat = chat
    import os
    for k, v in (env or {}).items():
        os.environ[k] = v
    ex = E.Executor.__new__(E.Executor)
    ex.logf = io.StringIO()
    ex.t0 = time.time()
    ex.model = model
    try:
        n = ex._ask_setup_rules({"party": party})
    finally:
        for k in (env or {}):
            os.environ.pop(k, None)
    rows = [json.loads(l) for l in ex.logf.getvalue().splitlines()]
    book = json.loads((tmp / "setup_rules.json").read_text()) \
        if (tmp / "setup_rules.json").exists() else {}
    return n, rows, book, said


RULE = '{"why":"it saps","rule":{"move":"%s","max_uses":1,"per_foe":true},"before":null}'
NULL = '{"why":"not worth a turn","rule":null}'

n, rows, book, said = run([RULE % "LEECH_SEED", RULE % "GROWL",
                           RULE % "THUNDER_WAVE", '{"setup":null,"why":"fine"}'])
FIRST = list(said)          # the pages of this first run, kept for below
asked = [r["move"] for r in rows if r["kind"] == "setup_rule_asked"]
ck("every no-power move the party holds is asked about, once each",
   asked == ["GROWL", "LEECH_SEED", "THUNDER_WAVE"], asked)
ck("...and no move with power ever is",
   not any(m in asked for m in ("TACKLE", "VINE_WHIP", "THUNDERSHOCK")))
ck("...nor one the policy already rules on",
   "SLEEP_POWDER" not in asked and "SLEEP_POWDER" in SEEN["sys"] is False
   or "SLEEP_POWDER" not in asked)
ck("the rules are kept with who knows the move and why",
   book["LEECH_SEED"]["who"] == "BULBASAUR L14"
   and book["LEECH_SEED"]["why"] == "it saps", book.get("LEECH_SEED"))
ck("the move named in the rule is the harness's, whatever the model wrote",
   all(book[k]["rule"]["move"] == k for k in asked))

E.set_active_spec(dict(B.DEFAULT_SPEC,
                       setup=[{"move": "SLEEP_POWDER", "max_uses": 1}]))
E.RUN = Path(str(list(book.keys()) and Path(tempfile.gettempdir())))


def lay(book_dict):
    tmp = Path(tempfile.mkdtemp(prefix="lay_"))
    (tmp / "setup_rules.json").write_text(json.dumps(book_dict))
    E.RUN = tmp
    E.set_active_spec(dict(B.DEFAULT_SPEC,
                           setup=[{"move": "SLEEP_POWDER", "max_uses": 1}]))
    E.lay_setup_rules()
    return [str(r.get("move")) for r in E.ACTIVE_SPEC["setup"]]


BOOK = {"_order": ["THUNDER_WAVE", "LEECH_SEED"],
        "THUNDER_WAVE": {"rule": {"move": "THUNDER_WAVE", "max_uses": 1}},
        "LEECH_SEED": {"rule": {"move": "LEECH_SEED", "max_uses": 1}},
        "GROWL": {"rule": None}}
ck("the rules lay over the policy's own, in the model's order",
   lay(BOOK) == ["SLEEP_POWDER", "THUNDER_WAVE", "LEECH_SEED"], lay(BOOK))
ck("...and a move answered with null lays nothing",
   "GROWL" not in lay(BOOK))
E.lay_setup_rules()
E.lay_setup_rules()
ck("laying twice does not stack them",
   [str(r.get("move")) for r in E.ACTIVE_SPEC["setup"]]
   == ["SLEEP_POWDER", "THUNDER_WAVE", "LEECH_SEED"])
ck("a revised rule replaces the one it revises, not joins it",
   lay(dict(BOOK, LEECH_SEED={"rule": {"move": "LEECH_SEED", "max_uses": 3}}))
   .count("LEECH_SEED") == 1
   and E.ACTIVE_SPEC["setup"][-1]["max_uses"] == 3)

# ---- a rule the DSL refuses is not kept, and comes round again ----------
n, rows, book, said = run(['{"why":"x","rule":{"move":"GROWL","max_uses":99}}',
                           NULL, NULL, '{"setup":null}'])
ck("a rule the policy would refuse is not kept",
   any(r["kind"] == "setup_rule_refused" for r in rows)
   and "GROWL" not in book, book)
ck("...so it is asked again at the next plan, and the others are not",
   set(book) - {"_order"} == {"LEECH_SEED", "THUNDER_WAVE"}, sorted(book))
n, rows, book, said = run([NULL, NULL, NULL, '{"setup":null}'])
ck("null is an answer and is kept as one",
   n == 0 and book["GROWL"]["rule"] is None and len(set(book) - {"_order"}) == 3)
n2, rows2, _, said2 = run(['{"gibberish": 1}'] * 4)
ck("an unreadable answer keeps nothing and says so",
   any(r["kind"] == "setup_rule_unparsed" for r in rows2))

# ---- what the question says --------------------------------------------
S = " ".join(SEEN["sys"].split())
ck("the question says why the move would otherwise never be used",
   "NEVER uses a move with no power" in S and "names the move" in S)
ck("...and that the order is part of the rule",
   "ONE RULE FIRES A TURN" in S and '"before"' in S)
ck("...and hands the judgment over",
   "is yours to judge" in S and "or null to leave it unused" in S)
ck("it names no move and calls none worth using",
   not any(w in S.upper() for w in
           ("LEECH", "HYPNOSIS", "THUNDER_WAVE", "DEADLY", "POWERFUL",
            "SHOULD USE", "WORTH USING", "THE BEST")), S[:160])
U = " ".join(FIRST[0].split())
ck("the move, who knows it and what else it has are on the page",
   "THE MOVE: GROWL" in U and "known by BULBASAUR L14" in U
   and "ITS OTHER MOVES:" in U and "TACKLE" in U)
ck("...and the rules already standing, in the order they are tried",
   "MOVES YOUR POLICY ALREADY HAS A RULE FOR" in U and "SLEEP_POWDER" in U)
ck("...and the run's own so far, so the next rule is written among them",
   "YOUR OWN RULES SO FAR" in U and "none yet" in U
   and "LEECH_SEED" in " ".join(FIRST[2].split()), FIRST[2][-160:])

# ---- the playback ------------------------------------------------------
ex = E.Executor.__new__(E.Executor)
ex.logf = io.StringIO()
ex.t0 = time.time()
ex.model = "m"
E.set_active_spec(dict(B.DEFAULT_SPEC, avoid_status_moves=False, setup=[
    {"move": "GROWL", "max_uses": 2, "first_turns": 2, "min_hp_frac": 0.0,
     "vs": "any", "per_foe": True},
    {"move": "LEECH_SEED", "max_uses": 1, "first_turns": 2,
     "min_hp_frac": 0.0, "vs": "any", "per_foe": True}]))
line = ex._setup_dry_run(PARTY[0], "trainer")
ck("the playback is the policy itself, turn by turn",
   line == ["GROWL", "GROWL", "VINE_WHIP", "VINE_WHIP"], line)
ck("...and it shows the seed that was never reached",
   "LEECH_SEED" not in line)

BK = {"_order": ["GROWL", "LEECH_SEED"],
      "GROWL": {"rule": {"move": "GROWL", "max_uses": 2, "first_turns": 2,
                         "vs": "any", "per_foe": True}, "who": "BULBASAUR L14"},
      "LEECH_SEED": {"rule": {"move": "LEECH_SEED", "max_uses": 1,
                              "first_turns": 2, "vs": "any", "per_foe": True},
                     "who": "BULBASAUR L14"}}
tmp = Path(tempfile.mkdtemp(prefix="echo_"))
E.RUN = tmp
saw = {}


def echo_chat(msgs, m, **kw):
    saw["sys"], saw["user"] = msgs[0]["content"], msgs[1]["content"]
    return json.dumps({"why": "the seed never landed", "setup": [
        {"move": "LEECH_SEED", "max_uses": 1, "first_turns": 2, "vs": "any",
         "per_foe": True},
        {"move": "GROWL", "max_uses": 1, "first_turns": 3, "vs": "trainer",
         "per_foe": True}]})


E.brock_probe.chat = echo_chat
book2 = dict(BK)
ck("the revision is taken", ex._setup_echo(PARTY, book2) is True)
ck("...and reorders the rules as the model said",
   book2["_order"] == ["LEECH_SEED", "GROWL"], book2["_order"])
ck("...and keeps the changed values",
   book2["GROWL"]["rule"]["vs"] == "trainer"
   and book2["GROWL"]["rule"]["max_uses"] == 1)
U2 = " ".join(saw["user"].split())
ck("the page shows what each Pokemon does, wild and trainer",
   "BULBASAUR L14" in U2 and "WILD:" in U2 and "TRAINER:" in U2
   and "GROWL -> GROWL" in U2, U2[:200])
S2 = " ".join(saw["sys"].split())
ck("...and says a wild line is every wild battle of the run",
   "hundreds fought while training" in S2
   and "never appears on a line is never reached" in S2)
ck("...and names no move and calls none good",
   not any(w in S2.upper() for w in ("LEECH", "GROWL", "DEADLY", "SHOULD USE")))
book3 = dict(BK)
E.brock_probe.chat = lambda *a, **k: '{"why":"they are right","setup":null}'
ck("a null revision leaves the rules alone", ex._setup_echo(PARTY, book3) is False)
book4 = dict(BK)
E.brock_probe.chat = lambda *a, **k: json.dumps(
    {"setup": [{"move": "GROWL", "max_uses": 99}]})
ck("...and a revision the policy would refuse does too",
   ex._setup_echo(PARTY, book4) is False
   and book4["GROWL"]["rule"]["max_uses"] == 2)
book5 = dict(BK)
E.brock_probe.chat = lambda *a, **k: json.dumps(
    {"setup": [{"move": "LEECH_SEED", "max_uses": 1, "per_foe": True}]})
ex._setup_echo(PARTY, book5)
ck("a rule left out of the revision is dropped, not kept",
   book5["GROWL"]["rule"] is None and book5["_order"] == ["LEECH_SEED"])

# ---- off switches ------------------------------------------------------
n, rows, book, said = run([RULE % "GROWL"], env={"RED_ARENA": "1"})
ck("the arena never asks", n == 0 and not said)
n, rows, book, said = run([RULE % "GROWL"], env={"RED_SETUP_ASK": "0"})
ck("RED_SETUP_ASK=0 turns it off", n == 0 and not said)
n, rows, book, said = run([RULE % "GROWL"], model=None)
ck("...and so does having no model to ask", n == 0 and not said)

SRC = (ROOT / "planner/executor.py").read_text()
ck("the run's rules are laid at launch, and never in an arena",
   'if os.environ.get("RED_ARENA") != "1":\n        _n = lay_setup_rules()' in SRC)
ck("...and the question is asked where the leg's plan starts",
   "self._ask_setup_rules(self.settle())" in SRC
   and SRC.index("self._party_floor(plan") < SRC.index("self._ask_setup_rules("))
ck("the author and the run are told the rule in the same words",
   B.SETUP_DOC in E.Executor.SETUP_RULE_SYS
   and B.SETUP_DOC in __import__("policy_author").DSL_DOC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

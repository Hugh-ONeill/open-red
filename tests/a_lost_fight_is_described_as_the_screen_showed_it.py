#!/usr/bin/env python3
"""A lost trainer fight reaches the page as a player watching it saw it.

Run 26 went into BROCK eight times with a L12 BULBASAUR whose only attack
was TACKLE, "not very effective" under every one; PIDGEY finished what it
could and took all the experience, and every plan said "Bulbasaur has a
strong type advantage over Brock's rock-types". The page said a blackout
happened and "GEODUDE L12 on somewhere", and named trainers and the money
they paid but never a patch of grass, so the run went door to door for
"remaining trainers to gain experience" (user, 2026-09-16: "its also not
gone into the wilds to train, it was looking for trainers to train
against"; "build all three").

Pinned: the recap (moves and what the screen said of each, the first foe's
HP, who fainted); experience per member since the step began; the map a
foe was fought on; and on a trainer step that has blacked out more than
once, the wild ground the run has fought on. None of it says what to do.

Synthetic: no game, no model.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


tmp = Path(tempfile.mkdtemp(prefix="fight_recap_"))
log = tmp / "executor_log.jsonl"
turns = []
for hp in (33, 32, 31, 30, 29, 28, 27, 26):
    turns.append({"kind": "battle_turn", "op": "battle_move",
                  "why": "TACKLE score=16.6 eff=0.5", "foe_hp": hp})
turns.append({"kind": "battle_turn", "op": "pick_party", "why": "replacement"})
for hp in (25, 24, 20, 19):
    turns.append({"kind": "battle_turn", "op": "battle_move",
                  "why": "GUST score=30.0 eff=0.5", "foe_hp": hp})
log.write_text("\n".join(json.dumps(t) for t in turns) + "\n")

ex = object.__new__(E.Executor)
ex.logf = open(log, "a")
ex.logged = []
ex.log = lambda k, **kw: ex.logged.append((k, kw))
ex._last_overworld_map = "PEWTER_GYM"
before = {"mode": "battle",
          "battle": {"kind": "trainer", "trainer": "BROCK", "leader": True,
                     "foe": {"species": "GEODUDE", "level": 12}}}
after = {"mode": "overworld", "party": [
    {"species": "BULBASAUR", "level": 12, "hp": 0},
    {"species": "PIDGEY", "level": 15, "hp": 0}]}
ex._note_fight(before, after, 0)
lf = getattr(ex, "_last_fight", {})
ck("the fight is kept as lost when the whole party fainted", lf.get("lost"))
ck("...against whom, and where", lf.get("who") == "BROCK"
   and lf.get("where") == "PEWTER_GYM")
ck("each move is counted with what the screen said of it",
   "TACKLE x8 (not very effective)" in lf.get("text", "")
   and "GUST x4 (not very effective)" in lf.get("text", ""))
ck("the first foe's HP is its own, and it was not knocked out",
   "GEODUDE L12 came out first at 33 hp and was at 19 hp" in lf.get("text", "")
   and "it was not knocked out" in lf.get("text", ""))
ck("who fainted", "Fainted: BULBASAUR, PIDGEY" in lf.get("text", ""))
ck("nothing about what to do",
   not any(w in lf.get("text", "").lower()
           for w in ("should", "try", "train", "level up", "vine")))
won = {"mode": "overworld", "party": [
    {"species": "BULBASAUR", "level": 12, "hp": 10},
    {"species": "PIDGEY", "level": 15, "hp": 0}]}
ex._note_fight(before, won, 0)
ck("a fight with someone still standing is not kept as lost",
   ex._last_fight.get("lost") is False)

# a blackout heals the party before the recap reads it (run 27, 2026-09-16)
healed = {"mode": "overworld", "map": {"id": "PEWTER_POKECENTER"},
          "last_text": "SAGE is out of useable POKéMON! SAGE blacked out!",
          "party": [{"species": "BULBASAUR", "level": 12, "hp": 36},
                    {"species": "PIDGEY", "level": 15, "hp": 38}]}
ex._note_fight(before, healed, 0)
ck("a blackout is a lost fight, though the party wakes healed",
   ex._last_fight.get("lost") is True)
ex._note_fight(before, dict(healed, last_text=""), 0)
ck("...and waking in a Center with nothing on screen says the same",
   ex._last_fight.get("lost") is True)
log.write_text("\n".join(json.dumps(t) for t in [
    {"kind": "battle_turn", "op": "battle_move", "why": "KO with GUST", "foe_hp": 5},
    {"kind": "battle_turn", "op": "battle_move", "why": None, "foe_hp": 3},
    {"kind": "battle_turn", "op": "battle_move",
     "why": "weaken with TACKLE (foe at 100%)", "foe_hp": 30}]) + "\n")
ex._note_fight(before, healed, 0)
ck("a move is named from 'KO with' and 'weaken with' rows",
   "GUST x1" in ex._last_fight["text"] and "TACKLE x1" in ex._last_fight["text"]
   and "KO x" not in ex._last_fight["text"] and "? x" not in ex._last_fight["text"])

# ---- experience since the step began ---------------------------------------
sg = {"id": "defeat_brock"}
p0 = {"party": [{"species": "BULBASAUR", "level": 12, "exp": 1314},
                {"species": "PIDGEY", "level": 13, "exp": 2000}]}
p1 = {"party": [{"species": "BULBASAUR", "level": 12, "exp": 1314},
                {"species": "PIDGEY", "level": 15, "exp": 2934}]}
ck("the first page of a step takes the baseline and says nothing",
   ex._party_since_text(p0, sg) == "")
t = ex._party_since_text(p1, sg)
ck("later pages say who gained what",
   "BULBASAUR L12 (+0 exp)" in t and "PIDGEY L13->L15 (+934 exp)" in t)
ck("...and the game's rule about who gets it",
   "still standing when the foe fainted" in t)
ck("a new step starts a new baseline",
   ex._party_since_text(p1, {"id": "other"}) == "")

# ---- the page -----------------------------------------------------------------
src = (ROOT / "planner/executor.py").read_text()
ck("a foe's map falls back to where the party last stood",
   'getattr(self, "_last_overworld_map",' in
   src[src.index("self._recent_foes = (getattr("):][:400])
ck("the blackout page carries the lost fight and the experience",
   "THE LAST FIGHT YOU LOST (vs" in src
   and "_since = self._party_since_text(start, sg)" in src)
ck("a trainer step blacked out more than once lists wild ground",
   "if (self._bo_here > 1\n                        and not self._is_party_goal("
   in src and "self._wild_elsewhere_fought_note(_hm, start)" in src)
ck("every trainer fight is recapped, and a recap never costs the fight",
   'if b0.get("kind") == "trainer" and _jpos is not None:' in src
   and 'self.log("fight_recap_error"' in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

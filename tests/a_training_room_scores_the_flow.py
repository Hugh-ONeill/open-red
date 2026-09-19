#!/usr/bin/env python3
"""A training room scores how far a trainee got toward its goal level
inside a budget of STEPS, the walk to the nurse included, and train rules
are ranked on that alone.

The plan (2026-09-19): "Metric: trainee experience per step walked, heal
walks included. Blackouts and experience landing on members already past
the goal count against. Score the FLOW, not experience per battle."

Pinned, against a scripted game: the trial stops at its step budget; a
fainted trainee costs a walk to the nurse, charged to the budget; three
battles that earned nothing, with somebody hurt, cost one too; reaching the
goal stops the trial early and the steps left are its quality; progress is
capped at the goal; experience landing on members already at the goal is
counted as spilled; a blackout ends the trial; the room's fraction, quality
and feedback read those numbers; the three rooms are arenas of kind train;
the picker ranks train rules apart from fight policies and refuses one that
lost to a constant tactic; the executor lays a train rule over the active
policy; the shim's nurse exists only in an arena and the pedometer never
reaches the model. Synthetic."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy  # noqa: E402
import executor as E  # noqa: E402
import pick_policy as PP  # noqa: E402
import policy_author as PA  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


TMP = Path(tempfile.mkdtemp(prefix="trainroom_"))
PA.LOG = TMP / "executor_log.jsonl"
PA.LOG.write_text("")


class Game:
    """A scripted patch of grass: each battle is (trainee exp, exp to the
    strong member, trainee hp after, did it run)."""

    def __init__(self, script, steps_per_grind=10, wake=None):
        self.script, self.i = list(script), 0
        self.steps_per_grind = steps_per_grind
        self.wake = wake
        self.sent = []
        self.reset()

    def reset(self):
        self.steps, self.mode, self.map = 0, "overworld", "ROUTE_1"
        self.party = [
            {"species": "IVYSAUR", "level": 20, "hp": 60, "max_hp": 60,
             "exp": 5000, "dvs": {"hp": 15}, "otId": 1},
            {"species": "PIKACHU", "level": 5, "hp": 18, "max_hp": 18,
             "exp": 125, "dvs": {"hp": 8}, "otId": 1}]

    def obs(self):
        o = {"mode": self.mode, "party": [dict(m) for m in self.party],
             "steps_walked": self.steps, "bag": {}}
        if self.mode == "battle":
            o["battle"] = {"kind": "wild",
                           "me": dict(self.party[0], maxhp=60, slot=1),
                           "foe": {"species": "RATTATA", "level": 3,
                                   "hp": 10, "maxhp": 10}}
        else:
            o["map"] = {"id": self.map}
        return o

    # the bridge
    def send(self, op, **kw):
        self.sent.append(op)
        if op == "checkpoint_restore":
            self.reset()
        elif op == "grind":
            self.steps += min(self.steps_per_grind, kw.get("steps", 60))
            self.mode = "battle"
        elif op == "arena_heal":
            for m in self.party:
                m["hp"] = m["max_hp"]
        return dict(self.obs(), result={"ok": True})

    # the executor
    def settle(self):
        return self.obs()

    def _lead_the_trainee(self, obs, step, sg, trace):
        return obs

    def handle_battle(self, sg, obs):
        got, other, hp, ran = self.script[min(self.i, len(self.script) - 1)]
        self.i += 1
        with open(PA.LOG, "a") as f:
            f.write(json.dumps({"kind": "battle_start",
                                "foe": "RATTATA L3"}) + "\n")
            f.write(json.dumps({"kind": "battle_turn",
                                "op": "battle_run" if ran else "battle_move"})
                    + "\n")
        self.party[1]["exp"] += got
        self.party[0]["exp"] += other
        self.party[1]["hp"] = hp
        if self.party[1]["exp"] >= 1000:
            self.party[1]["level"] = 10
        self.mode = "overworld"
        if self.wake and self.i >= self.wake:
            self.map = "VIRIDIAN_POKECENTER"
        return self.obs()


def room(script, cfg=None, k=1, **kw):
    g = object.__new__(PA.Gym)
    game = Game(script, **kw)
    g.b = g.ex = game
    g.arena_map = "ROUTE_1"
    g.train_cfg = dict({"trainee": 2, "goal": 10, "steps": 100,
                        "heal_walk": 30, "need_exp": 875}, **(cfg or {}))
    return g.eval_spec_train(dict(battle_policy.DEFAULT_SPEC), k=k), game


# ------------------------------------------------------------ the budget
r, g = room([(20, 0, 18, False)])
ck("a trial stops at its step budget",
   r["steps"] == 100 and r["battles"] == 10 and "100 steps" in r["gauntlet_detail"][0],
   r["gauntlet_detail"])
ck("...and what the trainee earned alone is counted as alone",
   r["gain"] == 200 and r["alone"] == 10 and r["shared"] == 0)
ck("progress is the share of the experience its goal needed",
   abs(r["progress"] - 200 / 875) < 1e-9 and r["need"] == 875)

# ---------------------------------------------------------- the nurse walk
r, g = room([(20, 0, 0, False), (20, 0, 18, False)])
ck("a fainted trainee costs a walk to the nurse, charged to the budget",
   r["heals"] == 1 and r["faints"] == 1 and "arena_heal" in g.sent
   and r["battles"] == 7, (r["heals"], r["battles"], r["gauntlet_detail"]))
r, g = room([(0, 0, 9, True)])
ck("three battles that earned nothing, with somebody hurt, cost one too",
   r["heals"] >= 1 and r["fled"] == r["battles"], (r["heals"], r["fled"]))
r, g = room([(0, 30, 18, False)])
ck("...but a whole party is never walked to the nurse for it",
   r["heals"] == 0 and r["nothing"] == 10, (r["heals"], r["nothing"]))

# -------------------------------------------------------- reaching the goal
r, g = room([(300, 0, 18, False)])
ck("reaching the goal stops the trial early",
   r["reached"] == 1 and r["steps"] == 30 and "L10 reached" in r["gauntlet_detail"][0],
   r["gauntlet_detail"])
ck("...progress is capped at the goal", r["progress"] == 1.0)
ck("...and the steps left are its quality",
   PA.arena_quality(r) > PA.arena_quality(room([(20, 0, 18, False)])[0]))

# ------------------------------------------------------------------ spill
r, g = room([(10, 10, 18, False)])
ck("experience landing on a member already at the goal is spilled",
   r["spill"] == 100 and r["shared"] == 10, (r["spill"], r["shared"]))
r2, _ = room([(10, 10, 18, False)], cfg={"goal": 30, "need_exp": 5000})
ck("...and not when that member is short of it too", r2["spill"] == 0)

# --------------------------------------------------------------- blackout
r, g = room([(20, 0, 18, False)], wake=3)
ck("a blackout ends the trial where it stands",
   r["blackouts"] == 1 and r["battles"] == 3 and "blackout" in r["gauntlet_detail"][0],
   r["gauntlet_detail"])

# ------------------------------------------------------- the room's numbers
r, _ = room([(20, 0, 18, False)], k=2)
ck("the room's fraction is the mean progress of its trials",
   abs(PA.arena_fraction(r) - 200 / 875) < 1e-9 and r["gauntlet_trials"] == 2)
ck("...its points are that plus a bounded bonus",
   PA.arena_fraction(r) <= PA.arena_points(r) < PA.arena_fraction(r) + 0.05)
fb = PA.feedback_text("cand", r)
ck("the feedback says what was earned, the walks and the faints",
   "the trainee earned 400 of the 1750 experience" in fb
   and "walk(s) to the nurse" in fb and "the wilds met: RATTATA L3" in fb, fb)
better, _ = room([(40, 0, 18, False)])
ck("more progress ranks first", PA.rank_key(better) > PA.rank_key(
    room([(20, 0, 18, False)])[0]))
ck("the three rooms are arenas of kind train",
   all(PA.ARENAS[n][0] == "train" for n in PA.TRAIN_ROOMS)
   and all((ROOT / f"plans/arena_{n}.json").exists() for n in PA.TRAIN_ROOMS))
for n in PA.TRAIN_ROOMS:
    sp = json.loads((ROOT / f"plans/arena_{n}.json").read_text())
    tc = sp["train"]
    ck(f"{n} names a trainee under its goal, with DVs of its own",
       sp["party"][tc["trainee"] - 1]["level"] < tc["goal"]
       and sp["party"][tc["trainee"] - 1].get("dv") == 8
       and tc["need_exp"] > 0 and tc["heal_walk"] > 0 and tc["steps"] > 0)
ck("the references are the old constant and the two tactics",
   [b for _, b in PA.TRAIN_BASELINES][0] is None
   and all(battle_policy._train_problems(b) == []
           for _, b in PA.TRAIN_BASELINES if b))
laid = PA.with_train({"name": "v13", "stab": 1.5, "provenance": {"x": 1}},
                     {"lead": True}, "cand")
ck("a candidate is the base policy with the rule laid over it",
   laid == {"name": "cand", "stab": 1.5, "train": {"lead": True}}
   and battle_policy.validate_spec(laid) == [])
ck("the rule's own page says the split and never a tactic",
   "Experience is SHARED equally" in PA.TRAIN_DOC
   and not any(w in PA.TRAIN_DOC.lower() for w in
               ("you should", "best tactic", "recommend")))

# ------------------------------------------------------------- the picker
d = TMP / "plans"
d.mkdir()


def art(name, total, refs, rooms=3, blackouts=0, train=True):
    ev = {"arena": "train", "cross_total": total,
          "arenas": {f"r{i}": {"gauntlet_trials": 2, "blackouts": blackouts}
                     for i in range(rooms)}}
    (d / name).write_text(json.dumps({
        "name": name, **({"train": {"lead": True}} if train else {}),
        "provenance": {"eval": ev, "references": {
            k: {"cross_total": v} for k, v in refs.items()}}}))


art("train_model_v1.json", 1.80, {"always fight": 1.50})
art("train_model_v2.json", 2.10, {"always fight": 1.50})
art("train_model_v3.json", 1.20, {"always fight": 1.50})
art("train_model_v4.json", 2.50, {"always fight": 1.50}, blackouts=2)
win, rows = PP.rank_train(list(d.glob("train_model_v*.json")))
why = {p.name: w for p, w in rows}
ck("the best-scoring train rule wins", win and win.name == "train_model_v2.json", win)
ck("...one that lost to a constant tactic is refused",
   "under a constant tactic" in why["train_model_v3.json"], why)
ck("...and so is one that blacked out in every trial",
   "blacked out" in why["train_model_v4.json"], why)
(d / "policy_model_v9.json").write_text(json.dumps({"name": "fight"}))
ck("fight policies never enter the train ranking",
   all(p.name.startswith("train_") for p, _ in rows))
ck("...nor train rules the fight ranking",
   "train_model" not in (PP.__doc__ or "").split("--kind train")[0]
   and 'a.glob or "policy_model_v*.json"' in (ROOT / "planner/pick_policy.py").read_text())

# ------------------------------------------------- laid over the live policy
E.set_active_spec({"name": "v13", "flee_wild": {"hp_below": 0.3}})
ok = E.lay_train_rule(d / "train_model_v2.json")
ck("the executor lays a train rule over the active policy",
   ok and E.ACTIVE_SPEC.get("train") == {"lead": True}
   and E.ACTIVE_SPEC.get("name") == "v13")
(d / "bad.json").write_text(json.dumps({"train": {"lead": "yes"}}))
E.set_active_spec({"name": "v13"})
ck("...and leaves a bad one off",
   E.lay_train_rule(d / "bad.json") is False and "train" not in E.ACTIVE_SPEC)
sh = (ROOT / "fresh_run.sh").read_text()
ck("the launch script picks it apart from the policy",
   "--kind train" in sh and '--train-spec "$TRAIN"' in sh
   and "plans/train.pin" in sh)

# ------------------------------------------------------------------ the shim
shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim's nurse exists only in a game started as an arena",
   'function OPS.arena_heal(G, c)\n  if os.getenv("RED_ARENA") ~= "1" then\n'
   '    return false, "no such op"' in shim)
ck("...which only policy_author's isolated game is",
   'os.environ["RED_ARENA"] = "1"' in (ROOT / "planner/policy_author.py").read_text()
   and "RED_ARENA" not in sh
   and "RED_ARENA" not in (ROOT / "run.sh").read_text())
ck("steps are counted a cell at a time and published",
   "if moved then STEPS_WALKED = STEPS_WALKED + 1 end" in shim
   and "o.steps_walked = STEPS_WALKED" in shim
   and shim.index("local STEPS_WALKED = 0") < shim.index("o.steps_walked"))
ck("...and the pedometer never reaches the model",
   "steps_walked" not in E.model_view({"steps_walked": 9, "mode": "overworld"}))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d_ in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d_ else f"  {str(d_)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

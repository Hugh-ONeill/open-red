#!/usr/bin/env bash
# One-shot executor run against a FRESH game process. new_game from a
# mid-session game lands in a ui state bootstrap can't clear, so a
# bootstrapped run must own its own process start-to-finish.
# Usage: fresh_run.sh <plan...> [extra executor args...]
# NOTE: pass --escalate yourself for authoring runs; a bare invocation is
# a REPLAY run (macros only — a failed subgoal fails the plan). Multiple
# plan files chain in order (executor.py plans nargs='+'); --continue
# resumes the on-disk save instead of new_game.
set -euo pipefail
cd "$(dirname "$0")"
# Tell stop_all.sh what this rig started, so it never has to guess
# from a process-name pattern (rig.sh).
# shellcheck source=rig.sh
. ./rig.sh
rig_register run
# RED_HEADED=1 opens a real window (run.sh --headed) and RED_SPEED sets the
# clock: 200x is a blur to watch, 10-20x is followable by eye.
setsid ./run.sh ${RED_HEADED:+--headed} "${RED_SPEED:-200}" &
GAME_PID=$!
rig_register game "-$GAME_PID"     # setsid made it a group; kill the group
# kill the whole process group: xvfb-run's cleanup does not reliably reach
# love, which otherwise survives as an orphan on the dead Xvfb display
trap 'kill -- -"$GAME_PID" 2>/dev/null || true;
      [ -n "${EXEC_PID:-}" ] && kill "$EXEC_PID" 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do [ -f run/obs.json ] && break; sleep 1; done
# exit 66 = the game never booted: the executor never ran, so no leg was
# judged and no evidence exists. campaign.sh retries instead of rewriting.
[ -f run/obs.json ] || { echo "game did not come up" >&2; exit 66; }
# THE MODEL-AUTHORED SPEC IS THE ONE THAT PLAYS. battle_policy's own
# header says the hand-seeded DEFAULT_SPEC "exists for spine/oracle
# validation only; the record run requires a model-authored spec" — and
# nothing ever passed --policy-spec, so every battle of the record run was
# fought on the seed. plans/policy_model_v1.json had been sitting there
# authored and live-evaluated (6/6 rival, 3/3 badge, 0 blackouts, beating
# the typed_v0 baseline on oracle agreement 47 to 36) and never once used.
# Newest by version, overridable, and silent if there is none.
# ...AND THE ONE THAT SCORED BEST, NOT THE ONE NAMED LAST. This read
# `sort -V | tail -1` — the highest version NUMBER, which is a filename and
# not a result — so run 16 fought its whole game on v6, whose own
# provenance records three gauntlet trials that cleared zero rooms and
# blacked out three times of three, while v1 (6/6 rival, three badges, no
# blackouts) and v3 (eight Elite Four rooms, no blackouts) sat beside it
# (2026-09-12). Every spec carries the trial that judged it; pick_policy.py
# reads it, refuses one that failed its own trial, and picks by STAGE where
# there is a spec scored for it — the arenas measure different things and a
# POTION rule is right for Kanto and useless at the league.
_badges=$(python - <<'PB' 2>/dev/null || echo 0
import json
try:
    print(len((json.load(open("run/obs.json")).get("badges") or [])))
except Exception:
    print(0)
PB
)
# --why goes to stderr and the chosen path to stdout, so the log keeps
# the whole ranking (including what was rejected and why) beside the pick.
# A SPEC CHOSEN BY HAND OUTRANKS THE PICKER, AND OUTLIVES A RELAUNCH.
# pick_policy ranks by each spec's own provenance, which is scored in
# whatever arenas that spec was authored in; the three-way sweep on the
# workshopped rooms is a different and later verdict (v13: medicine decides
# 7 of 18 rooms against 4, real league 15/20), and the picker cannot read
# it. An env var would last one launch, so the choice lives in a file:
# plans/policy.pin holds one path. RED_POLICY still wins for a one-off;
# delete the pin to hand the choice back to the picker (user, 2026-09-16:
# "set v13 as the chain's policy").
# (|| true inside: under pipefail a missing pin failed the pipeline and
# set -e ended the launch before the executor started, 2026-09-19)
_pin=$( { head -1 plans/policy.pin 2>/dev/null || true; } | tr -d '[:space:]')
[ -n "$_pin" ] && [ ! -s "$_pin" ] && echo "[policy] pin $_pin is missing; falling back to the picker" >&2 && _pin=""
POLICY="${RED_POLICY:-${_pin:-$(python planner/pick_policy.py \
        --badges "$_badges" --why || true)}}"
pol=()
if [ -n "$POLICY" ] && [ -s "$POLICY" ]; then
  pol=(--policy-spec "$POLICY")
  echo "[policy] $POLICY"
fi
# ...AND THE TRAIN RULE LAID OVER IT. How a weak member is raised is its
# own artifact (plans/train_model_v*.json), authored over the fight policy
# and scored in the training rooms, which say nothing about fights and the
# fight rooms nothing about them; pick_policy ranks it apart (--kind
# train) and refuses one that lost to a constant tactic. Same override
# ladder as the policy: RED_TRAIN for a one-off, plans/train.pin to hold a
# choice, the picker otherwise. With none, the executor trains the old way.
_tpin=$( { head -1 plans/train.pin 2>/dev/null || true; } | tr -d '[:space:]')
[ -n "$_tpin" ] && [ "$_tpin" != "none" ] && [ ! -s "$_tpin" ] && echo "[policy] train pin $_tpin is missing; falling back to the picker" >&2 && _tpin=""
# RED_TRAIN=none (or a pin holding "none") turns it off: no rule is passed.
if [ "${RED_TRAIN:-$_tpin}" = "none" ]; then
  TRAIN=""
  echo "[policy] train rule: none (the executor trains the old way)"
else
  TRAIN="${RED_TRAIN:-${_tpin:-$(python planner/pick_policy.py \
          --kind train --why || true)}}"
fi
if [ -n "$TRAIN" ] && [ -s "$TRAIN" ]; then
  pol+=(--train-spec "$TRAIN")
  echo "[policy] train rule $TRAIN"
fi
# BACKGROUNDED SO IT CAN BE REGISTERED AND SO THE TRAP CAN REACH IT.
# Run in the foreground, a SIGTERM to this script ran the EXIT trap (killing
# the game) and then LEFT THE EXECUTOR ALIVE, talking to a bridge whose game
# had gone — which is precisely the "executor that outlived its game"
# contamination stop_all.sh was written for. `wait` still propagates its
# exit status, which campaign.sh reads.
python planner/executor.py --bootstrap "$@" "${pol[@]}" &
EXEC_PID=$!
rig_register executor "$EXEC_PID"
wait "$EXEC_PID"

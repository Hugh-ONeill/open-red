#!/usr/bin/env bash
# The no-game test suite, in parallel: every tests/*.py except the ones that
# BOOT A GAME (they drive a second copy of the game and must never run beside
# a live chain — tests/pc_box.py, the contract tests, the ops that need a
# real screen). Prints the count and the failures.
#   tests/run_suite.sh            # all no-game tests
#   JOBS=4 tests/run_suite.sh     # fewer at once
set -u
cd "$(dirname "$0")/.."
BOOTS='pc_box|contract|dig_out|stop_all_kills_the_whole_tree|a_crash_saves|a_naming_screen|a_name_is_the|a_machine_is_the|a_dead_game|a_policy_is_fit|a_fence_at|a_save_waits|an_arena_keeps|a_long_speech|a_save_whose|a_leg_is_measured|a_nurse_behind|a_level_up_move|a_staircase_is_not|an_edge_is_news|a_tm_reads|repeat_gate|a_lift_panel|an_hm_in_the|a_wipe_is|a_leg_boundary|saving_is_the|predicates|replay_smoke'
OUT=$(mktemp -d)
ls tests/*.py | grep -Ev "$BOOTS" | xargs -P "${JOBS:-10}" -I{} bash -c \
  'n=$(basename {} .py); timeout 300 python3 {} > '"$OUT"'/$n.log 2>&1 || echo "$n" >> '"$OUT"'/FAILED'
echo "ran $(ls "$OUT"/*.log | wc -l) tests (logs in $OUT)"
echo "failed:"; sort "$OUT"/FAILED 2>/dev/null
[ ! -s "$OUT/FAILED" ]

#!/usr/bin/env bash
# Bring the base game up to date before a new attempt (user, 2026-10-02:
# "make sure we merge in changes before each new attempt").
#
# The base game is ~/Developer/gen1recomp, upstream bryanthaboi's
# pokemon-gen1-recomp-project (branch dev). Our own commits on top of it
# export puzzle data as tables (boulder holes and barriers, switches, quiz
# machines); they are carried across by rebasing them onto upstream.
#
#   ./update_base.sh            fetch, rebase, re-import the ROM data, check
#   ./update_base.sh --check    only the checks, on the base as it stands
#
# NEVER while a chain runs: every attempt boots the game from this checkout.
# If a check fails, nothing is rolled back for you; the old commit and the
# command to return to it are printed, and the launch is the user's call.
set -uo pipefail
cd "$(dirname "$0")"
BASE="$HOME/Developer/gen1recomp"
ROM="${RED_ROM:-$HOME/Downloads/Pokemon - Red Version (USA, Europe).gb}"
UPSTREAM="${RED_BASE_UPSTREAM:-origin/dev}"

if pgrep -f "^bash ./fresh_discovery.sh|^bash ./campaign.sh|planner/executor.py --bootstrap" >/dev/null; then
  echo "!! a chain or executor is running; stop it first (./stop_all.sh)" >&2
  exit 2
fi

if [ "${1:-}" != "--check" ]; then
  if [ -n "$(git -C "$BASE" status --porcelain --untracked-files=no)" ]; then
    echo "!! $BASE has uncommitted changes; refusing to rebase over them" >&2
    exit 2
  fi
  OLD=$(git -C "$BASE" rev-parse HEAD)
  git -C "$BASE" fetch -q origin || { echo "!! fetch failed" >&2; exit 1; }
  BEHIND=$(git -C "$BASE" rev-list --count HEAD.."$UPSTREAM")
  echo "base: $BEHIND upstream commit(s) to take; ours on top:"
  git -C "$BASE" log --oneline "$UPSTREAM"..HEAD | sed 's/^/  /'
  if [ "$BEHIND" -gt 0 ]; then
    if ! git -C "$BASE" rebase -q "$UPSTREAM"; then
      git -C "$BASE" rebase --abort
      echo "!! our commits do not rebase cleanly onto $UPSTREAM; left at $OLD" >&2
      exit 1
    fi
    echo "rebased onto $UPSTREAM (was $OLD; back with: git -C $BASE reset --hard $OLD)"
  fi
  # The importer decodes the ROM into each LOVE identity; a newer base can
  # want a newer cache, and then boots to its launcher instead of the game.
  [ -f "$ROM" ] || { echo "!! no ROM at $ROM (set RED_ROM)" >&2; exit 1; }
  for ident in pokemon-love2d red-contract; do
    ( cd "$BASE" && POKEPORT_IDENTITY="$ident" POKEPORT_IMPORT_ROM="$ROM" \
        POKEPORT_IMPORT_ONLY=1 POKEPORT_FORCE_IMPORT=1 SDL_AUDIODRIVER=dummy timeout 900 \
        xvfb-run -a env -u WAYLAND_DISPLAY SDL_VIDEODRIVER=x11 love . \
        >/dev/null 2>&1 ) && echo "ROM data imported for $ident" \
      || { echo "!! ROM import failed for $ident" >&2; exit 1; }
  done
fi

# THE CHECKS: the observation contract on a new game and on the newest
# checkpoint, then every test that boots a game.
fail=0
echo "--- contract, new game"
POKEPORT_GAME=red python3 tests/contract.py --new-game 2>&1 | tail -1
[ "${PIPESTATUS[0]}" = 0 ] || fail=1
SAVE=$(ls -td run/saves/*/ 2>/dev/null | head -1)
if [ -n "$SAVE" ] && [ -f "${SAVE}slot1.lua" ]; then
  echo "--- contract, $SAVE"
  POKEPORT_GAME=red python3 tests/contract.py --save "${SAVE}slot1.lua" 2>&1 | tail -1
  [ "${PIPESTATUS[0]}" = 0 ] || fail=1
fi
echo "--- boot tests"
BOOTS=$(grep "^BOOTS=" tests/run_suite.sh | sed "s/^BOOTS='//; s/'\$//")
# pc_box needs two party members, and the live save is whatever the last run
# left (a fresh run has one): give it the newest checkpoint that has two
PCSAVE=$(python3 - <<'PY'
import re
from pathlib import Path
for d in sorted(Path("run/saves").glob("*/"), key=lambda p: p.stat().st_mtime, reverse=True):
    f = d / "slot1.lua"
    if f.exists() and len(re.findall(r'species\s*=', f.read_text(errors="ignore"))) >= 2:
        print(f); break
PY
)
for t in $(ls tests/*.py | grep -E "$BOOTS" | grep -v "contract.py"); do
  _args=()
  [ "$(basename "$t")" = "pc_box.py" ] && [ -n "$PCSAVE" ] && _args=(--save "$PCSAVE")
  if POKEPORT_GAME=red RED_BRIDGE_DIR="$(mktemp -d)" timeout 600 python3 "$t" "${_args[@]}" >/dev/null 2>&1; then
    :
  else
    echo "  FAIL $(basename "$t" .py)"; fail=1
  fi
done
echo "--- the no-game suite"
CLAUDE_SMOKE=1 tests/run_suite.sh 2>&1 | tail -1
if [ "$fail" = 0 ]; then
  echo "BASE OK: $(git -C "$BASE" log --oneline -1)"
else
  echo "!! BASE CHECKS FAILED: do not launch on it without a decision" >&2
  exit 1
fi

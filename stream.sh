#!/usr/bin/env bash
# One command for a streamed run: a new game played at 200x where nobody sees
# it, and on screen the HUD beside a 1x copy of that game (tools/shadow).
#
#   ./stream.sh            new game (fresh world, banked outline), windows up
#   ./stream.sh --resume   keep the world, carry on from where the chain stopped
#   ./stream.sh --attach   only the windows, for a chain that is already running
#   ./stream.sh --off      stop streaming: the copy and layout watcher stop, and a
#                          relaunched chain boots as before (run/stream.env removed)
#
# What it does, in order: refuses while a chain runs (except --attach); brings
# the base game up to date (update_base.sh: every new attempt starts on it);
# works out two half-screen tiles on the focused monitor; starts the chain
# headless and muted, its window the size of the copy's tile (the window's
# size is logic in this port, so the copy can only match a run of its size);
# places the copy left and the HUD right with runtime Hyprland rules (gone at
# the next `hyprctl reload`); starts the HUD and the copy. The copy follows
# each boot as the game restarts; its log is run/shadow.log.
#
# The run is the same run either way: the copy only reads what it recorded.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
MODE=new
case "${1:-}" in
  --resume) MODE=resume ;;
  --attach) MODE=attach ;;
  --off)
    rm -f run/stream.env
    for p in $(pgrep -f "^python3 -u tools/shadow/play.py --live" || true); do
      kill -TERM -- "-$(ps -o pgid= -p "$p" | tr -d ' ')" 2>/dev/null || true
    done
    pkill -f "^python3 tools/stream_layout.py" 2>/dev/null || true
    echo "[stream] off: copy and layout watcher stopped; the next chain launch boots as before"
    exit 0 ;;
  "") ;;
  *) echo "usage: $0 [--resume|--attach|--off]"; exit 2 ;;
esac

if ! grep -q 'RED_WINDOW' harness/shim.lua || ! grep -q '_headed=()' fresh_run.sh; then
  echo "the headless + RED_WINDOW boot pieces are not applied (pending_next_stop/stream-launch)"; exit 1
fi
running=$(pgrep -f "fresh_discovery.sh" || true)
if [ "$MODE" != attach ] && [ -n "$running" ]; then
  echo "a chain is running (pids: $running): stop it first (./stop_all.sh), or use --attach"; exit 1
fi

# the two tiles, from the focused monitor and the gaps/borders in use
read -r W H LX LY RX RY FW < <(python3 - <<'EOF'
import json, subprocess
def opt(name):
    d = json.loads(subprocess.check_output(["hyprctl", "getoption", name, "-j"]))
    v = d.get("custom") or d.get("int")
    return int(str(v).split()[0])
# a real monitor: when the display is off or its link drops, Hyprland puts a
# 1920x1080 stand-in (FALLBACK, or HEADLESS-n) in its place, and tiles sized
# from it shrink the run. None: print nothing, and the last real tiles are used
mons = [m for m in json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
        if not m["name"].startswith(("HEADLESS", "FALLBACK"))]
if not mons:
    raise SystemExit(0)
mon = next((m for m in mons if m["focused"]), mons[0])
gi, go, b = opt("general:gaps_in"), opt("general:gaps_out"), opt("general:border_size")
rl, rt, rr, rb = mon["reserved"]
sw, sh = int(mon["width"] / mon["scale"]), int(mon["height"] / mon["scale"])
x0, y0 = mon["x"] + rl + go, mon["y"] + rt + go
uw, uh = sw - rl - rr - 2 * go, sh - rt - rb - 2 * go
col = (uw - 2 * gi) // 2
w, h = col - 2 * b, uh - 2 * b
w -= w % 2; h -= h % 2                       # the game keeps even sizes
fw = uw - 2 * b
fw -= fw % 2
print(w, h, x0 + b, y0 + b, x0 + col + 2 * gi + b, y0 + b, fw)
EOF
) || true   # nothing printed: no real monitor (below)
if [ -n "${W:-}" ]; then
  echo "$W $H $LX $LY $RX $RY $FW" > run/stream.tiles
elif [ -f run/stream.tiles ]; then
  read -r W H LX LY RX RY FW < run/stream.tiles
  echo "[stream] no real monitor (the display is off): the last real tiles"
else
  echo "[stream] no real monitor (the display is off) and no earlier tiles: launch once it is on"; exit 1
fi
echo "[stream] tiles ${W}x${H}: copy at ${LX},${LY}, HUD at ${RX},${RY}"

# the stream settings, kept for every relaunch while streaming (fresh_discovery.sh reads them).
# --attach keeps the ones a running chain already boots with: the run's window
# size is its view, so it changes only with a launch
if [ "$MODE" = attach ] && [ -f run/stream.env ]; then
  W=$(sed -n 's/^RED_WINDOW=\([0-9]*\)x[0-9]*$/\1/p' run/stream.env)
  H=$(sed -n 's/^RED_WINDOW=[0-9]*x\([0-9]*\)$/\1/p' run/stream.env)
else
cat > run/stream.env <<EOF2
RED_HEADED=0
RED_MUTE=1
RED_WINDOW=${W}x${H}
RED_DRAW_EVERY=${RED_DRAW_EVERY:-30}
EOF2
fi

if [ "$MODE" != attach ]; then
  ./update_base.sh || { echo "[stream] the base update failed; launching on the old base is your call"; exit 1; }
  [ "$MODE" = new ] && rm -f run/outline_leg
  (RED_HEADED=0 RED_MUTE=1 RED_WINDOW="${W}x${H}" RED_DRAW_EVERY="${RED_DRAW_EVERY:-30}" RED_NUM_CTX="${RED_NUM_CTX:-32768}" \
     setsid nohup systemd-inhibit --mode=block --what=sleep:idle --why="red-recomp chain" \
     ./fresh_discovery.sh 4 >> run/chain.log 2>&1 < /dev/null &)
  echo "[stream] chain started ($MODE), headless at ${W}x${H}"
fi

# the copy is the only love window on screen (the run's is headless)
hyprctl -q keyword windowrule "match:class ^(love)$, float on"
hyprctl -q keyword windowrule "match:class ^(love)$, size $W $H"
hyprctl -q keyword windowrule "match:class ^(love)$, move $LX $LY"
hyprctl -q keyword windowrule "match:title ^(red-recomp HUD)$, float on"
hyprctl -q keyword windowrule "match:title ^(red-recomp HUD)$, size $W $H"
hyprctl -q keyword windowrule "match:title ^(red-recomp HUD)$, move $RX $RY"

if ! pgrep -f "tools/hud.py" >/dev/null; then
  setsid kitty --title "red-recomp HUD" python3 tools/hud.py >/dev/null 2>&1 < /dev/null &
else
  # a HUD already open was placed before the rules existed: put it there too
  hyprctl -q dispatch setfloating "title:^(red-recomp HUD)$" || true
  hyprctl -q dispatch resizewindowpixel exact "$W" "$H",title:"^(red-recomp HUD)$" || true
  hyprctl -q dispatch movewindowpixel exact "$RX" "$RY",title:"^(red-recomp HUD)$" || true
fi
# the old copy with its game: play.py runs under setsid, so its group is both
# (never this script's own group, in case a pattern ever matches it)
me=$(ps -o pgid= -p $$ | tr -d ' ')
for p in $(pgrep -f "^python3 -u tools/shadow/play.py --live" || true); do
  g=$(ps -o pgid= -p "$p" | tr -d ' ')
  [ -n "$g" ] && [ "$g" != "$me" ] && kill -TERM -- "-$g" 2>/dev/null || true
done
# which battles the copy shows: bosses only (gym leaders, the rival, Giovanni,
# the Elite Four, the champion, event fights); trainer fights at 1x put it
# ~10 min behind per 18 of the run (2026-10-03). SHADOW_SHOW_BATTLES=trainers
# or all to see more.
export SHADOW_SHOW_BATTLES="${SHADOW_SHOW_BATTLES:-bosses}"
# the copy as the plain game (user, 2026-10-05: "fully disable the mod and just
# go au natural"). SHADOW_MOD=dramatic brings the Dramatic Shape mod back
# (tools/shadow/dramatic.py: a patched private copy, logic-neutral), with
# SHADOW_VOXEL=0 SHADOW_TILT=0 SHADOW_DS_OPTS=battles=stadium for its Pokemon
# Stadium battles on the flat map, or SHADOW_VOXEL=3 for the voxel diorama.
# Drawn on the discrete GPU (Mesa defaults to the CPU's integrated one here).
export SHADOW_MOD="${SHADOW_MOD-}"
export DRI_PRIME="${DRI_PRIME-1}"
# the copy's COLORS (draw-only): empty is the run's own (SGB);
# SHADOW_COLORS=redpp for ADVANCED
export SHADOW_COLORS="${SHADOW_COLORS-}"
since=()
[ "$MODE" != attach ] && since=(--since "$(date +%s)")   # only this launch's boots
setsid nohup python3 -u tools/shadow/play.py --live "${since[@]}" >> run/shadow.log 2>&1 < /dev/null &
# the HUD across the whole screen while the model authors and the copy is idle
pkill -f "^python3 tools/stream_layout.py" 2>/dev/null || true
setsid nohup python3 tools/stream_layout.py "$W" "$H" "$LX" "$LY" "$RX" "$RY" "$FW" \
  >/dev/null 2>&1 < /dev/null &
echo "[stream] HUD and 1x copy up (copy log: run/shadow.log)"

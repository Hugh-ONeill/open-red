#!/usr/bin/env python3
"""A press in a room with people not yet present waits for its scene, so whoever
the scene brings is on the very next page — named in the press's own answer.

Run 42, 2026-10-10: the Cell Separator's press came back before its queued
scene (sound effects that play in real time while the game runs at 200x), the
page after it listed only the separator, and a run whose step pointed
elsewhere walked out through the scene and never saw human Bill, who holds the
S.S. Ticket; nothing pulled it back. Run 41 only got the ticket because its
next round happened to press something else in the room. Probed on run 42's
own save: the press now answers "ok — and then BILLSHOUSE_BILL1 appeared in
this room" and the next observation has him at (4,4); a press with no scene in
such a room costs ~0.05 s more.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "harness/shim.lua").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

ck("the room's absent PEOPLE are taken before a press (item balls never count)",
   'wd.press_absent = (cmd.op == "interact") and wd.absent_names(G) or nil' in src
   and "and not od.item then" in src)
i_adv = src.index('wd_run(G, "advance_to_decision", OP_FRAME_BUDGET, advance_to_decision, G)\n    if wd.press_absent then')
i_obs = src.index("observe(G, seq, result)", i_adv)
ck("the wait runs after the press's own text is closed, before the observation",
   0 < i_adv < src.index('wd_run(G, "reveal_wait"', i_adv) < i_obs)
ck("...in wall-clock time, only while a scene shows, at most 4 s",
   "local deadline, quiet_since = t0 + 4, nil" in src and "scene_on()" in src
   and "quiet_since > 0.25" in src)
ck("...and the press's answer names who appeared, by public name",
   '" appeared in this room"' in src and "pn.object(ow.map.id, npc.def" in src)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

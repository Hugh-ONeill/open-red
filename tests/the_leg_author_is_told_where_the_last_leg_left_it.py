#!/usr/bin/env python3
"""The leg author is told where the last leg left the party: the place it
came into, what it came through, whether that ground is new, and what is
still unknown there.

Run of record 11 (2026-09-27): "Reach Lavender Town" was written standing
at Rock Tunnel's south mouth, on ground the run had never stood on, its
south side never on screen, and the author was told only that "Exit Rock
Tunnel" was done. It wrote Route 11 -> 12 -> 13 -> 14 -> 15, a heal went
in front, and the run walked back through the tunnel, away from the one
place it had just reached (user: "i wish it remembered what it was doing
and went right back").

Pinned: on a leg's first authoring the line names the finished leg, the
place, the way in, that it is new, its unseen spots and its unseen side;
on a rewrite mid-leg it says how the party came to stand where it is; it
says nothing when the journal's last arrival is not where the party
stands; it names no destination; build_prompt carries it. Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp(prefix="lastleg_"))
run, plans = tmp / "run", tmp / "plans"
run.mkdir()
plans.mkdir()
(plans / "outline.txt").write_text(
    "Reach Rock Tunnel\nExit Rock Tunnel\nReach Lavender Town\n")
(run / "outline_leg").write_text("2")
(run / "leg_start.leg").write_text("2")          # the baseline is leg 2's
(run / "obs.json").write_text(json.dumps({"map": {"id": "ROUTE_10"}}))
(run / "executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"kind": "explored", "frm": "ROUTE_10|0,4", "via": "8,17",
     "to": "ROCK_TUNNEL_1F|14,2", "t": 1},
    {"kind": "battle_turn", "t": 2},
    {"kind": "explored", "frm": "ROCK_TUNNEL_1F|24,16", "via": "15,33",
     "to": "ROUTE_10|14,52", "t": 3},
]) + "\n")
(run / "explored.json").write_text(json.dumps({
    "visits": {"ROUTE_10|0,4": 3, "ROUTE_10|14,52": 1},
    "frontier": {"ROUTE_10|0,4": ["west"]},
    "region_seen": {"ROUTE_10|14,52": 6},
    "sides_unseen": {"ROUTE_10": ["south"]}}))

line = A.last_leg_left_you(run, plans)
ck("the first authoring names the leg just finished",
   "WHERE THE LAST LEG LEFT YOU: 'Exit Rock Tunnel' was finished" in line, line)
ck("...the place it came into and what it came through",
   "came into ROUTE_10|14,52 from ROCK_TUNNEL_1F|24,16" in line, line)
ck("...that the ground is new",
   "the first time this run ever stood there" in line, line)
ck("...the spots still unknown there", "6 spot(s) there" in line, line)
ck("...and the side never on screen, as an open question",
   "its south side has never been on screen (what lies southward is not known)"
   in line, line)
ck("it names no destination",
   not any(w in line for w in ("LAVENDER", "Lavender", "go ", "should")), line)

(run / "leg_start.leg").write_text("3")          # leg 3 has begun
line = A.last_leg_left_you(run, plans)
ck("a rewrite mid-leg says how the party came to stand there",
   line.startswith("\n\nHOW YOU CAME TO BE WHERE YOU ARE: you last came into "
                   "ROUTE_10|14,52"), line)

(run / "obs.json").write_text(json.dumps({"map": {"id": "CERULEAN_CITY"}}))
ck("nothing is said when the last arrival is not where the party stands",
   A.last_leg_left_you(run, plans) == "")

src = (ROOT / "planner/author.py").read_text()
ck("build_prompt carries it, beside the outline so far",
   "+ outline_so_far()\n        + last_leg_left_you()" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

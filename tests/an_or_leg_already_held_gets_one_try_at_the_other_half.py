#!/usr/bin/env python3
"""A type leg written as an "or" that the party already satisfies on
arrival gets one non-fatal attempt at the half it lacks, and is then done
either way.

2026-09-24. The outline author writes half its type legs as pairs, and a
pair is done the moment either type is held. A Bulbasaur start crossed off
"WATER or GRASS" untouched; a Squirtle start crossed off every "X or
WATER" on the list, which was most of them, and the party was never built
(user: "kinda have to do it if we have half the list already fulfilled by
squirtle"). The rule is the user's design, the one-attempt version: read
which half is held, run one attempt at the other, written in the model's
own words minus the half it has, then cross the leg off as it would have
been. What to catch, and whether, stays the plan's.

Pinned: the other half is derived only for an "or" type leg with one side
held and another not; the article follows the type; a leg holding none is
not this rule's (it is not accomplished); nothing is derived for a
single-type leg or a leg that is not a type leg; the CLI reads the party's
types from the observation and prints the derived leg or nothing; the
chain runs it only inside the judged-already-accomplished branch, after
the mark is written, with one campaign attempt, never fatal, with a
journal row, and sweeps on afterwards. Synthetic."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import or_leg as O  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


M = O.missing_branch
ck("a pair with the GRASS half held asks for the WATER half",
   M("the party holds a WATER or GRASS type", {"GRASS", "POISON"}) == "the party holds a WATER type")
ck("...and the other way round",
   M("the party holds a WATER or GRASS type", {"WATER"}) == "the party holds a GRASS type")
ck("the article follows the type",
   M("the party holds a FIRE or ELECTRIC type", {"FIRE"}) == "the party holds an ELECTRIC type")
ck("a triple with one held keeps the other two as an or",
   M("the party holds a FIRE or ICE or PSYCHIC type", {"FIRE", "FLYING"})
   == "the party holds an ICE or PSYCHIC type")
ck("holding every half is nothing to do", M("the party holds a WATER or GRASS type", {"WATER", "GRASS"}) == "")
ck("holding none is not this rule's: the leg is not accomplished",
   M("the party holds a WATER or GRASS type", {"FIRE"}) == "")
ck("a single-type leg is nothing", M("the party holds a FLYING type", {"NORMAL"}) == "")
ck("a leg that is not a type leg is nothing",
   M("every party member is at least level 12", {"GRASS"}) == ""
   and M("Reach Celadon City", {"GRASS"}) == "")

d = Path(tempfile.mkdtemp())
obs = {"party": [{"species": "BULBASAUR", "types": ["GRASS", "POISON"]},
                 {"species": "PIDGEY", "types": ["NORMAL", "FLYING"]}]}
(d / "obs.json").write_text(json.dumps(obs))
r = subprocess.run([sys.executable, str(ROOT / "planner/or_leg.py"),
                    "the party holds a WATER or GRASS type", str(d / "obs.json")],
                   capture_output=True, text=True)
ck("the CLI reads the party's types and prints the other half",
   r.returncode == 0 and r.stdout.strip() == "the party holds a WATER type", r.stdout)
r2 = subprocess.run([sys.executable, str(ROOT / "planner/or_leg.py"),
                     "the party holds a FLYING or NORMAL type", str(d / "obs.json")],
                    capture_output=True, text=True)
ck("...and prints nothing, exit 1, when there is nothing to try",
   r2.returncode == 1 and r2.stdout.strip() == "", r2.stdout)
ck("the held types are read off every member", O.held_types(obs) == {"GRASS", "POISON", "NORMAL", "FLYING"})

SH = (ROOT / "fresh_discovery.sh").read_text()
i = SH.index("judged already accomplished before running")
j = SH.index("sweep_ahead \"$i\"\n    continue", i)
blk = SH[i:j]
ck("the chain tries the other half only inside the already-accomplished branch, after the mark",
   'echo "$i" > "$PROGRESS"' in blk
   and 'python planner/or_leg.py "$leg"' in blk
   and blk.index('echo "$i" > "$PROGRESS"') < blk.index("or_leg.py"))
ck("...with one campaign attempt, never fatal",
   './campaign.sh 1 "$_bp" -- --escalate || true' in blk)
ck("...its plan under its own name, so no leg's plan is reused or overwritten",
   '_bonus_' in blk and '--out "$_bp"' in blk)
ck("...and a journal row for the attempt",
   'or_leg.py --record "$leg" "$_bonus"' in blk and '"kind": "or_leg_bonus"' in (ROOT / "planner/or_leg.py").read_text())
ck("...and a plan that cannot be written leaves the leg done",
   "the leg stands done" in blk)
ck("...then sweeps on as before", SH[j:j + 60].startswith('sweep_ahead "$i"\n    continue'))
s = SH.index("sweep_ahead() {")
sweep = SH[s:SH.index("\n}\n", s)]
ck("the look-ahead sweep leaves such a leg alone, so it reaches its own turn",
   'python planner/or_leg.py "$_st" >/dev/null 2>&1' in sweep
   and "not swept:" in sweep
   and sweep.index("or_leg.py") < sweep.index("skip_legs.py"))
ck("...and skips nothing when the sweep's whole list was such legs",
   'if [ -n "$got" ] && python planner/skip_legs.py $nums; then' in sweep)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

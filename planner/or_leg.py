#!/usr/bin/env python3
"""AN "OR" HELD ON ARRIVAL STILL GETS ONE TRY AT ITS OTHER HALF.

"the party holds a WATER or GRASS type" is done the moment either is held,
so with a Bulbasaur in the party it was crossed off at the boundary and
nothing was caught; with a Squirtle, every "X or WATER" leg on the list
went the same way, which is half the type legs the outline author writes
(2026-09-24, user: "it satisfies all those catch goals by picking squirt at
the start which would prevent any of the non-water types from being
caught ... kinda have to do it if we have half the list already fulfilled
by squirtle").

So when the chain finds such a leg already accomplished, it reads which
half the party holds and which it does not, and runs ONE non-fatal attempt
at the other half — "the party holds a GRASS type", the model's own words
minus the half it has — before crossing the leg off, which it does either
way. A scheduling rule about party building, nothing told to the model:
what to catch, and whether, stays the plan's.

  or_leg.py "the party holds a WATER or GRASS type"            # prints the other half, or nothing
  or_leg.py --record LEG BONUS                                  # journal row for the attempt
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

OBS = Path("run/obs.json")
JOURNAL = Path("run/executor_log.jsonl")
LEG = re.compile(r"^the party holds an? ([A-Z]+(?: or [A-Z]+)+) type$")


def held_types(obs: dict | None) -> set:
    out = set()
    for mon in ((obs or {}).get("party") or []):
        for t in (mon.get("types") or []):
            out.add(str(t).upper())
    return out


def missing_branch(leg: str, held: set) -> str:
    """The leg with the held half removed, or "" when the leg is not an
    "or" type leg, holds none of its types yet (not accomplished, so not
    this rule's), or holds every one of them."""
    m = LEG.match(str(leg or "").strip())
    if not m:
        return ""
    types = m.group(1).split(" or ")
    have = [t for t in types if t in held]
    want = [t for t in types if t not in held]
    if not have or not want:
        return ""
    art = "an" if want[0][0] in "AEIOU" else "a"
    return f"the party holds {art} {' or '.join(want)} type"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--record":
        leg, bonus = argv[1], argv[2]
        try:
            obs = json.loads(OBS.read_text() or "{}")
        except (OSError, ValueError):
            obs = {}
        with JOURNAL.open("a") as f:
            f.write(json.dumps({"t": time.time(), "kind": "or_leg_bonus",
                                "leg": leg, "bonus": bonus,
                                "held": sorted(held_types(obs))}) + "\n")
        return 0
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    obs_path = Path(argv[1]) if len(argv) > 1 else OBS
    try:
        obs = json.loads(obs_path.read_text() or "{}")
    except (OSError, ValueError):
        return 1
    out = missing_branch(argv[0], held_types(obs))
    if not out:
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

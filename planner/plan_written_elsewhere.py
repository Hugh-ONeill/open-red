#!/usr/bin/env python3
"""Was this plan written from somewhere other than where the run stands?

A PLAN IS WRITTEN FROM A PLACE. Its travel steps say where to go next from
there, and a rewrite is always written from wherever the run was stuck
mid-leg. Picked up again from somewhere else, those steps are walked
literally: "Obtain the FRESH WATER" v1, written in Rock Tunnel, opened
with exit_rock_tunnel -> ROUTE_10, and the run, standing in the Celadon
Pokemon Center with the store two doors away, walked thirteen legs back
through Lavender and the tunnel to satisfy it, then thirteen legs back
(run 27, 2026-09-17). find_plan.py finds a plan by its objective, which is
right, and which is exactly how a plan from elsewhere comes back.

The plan records the map it was written from (author.py). This says
whether the run stands somewhere else now, and nothing about whether the
plan would still work: a plan from elsewhere is asked for again from here.
A plan with no record makes no claim.

Usage: plan_written_elsewhere.py <plan.json> [<map the run stands on>]
Prints "<written from> (the run stands on <here>)" and exits 0 when they
differ; exits 3 otherwise.
"""
import json
import sys
from pathlib import Path


def map_now() -> str:
    for src in ("run/obs.json", "run/last_state.json"):
        try:
            d = json.loads(Path(src).read_text() or "{}")
        except (OSError, ValueError):
            continue
        m = d.get("map")
        mid = m.get("id") if isinstance(m, dict) else m
        if mid:
            return str(mid)
    return ""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    try:
        plan = json.loads(Path(sys.argv[1]).read_text())
    except (OSError, ValueError):
        sys.exit(3)
    frm = str((plan or {}).get("written_from") or "")
    here = sys.argv[2] if len(sys.argv) > 2 else map_now()
    if not frm or not here or frm == here:
        sys.exit(3)
    print(f"{frm} (the run stands on {here})")


if __name__ == "__main__":
    main()

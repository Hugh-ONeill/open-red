#!/usr/bin/env python3
"""Is each arena still a fight? Ask the medicine.

AN ARENA THAT EVERYONE SWEEPS MEASURES NOTHING, and after the lead and
switch orders landed, eight of the nine were swept by every candidate
(2026-09-15, user: "we have to ensure each fight is still challenging ...
until it essentially forces usage of items to not die").

The target is exact and it is testable: take one spec, and take the SAME
spec with its healing rules cut out. A room is calibrated when the first
one wins it and the second one does not. Anything both win is too easy;
anything neither wins is too hard, and a room nobody can take is as
silent as a room everybody can.

Nothing else differs between the two — same move scoring, same lead,
same switches, same party, same bag — so the gap between them is the
medicine and only the medicine.

  calibrate_arenas.py --spec plans/policy_model_v9.json
  calibrate_arenas.py --spec ... --only cerulean --trials 2
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOMS = ["pewter", "cerulean", "vermilion", "celadon", "fuchsia",
         "saffron", "cinnabar", "viridian"]


def strip_medicine(spec: dict) -> dict:
    out = dict(spec)
    out["name"] = str(spec.get("name") or "spec") + "_nomeds"
    out["battle_items"] = []
    out["field_heal"] = None
    out["field_cure"] = []
    out.pop("provenance", None)
    return out


def score(arena: str, spec_path: Path, trials: int) -> tuple:
    """(beaten, of, blackouts) for one spec in one arena."""
    r = subprocess.run(
        [sys.executable, "-u", str(REPO / "planner/policy_author.py"),
         "--arenas", arena, "--eval-only", str(spec_path),
         "--trials", str(trials)],
        capture_output=True, text=True, cwd=REPO, timeout=3600)
    beat = of = black = None
    for line in r.stdout.splitlines():
        if ": beat " in line or "] beat " in line:
            try:
                head = line.split("beat ", 1)[1]
                beat, rest = head.split("/", 1)
                of = rest.split(" ", 1)[0]
                black = line.split("blackouts ", 1)[1].split(";")[0]
                beat, of, black = int(beat), int(of), int(black)
            except (ValueError, IndexError):
                continue
            break                   # the first line is the spec we asked for
    return beat, of, black


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", type=Path,
                    default=REPO / "plans/policy_model_v9.json")
    ap.add_argument("--only", default="")
    ap.add_argument("--trials", type=int, default=2)
    a = ap.parse_args()
    full = json.loads(a.spec.read_text())
    bare = strip_medicine(full)
    with tempfile.TemporaryDirectory() as td:
        bare_p = Path(td) / "nomeds.json"
        bare_p.write_text(json.dumps(bare, indent=1))
        print(f"{'arena':11s} {'with medicine':>14s} {'without':>10s}   verdict")
        for room in ROOMS:
            if a.only and room != a.only:
                continue
            w = score(room, a.spec, a.trials)
            n = score(room, bare_p, a.trials)
            if None in w or None in n:
                print(f"{room:11s} {'?':>14s} {'?':>10s}   COULD NOT SCORE")
                continue
            wf = w[0] / max(1, w[1])
            nf = n[0] / max(1, n[1])
            # A ROOM IS CALIBRATED WHEN THE MEDICINE DECIDES IT, not when
            # the healing spec is flawless. The first rule demanded a
            # perfect sweep, so Vermilion — which blacks out in EVERY
            # trial without healing and in one of four with it — was
            # filed as "hard" for losing a single fight out of sixteen
            # (2026-09-15). What matters is the gap: win most of the
            # room, and cost real blackouts when the medicine is taken
            # away.
            swing = n[2] - w[2]
            if wf >= 0.85 and swing >= a.trials / 2:
                verdict = "CALIBRATED — the medicine is what wins it"
            elif nf >= 0.85 and swing <= 0:
                verdict = "TOO EASY — it is won without healing at all"
            elif swing >= a.trials / 2:
                verdict = (f"HARD — medicine decides it ({swing} fewer "
                           f"blackouts) but only wins {wf:.0%}")
            elif wf < 0.5:
                verdict = "TOO HARD — healing does not save it"
            elif swing <= 0:
                verdict = "TOO EASY — healing costs it nothing"
            else:
                verdict = (f"THIN — medicine is worth only {swing} "
                           f"blackout(s) across {a.trials} trials")
            print(f"{room:11s} {w[0]:>6d}/{w[1]:<3d} b{w[2]:<2d} "
                  f"{n[0]:>3d}/{n[1]:<3d} b{n[2]:<2d}   {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

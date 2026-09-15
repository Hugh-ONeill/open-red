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
         "saffron", "cinnabar", "viridian", "e4", "e4_ideal"]


def strip_medicine(spec: dict) -> dict:
    out = dict(spec)
    out["name"] = str(spec.get("name") or "spec") + "_nomeds"
    out["battle_items"] = []
    out["field_heal"] = None
    out["field_cure"] = []
    out.pop("provenance", None)
    return out


def score(arena: str, spec_path: Path, trials: int) -> tuple:
    """(beaten, of, blackouts) for one spec in one arena.

    ONE ROOM THAT WILL NOT FINISH MUST NOT TAKE THE SWEEP WITH IT. The
    timeout was raised, not caught, so when the league arena wedged in a
    fight that could not resolve the whole run died on an unhandled
    TimeoutExpired an hour later — with eight rooms already measured and
    two still to go, and nothing written down to say which room it was
    (2026-09-15). A room that runs out of its hour has failed to score,
    which is a result the table can print."""
    try:
        r = subprocess.run(
            [sys.executable, "-u", str(REPO / "planner/policy_author.py"),
             "--arenas", arena, "--eval-only", str(spec_path),
             "--trials", str(trials)],
            capture_output=True, text=True, cwd=REPO, timeout=3600)
    except subprocess.TimeoutExpired:
        print(f"  [{arena}: gave up after an hour]", flush=True)
        return None, None, None
    beat = of = black = None
    for line in r.stdout.splitlines():
        # the gyms report "beat X/Y of the room", the league "Elite Four
        # rooms cleared X/Y" — same measurement, two sentences
        _mark = ("rooms cleared " if "rooms cleared " in line
                 else "beat " if (": beat " in line or "] beat " in line)
                 else "")
        if _mark:
            try:
                head = line.split(_mark, 1)[1]
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
    ap.add_argument("--only", default="",
                    help="one room, or several separated by commas")
    ap.add_argument("--trials", type=int, default=2)
    a = ap.parse_args()
    full = json.loads(a.spec.read_text())
    bare = strip_medicine(full)
    with tempfile.TemporaryDirectory() as td:
        bare_p = Path(td) / "nomeds.json"
        bare_p.write_text(json.dumps(bare, indent=1))
        # SAY WHAT THE DENOMINATOR IS. A room that scores one flag over
        # four trials printed "4/4", which reads as four fights — and
        # Saffron fights FIVE battles a trial to reach the one flag it
        # scores (user, 2026-09-15: "i was misreading the 4/4 as having
        # only 4 fights"). Rooms that score one flag are reported as
        # trials won; rooms that score many are reported as fights.
        print(f"{'arena':11s} {'with medicine':>18s} {'without':>14s}   "
              f"verdict")
        want = {r.strip() for r in a.only.split(",") if r.strip()}
        for room in ROOMS:
            if want and room not in want:
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
            # A ROOM THAT WIPES YOU EVERY TRIAL IS NOT EASY. The rule
            # fell through to "won without healing at all" whenever the
            # blackout swing was zero, so Cerulean — which blacked the
            # party out in ALL FOUR trials with medicine and all four
            # without — was reported as too easy when it was beating
            # them outright (2026-09-15).
            if w[2] >= a.trials and swing <= 0:
                verdict = ("TOO HARD — it wipes every trial, with medicine "
                           "and without")
            elif wf >= 0.85 and swing >= a.trials / 2:
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
            unit = "trials won" if w[1] == a.trials else "fights"
            print(f"{room:11s} {w[0]:>3d}/{w[1]:<3d} b{w[2]:<2d} "
                  f"{n[0]:>4d}/{n[1]:<3d} b{n[2]:<2d} "
                  f"{unit:<10s}  {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

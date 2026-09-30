#!/usr/bin/env python3
"""Is each arena still a fight? Take one faculty away and see.

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

...AND THE FACULTY IS AN ARGUMENT NOW (user, 2026-09-21: "we might have to
recalibrate to seperate out policies, the previous calibration was to
seperate item usage from no item usage, this might have to be calibrated
differently"). The nine rooms were calibrated to separate a spec that heals
from one that does not, and they do that well. They say nothing about a
spec that uses STATUS MOVES, because a room whose every candidate sweeps it
cannot: v15's four candidates tied at 8.24-8.41 of 9.00, six rooms cleared
perfectly by all of them. Which faculty the twin loses is now `--strip`,
and a room is calibrated FOR THAT FACULTY when losing it costs the room.

A ROOM CAN BE DECIDED TWO WAYS. Medicine shows up as blackouts: take it
away and the party dies. A status move need not — it can show up as fights
won, or as nothing at all. So both are measured and either can decide a
room, and both are printed whatever the answer.

  calibrate_arenas.py --spec plans/policy_model_v12.json
  calibrate_arenas.py --spec ... --path real
  calibrate_arenas.py --spec ... --only cerulean_ideal,e4_real --trials 2
  calibrate_arenas.py --spec plans/policy_model_v15.json --strip setup
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GYM_ROOMS = ["pewter", "cerulean", "vermilion", "celadon", "fuchsia",
             "saffron", "cinnabar", "viridian"]


def rooms(path: str) -> list:
    """The nine rooms of one path, in game order, the league last.

    TWO PATHS, TWO TABLES (user, 2026-09-15). `real` is the party the
    model-authored runs carried into each room with the handful of
    medicine a run has been seen to buy; `ideal` is the party a player
    would build, five under the ace, with the shelf in the bag. The same
    spec is read in both, and a room is calibrated per path."""
    return [f"{r}_{path}" for r in GYM_ROOMS] + [f"e4_{path}"]


def strip_medicine(spec: dict) -> dict:
    out = dict(spec)
    out["name"] = str(spec.get("name") or "spec") + "_nomeds"
    out["battle_items"] = []
    out["field_heal"] = None
    out["field_revive"] = None
    out["field_cure"] = []
    out.pop("provenance", None)
    return out


def strip_setup(spec: dict) -> dict:
    """The same spec with no deliberate status-move rules.

    A 0-power move is never picked by score while a damaging move has PP,
    so emptying `setup` is the whole of taking status away: the twin can
    still switch, still heal, still cure, and simply never spends a turn
    putting something on a foe."""
    out = dict(spec)
    out["name"] = str(spec.get("name") or "spec") + "_nosetup"
    out["setup"] = []
    out.pop("provenance", None)
    return out


def strip_pp(spec: dict) -> dict:
    """The same spec that will not switch out a Pokemon with nothing left
    to throw. Only the out_of_pp rules go; every other switch stays."""
    out = dict(spec)
    out["name"] = str(spec.get("name") or "spec") + "_nopp"
    out["switch"] = [r for r in (spec.get("switch") or [])
                     if not (isinstance(r, dict) and r.get("out_of_pp"))]
    out.pop("provenance", None)
    return out


def strip_switch(spec: dict) -> dict:
    """The same spec that never switches mid-battle."""
    out = dict(spec)
    out["name"] = str(spec.get("name") or "spec") + "_noswitch"
    out["switch"] = []
    out.pop("provenance", None)
    return out


# what each faculty is called in the table, and what taking it away means
# the spec key each faculty lives in, so an empty one can be refused
_KEYS = {"medicine": "battle_items", "setup": "setup", "pp": "switch",
         "switch": "switch"}
FACULTIES = {
    "medicine": (strip_medicine, "medicine", "healing"),
    "setup": (strip_setup, "status moves", "a status move"),
    "pp": (strip_pp, "the out-of-PP switch", "switching when dry"),
    "switch": (strip_switch, "switching", "switching"),
}


def score(arena: str, spec_path: Path, trials: int, arm: str = "") -> tuple:
    """(beaten, of, blackouts) for one spec in one arena.

    THE ARM'S OWN JOURNAL IS KEPT, and its trial lines are printed. The
    arena writes its journal into run/policyarena/<arena>/ and starts it
    empty at every boot, so scoring the stripped arm after the medicine
    arm left nothing to say whether the medicine was ever spent — the
    league on the real path came back 7/10 in both arms (2026-09-15) and
    the only journal on disk was the one with no items in it. Each arm's
    journal is copied aside as executor_log.<arm>.jsonl, and the runner's
    per-trial lines go into this log rather than into a pipe.

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
    if arm:
        src = REPO / "run/policyarena" / arena / "executor_log.jsonl"
        try:
            (src.parent / f"executor_log.{arm}.jsonl").write_bytes(
                src.read_bytes())
        except OSError:
            pass
        for line in r.stdout.splitlines():
            if line.startswith("  trial "):
                print(f"    [{arena} {arm}] {line.strip()}", flush=True)
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
    ap.add_argument("--path", choices=["real", "ideal", "both"],
                    default="both", help="which path's rooms to score")
    ap.add_argument("--strip", choices=sorted(FACULTIES), default="medicine",
                    help="which faculty the twin loses; a room is "
                         "calibrated for the faculty that decides it")
    a = ap.parse_args()
    full = json.loads(a.spec.read_text())
    _strip, _noun, _doing = FACULTIES[a.strip]
    bare = _strip(full)
    if json.dumps(bare.get(_KEYS[a.strip]), sort_keys=True) == json.dumps(
            full.get(_KEYS[a.strip]), sort_keys=True):
        print(f"{a.spec.name} has no {_noun} to take away — the two arms "
              f"would be the same spec, and every room would read TOO EASY.")
        return 2
    with tempfile.TemporaryDirectory() as td:
        bare_p = Path(td) / "stripped.json"
        bare_p.write_text(json.dumps(bare, indent=1))
        # SAY WHAT THE DENOMINATOR IS. A room that scores one flag over
        # four trials printed "4/4", which reads as four fights — and
        # Saffron fights FIVE battles a trial to reach the one flag it
        # scores (user, 2026-09-15: "i was misreading the 4/4 as having
        # only 4 fights"). Rooms that score one flag are reported as
        # trials won; rooms that score many are reported as fights.
        print(f"spec {a.spec.name}: {_noun} against no {_noun}, "
              f"{a.trials} trial(s) a room")
        print(f"{'arena':16s} {'with':>18s} {'without':>14s}   verdict")
        want = {r.strip() for r in a.only.split(",") if r.strip()}
        paths = ("real", "ideal") if a.path == "both" else (a.path,)
        for room in [r for pth in paths for r in rooms(pth)]:
            if want and room not in want:
                continue
            w = score(room, a.spec, a.trials, arm="with")
            n = score(room, bare_p, a.trials, arm="without")
            if None in w or None in n:
                print(f"{room:16s} {'?':>14s} {'?':>10s}   COULD NOT SCORE")
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
            # ...AND THE FIGHTS, BESIDE THE BLACKOUTS. Medicine decides a
            # room by keeping the party alive, so blackouts were the whole
            # test. A status move can decide one without saving a life —
            # it wins fights that would otherwise be lost — and a room
            # where the stripped arm wipes no more often but clears two
            # fewer fights is still a room that measures it.
            gap = wf - nf
            decides = swing >= a.trials / 2 or gap >= 0.15
            # A ROOM THAT WIPES YOU EVERY TRIAL IS NOT EASY. The rule
            # fell through to "won without healing at all" whenever the
            # blackout swing was zero, so Cerulean — which blacked the
            # party out in ALL FOUR trials with medicine and all four
            # without — was reported as too easy when it was beating
            # them outright (2026-09-15).
            _by = (f"{swing} fewer blackout(s)" if swing > 0
                   else f"{gap:.0%} more of the room")
            # A FACULTY CAN COST A ROOM, and the first version could not say
            # so: at Brock the status arm took 3 fights of 8 to the stripped
            # arm's 7, and it read "TOO EASY — it is won without a status
            # move at all", which is true and hides the whole finding
            # (2026-09-21). A turn that does no damage is a turn, and a
            # L12 BULBASAUR against a L14 ONIX does not have two to give.
            if gap <= -0.15 or swing <= -a.trials / 2:
                verdict = (f"HARMFUL — the {_noun} COSTS it "
                           f"{-gap:.0%} of the room"
                           + (f" and {-swing} more blackout(s)"
                              if swing < 0 else ""))
            elif w[2] >= a.trials and not decides:
                verdict = (f"TOO HARD — it wipes every trial, with {_noun} "
                           f"and without")
            elif wf >= 0.85 and decides:
                verdict = f"CALIBRATED — the {_noun} is what wins it ({_by})"
            elif nf >= 0.85 and not decides:
                verdict = f"TOO EASY — it is won without {_doing} at all"
            elif decides:
                verdict = (f"HARD — the {_noun} decides it ({_by}) but only "
                           f"wins {wf:.0%}")
            elif wf < 0.5:
                verdict = f"TOO HARD — the {_noun} does not save it"
            elif swing <= 0 and gap <= 0:
                verdict = f"TOO EASY — the {_noun} costs it nothing"
            else:
                verdict = (f"THIN — the {_noun} is worth {swing} blackout(s) "
                           f"and {gap:+.0%} of the room over {a.trials} "
                           f"trial(s)")
            unit = "trials won" if w[1] == a.trials else "fights"
            print(f"{room:16s} {w[0]:>3d}/{w[1]:<3d} b{w[2]:<2d} "
                  f"{n[0]:>4d}/{n[1]:<3d} b{n[2]:<2d} "
                  f"{unit:<10s}  {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

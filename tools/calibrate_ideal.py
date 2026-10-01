#!/usr/bin/env python3
"""Set each ideal room at the level where medicine decides it.

The ideal path's purpose (user, 2026-10-01): "part of what ideal is supposed
to test is that proper item usage can carry an underleveled but well built
team to victory". A room every policy sweeps without medicine tests nothing
of that, and a room nobody wins with it tests nothing either. This shifts a
room's party up and down in level (same species, moves and bag) and scores,
at each step, a REFERENCE: the plain baseline tactics with a generic set of
item rules, against the same tactics with none (policy_author's eval prints
the baseline beside every spec, and the baseline is exactly the stripped
twin). The room belongs where the medicine arm wins and the bare one does not.
The reference is no candidate policy, so the rooms are not tuned to one.

  tools/calibrate_ideal.py                       # every ideal room, its grid
  tools/calibrate_ideal.py --rooms pewter --grid 0,2,4,6 --trials 2
  tools/calibrate_ideal.py --report               # the table from what ran
Writes plans/cal/ and run/cal/ only; results to run/cal/results.jsonl.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
CAL_PLANS, CAL_RUN = ROOT / "plans/cal", ROOT / "run/cal"
RESULTS = CAL_RUN / "results.jsonl"


def ref_spec() -> dict:
    import battle_policy as B
    s = copy.deepcopy(B.DEFAULT_SPEC)
    s.update({
        "name": "ref_medicine",
        "battle_items": [
            {"item": "heal", "hp_below": 0.4, "max_uses": 3},
            {"item": "revive", "target": "fainted", "max_uses": 2},
            {"item": "cure", "hp_below": 1.0, "max_uses": 2}],
        "field_heal": {"item": "heal", "hp_below": 0.6},
        "field_revive": {"item": "revive"},
        "field_cure": [{"status": st, "item": "cure"}
                       for st in ("PSN", "PAR", "BRN", "SLP", "FRZ")],
    })
    assert not B.validate_spec(s), B.validate_spec(s)
    return s


def rooms() -> dict:
    """name -> (kind, base save, ideal spec)."""
    import gin_gym_arenas as G
    out = {}
    for g in G.GYMS:
        if g["paths"].get("ideal") is not None:
            out[g["name"]] = ("gym", g.get("base") or G.pick_base(g["badges"]),
                              G.build(g, "ideal"))
    out["e4"] = ("e4", ROOT / "run/arena_e4.lua",
                 json.loads((ROOT / "plans/arena_e4_ideal.json").read_text()))
    return out


def shifted(spec: dict, d: int) -> dict:
    s = copy.deepcopy(spec)
    for m in s["party"]:
        m["level"] = max(2, int(m["level"]) + d)
    return s


def build(name: str, d: int, base: Path, spec: dict) -> tuple:
    CAL_PLANS.mkdir(parents=True, exist_ok=True)
    CAL_RUN.mkdir(parents=True, exist_ok=True)
    sp = CAL_PLANS / f"arena_cal_{name}_{d:+d}.json"
    out = CAL_RUN / f"arena_cal_{name}_{d:+d}.lua"
    sp.write_text(json.dumps(shifted(spec, d), indent=1))
    r = subprocess.run([sys.executable, str(ROOT / "planner/gin_save.py"), "--base", str(base),
                        "--spec", str(sp), "--out", str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:] or r.stdout[-300:])
    return out, sp


_LINE = re.compile(r"(?:beat (\d+)/(\d+) of the room|Elite Four rooms cleared (\d+)/(\d+))")


def evaluate(cal: str, kind: str, lua: Path, sp: Path, trials: int) -> dict:
    """Run policy_author's eval-only on one calibration room; returns the
    fraction won by the reference and by the bare baseline."""
    refp = CAL_RUN / "ref_medicine.json"
    refp.write_text(json.dumps(ref_spec(), indent=1))
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "import policy_author as PA\n"
        "from pathlib import Path\n"
        "PA.ARENAS[%r] = (%r, Path(%r), Path(%r))\n"
        "sys.argv = ['policy_author.py', '--arenas', %r, '--trials', %r, "
        "'--run-id', %r, '--eval-only', %r]\n"
        "PA.main()\n") % (str(ROOT / "planner"), cal, kind, str(lua), str(sp), cal,
                          str(trials), "cal_" + cal, str(refp))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(ROOT), timeout=3600)
    got = {}
    for line in r.stdout.splitlines():
        who = ("ref" if line.startswith("ref_medicine") else
               "bare" if line.startswith("baseline") else None)
        m = _LINE.search(line)
        if who and m and who not in got:
            a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
            got[who] = int(a) / max(1, int(b))
    if "ref" not in got:
        got["error"] = (r.stderr or r.stdout)[-300:]
    return got


def report() -> str:
    rows = [json.loads(l) for l in RESULTS.read_text().splitlines() if l.strip()]
    by = {}
    for r in rows:
        by.setdefault(r["room"], []).append(r)
    out = []
    for room, rs in by.items():
        out.append(room)
        best = None
        for r in sorted(rs, key=lambda x: x["d"]):
            gap = (r.get("ref") or 0) - (r.get("bare") or 0)
            mark = ""
            if r.get("ref") is not None and r["ref"] >= 0.6 and (best is None or gap > best[1]):
                best = (r["d"], gap)
            out.append(f"  {r['d']:+d} levels: medicine {r.get('ref', 0):.0%}, "
                       f"bare {r.get('bare', 0):.0%}, gap {gap:+.0%}"
                       + (f"  [{r['error'][:80]}]" if r.get("error") else ""))
        out.append(f"  -> {'%+d levels' % best[0] if best else 'no setting where medicine wins'}"
                   + (f" (gap {best[1]:+.0%})" if best else ""))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rooms", default="")
    ap.add_argument("--grid", default="-4,-2,0,2")
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    if a.report:
        print(report())
        return
    all_rooms = rooms()
    want = [r for r in (a.rooms.split(",") if a.rooms else all_rooms) if r]
    grid = [int(x) for x in a.grid.split(",")]
    for name in want:
        kind, base, spec = all_rooms[name]
        for d in (grid if name != "pewter" or a.rooms else [0, 2, 4, 6]):
            lua, sp = build(name, d, base, spec)
            got = evaluate(f"cal_{name}_{d:+d}", kind, lua, sp, a.trials)
            row = {"room": name, "d": d, **got}
            with RESULTS.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(json.dumps(row), flush=True)
    print(report())


if __name__ == "__main__":
    main()

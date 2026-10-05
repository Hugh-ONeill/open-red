#!/usr/bin/env python3
"""A failed walk a person voided (run/walk_failures_void) does not refuse
the next plan, and a push carries what waits on what waits on it.

Run 36, 2026-10-05: HM04's plans failed walking to FUCHSIA_CITY because
`go` pressed use_warp on Seafoam B3F's current mouth; once that was fixed
the same-walk rule still refused every draft that walked there (user:
"clear only this record"). The authoring failure then pushed HM04 later
with "Clear Victory Road" riding, and left "Defeat the Elite Four", which
waits on Victory Road, in front of both.

Pinned: the failed walk counts until its plan_start is listed, then not,
in the places and in the history; another plan's failure is untouched;
a push carries riders of riders, a PULL row counts as waiting; and a
push that would leave nothing moved is refused. Synthetic."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


G = "Obtain HM04 STRENGTH from the Warden in the Safari Zone"
with tempfile.TemporaryDirectory() as d:
    run = Path(d)
    rows = [{"t": 100.0, "kind": "plan_start", "goal": G},
            {"t": 101.0, "kind": "escalate_context", "subgoal": "go_f",
             "target": "map:FUCHSIA_CITY"},
            {"t": 102.0, "kind": "escalate_end", "subgoal": "go_f", "success": False},
            {"t": 200.0, "kind": "plan_start", "goal": "Clear Victory Road"}]
    (run / "executor_log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    p0 = A._failed_walk_places(G, run)
    h0 = A._failed_walk_history(G, run)
    ck("a failed walk counts", p0 == [("go_f", "FUCHSIA_CITY")] and h0[0] == 1, (p0, h0))
    (run / "walk_failures_void").write_text("200.0\tanother plan\n")
    ck("another plan's void leaves it standing",
       A._failed_walk_places(G, run) == p0)
    (run / "walk_failures_void").write_text(
        "100.0\tfailed on the B3F replay bug fixed in 96ac691\n")
    ck("listed, it is not the same walk", A._failed_walk_places(G, run) == [])
    ck("...nor in the history", A._failed_walk_history(G, run) == (0, set()))


def push(outline, frm, after, inserts):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        (d / "plans/outline.txt").write_text("\n".join(outline) + "\n")
        (d / "plans/outline.authored").write_text(outline[-1] + "\n")
        (d / "run/outline_inserts").write_text("\n".join(inserts) + "\n")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "planner"))
        r = subprocess.run([sys.executable, str(ROOT / "planner/push_leg.py"),
                            str(frm), str(after)], cwd=d, env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr, \
            (d / "plans/outline.txt").read_text().splitlines()


O = ["Obtain HM04", "Clear Victory Road", "Defeat the Elite Four",
     "Reach Celadon City", "Defeat the rival in the final showdown"]
INS = ["LEG=Clear Victory Road|Obtain HM04",
       "LEG=Defeat the Elite Four|Clear Victory Road"]
rc, out, lines = push(O, 1, 4, INS)
ck("what waits on a rider rides too",
   rc == 0 and lines[:4] == ["Reach Celadon City", "Obtain HM04",
                             "Clear Victory Road", "Defeat the Elite Four"],
   (rc, out, lines))
rc, out, lines = push(O, 1, 4, ["LEG=Clear Victory Road|PULL Obtain HM04",
                                "LEG=Defeat the Elite Four|Clear Victory Road"])
ck("a leg pulled ahead for another counts as waited on",
   rc == 0 and lines.index("Obtain HM04") < lines.index("Clear Victory Road")
   < lines.index("Defeat the Elite Four"), (rc, out, lines))
rc, out, lines = push(O[:3] + O[4:], 1, 3, INS)
ck("all of it riding to where it stands is no move, and refused",
   rc == 5 and lines == O[:3] + O[4:], (rc, out, lines))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

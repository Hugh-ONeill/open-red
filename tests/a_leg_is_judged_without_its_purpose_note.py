#!/usr/bin/env python3
"""A leg is judged done as itself, not as the leg its purpose note names;
and a party leg whose plan met its conditions unconfirmed plays on.

Run of record 11 (2026-09-27): "the party holds a FIGHTING or GRASS type
(a doubt you recorded when outlining: for: Defeat Brock for the Boulder
Badge)" with Bulbasaur in the party was refused by check-done as "names
BOULDERBADGE and the run is not wearing it": the note rode into every
mechanical check. The leg was re-planned, ran a second time, and was
pushed. "every party member is at least level 20 (...for: Reach Vermilion
City)" with all four at 20 was refused as "names VERMILION_CITY" and
pushed the same way.

Pinned: check-done and the already-done check read the objective without
its note, so a met leg reaches the judge; an objective that itself names
an unearned badge is still refused; and the chain's met-but-unconfirmed
redo is not a second attempt for a party leg. Synthetic: the model is
stubbed.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp(prefix="doubtnote_"))
(tmp / "run").mkdir()
(tmp / "plans").mkdir()
os.chdir(tmp)

asked = []


def fake_chat(msgs, model):
    asked.append(msgs[-1]["content"])
    return json.dumps({"done": True, "why": "BULBASAUR is a GRASS type"})


A.brock_probe.chat = fake_chat
import upkeep_ask  # noqa: E402
upkeep_ask.maybe_skip = lambda *a, **k: ""

NOTE = " (a doubt you recorded when outlining: for: Defeat Brock for the Boulder Badge)"
LEG = "the party holds a FIGHTING or GRASS type"
START = ("standing in ROUTE_2 with PIKACHU L12 (ELECTRIC), BULBASAUR L14 "
         "(GRASS/POISON), PIDGEY L12 (NORMAL/FLYING)")

out = io.StringIO()
with redirect_stdout(out), redirect_stderr(io.StringIO()):
    done = A.check_done(LEG + NOTE, START, "m")
ck("a met party leg is not refused over the badge its purpose note names",
   done and "BOULDERBADGE" not in out.getvalue(), out.getvalue()[-300:])
ck("...the judge is asked about the objective itself",
   asked and asked[-1].startswith("THE OBJECTIVE: " + LEG)
   and "a doubt you recorded" not in asked[-1].split("\n")[0], asked[-1:][:1])

out = io.StringIO()
with redirect_stdout(out), redirect_stderr(io.StringIO()):
    done = A.check_done("Defeat Brock for the Boulder Badge", START, "m")
ck("an objective that itself names an unearned badge is still refused",
   not done and "BOULDERBADGE" in out.getvalue(), out.getvalue()[-300:])

err = io.StringIO()
with redirect_stdout(io.StringIO()), redirect_stderr(err):
    A.check_already_done(LEG + NOTE, START, "m")
ck("the already-done check reads it without the note too",
   "BOULDERBADGE" not in err.getvalue(), err.getvalue()[-300:])

sh = (ROOT / "fresh_discovery.sh").read_text()
_play = sh.find('if [ "$confirmed" = 0 ] && [ "${_party:-0}" = 1 ]; then')
_redo = sh.find('if [ "$redone" = 0 ] && [ "$confirmed" = 0 ]; then')
ck("a party leg met but unconfirmed plays on before the redo can re-plan it",
   0 < _play < _redo)
_blk = sh[_play:_redo]
ck("...and is counted and noted, like a party leg that failed its attempt",
   'echo "$i" > "$PROGRESS"' in _blk and "outline_upkeep_missed" in _blk
   and "continue" in _blk)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A move offered, and the moves it would replace, show their PP.

The TM question and the level-up question showed type and power, so
SOLARBEAM at 120 read as a plain upgrade on RAZOR_LEAF at 55; the summary
screen also says 10 uses against 25 (user, 2026-09-16: "its the same trap
with char and fireblast replacing flamethrower when pp utility is crucial
for the e4"). Pinned: the shim publishes max PP for party moves (PP UPs
counted as the engine counts them), for a move being learned and the moves
known then, and for a machine's move; both questions show "PP now/max" for
a known move and "PP max" for an offered one. The charge turn is not on the
summary screen and is not said.

Synthetic: source anchors and the PP words; no game, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


ck("a known move reads PP left of max",
   E._pp_words({"id": "RAZOR_LEAF", "pp": 12, "max_pp": 25}) == "PP 12/25")
ck("an offered move reads its max",
   E._pp_words({"id": "SOLARBEAM", "max_pp": 10}) == "PP 10")
ck("no max, no PP words", E._pp_words({"id": "X", "pp": 5}) == "")

SH = (ROOT / "harness/shim.lua").read_text()
ck("party moves carry max PP with PP UPs counted",
   "m.moves[j].max_pp = mdef.pp + _ups * math.floor(mdef.pp / 5)" in SH)
ck("a move being learned carries max PP, and the known ones their PP too",
   "max_pp = md and md.pp or nil }" in SH and "known[i].pp = m.pp" in SH)
ck("a machine's move carries max PP", "max_pp = mdef and mdef.pp }" in SH)
PK = (Path.home() / "Developer/gen1recomp/src/pokemon/Pokemon.lua").read_text()
ck("...counted as the engine counts PP UPs",
   "mdef.pp + (mv.ppUps or 0) * math.floor(mdef.pp / 5)" in PK)

SRC = (ROOT / "planner/executor.py").read_text()
ck("both questions add the PP words to each move",
   SRC.count("bits.append(_pp_words(x))") == 2)
ck("the machine's line carries its PP",
   'f", PP {_mpp}" if _mpp else ""' in SRC)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

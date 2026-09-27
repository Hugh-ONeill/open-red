#!/usr/bin/env python3
"""A level leg runs like any leg; a party leg that cannot be written is
played past, not pushed; and the missing rung will not insert on a rule
of the game it cannot point at.

Run of record 9 (2026-09-26/27): the one-short-attempt rule for party legs
also cut the level legs, and the run reached Celadon at 29-33 with an Abra
at 11 (user: "i thought level legs got full attempts because theyre always
achievable just possibly slow"). Three party legs went through the
authoring-failed path and were pushed down the list. And the missing rung
inserted "Defeat the Team Rocket Leader in Mt. Moon" and "Obtain the MOON
STONE in Mt. Moon" on "the game requires ... to trigger ..." (user: "do all
three").

Pinned: a leg on the party list is a party leg unless it is a level; the
one-attempt rule reads that; an unwritable party leg plays on before any
push; the purpose ask never skips a level; a reason that asserts a rule of
the game is turned down while one that says where a thing comes from is
not. Synthetic."""
from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


sh = (ROOT / "fresh_discovery.sh").read_text()
ck("a leg on the party list is a party leg unless it is a level",
   '*"at least level "*) ;;\n      *) _is_party=1 ;;' in sh
   and sh.index("_is_party=0") < sh.index('goal="$leg"'))
ck("...and the one-attempt rule reads that", "_party=$_is_party" in sh)
ck("an unwritable party leg plays on before any push",
   'if [ "$_arc" != 0 ] && [ "$_is_party" = 1 ]; then' in sh
   and sh.index('if [ "$_arc" != 0 ] && [ "$_is_party" = 1 ]; then')
   < sh.index("authoring failed for leg $i ($goal) — pushing it later"))

import upkeep_ask as U  # noqa: E402
d = Path(tempfile.mkdtemp(prefix="lvl_"))
(d / "plans").mkdir(); (d / "run").mkdir()
LV = "every party member is at least level 35"
(d / "plans/outline.upkeep").write_text(LV + "\n")
(d / "plans/outline.notes").write_text(LV + "\tfor: Reach Saffron\n")
(d / "plans/outline.authored").write_text("Reach Saffron\n" + LV + "\n")
(d / "plans/outline.txt").write_text("Reach Saffron\n" + LV + "\n")
(d / "run/outline_leg").write_text("1")
os.chdir(d)
U.brock_probe = None
ck("the purpose ask never skips a level", U.maybe_skip(LV, "s", "m") == ""
   and not (d / "run/upkeep_purpose_asked").exists())

replies = []


def chat(msgs, model, **kw):
    if msgs[0]["content"] != A.CHECKMISSING_SYS:
        return '{"why": "not yet", "done": false}'
    return replies.pop(0)


A.brock_probe.chat = chat
replies[:] = ['{"why": "the game requires the defeat of the Team Rocket leader to trigger the exit", '
              '"insert": "Defeat the Team Rocket Leader in Mt. Moon"}',
              '{"why": "the S.S. Ticket is obtained from Bill in his house on Route 25", '
              '"insert": "Help Bill in his house on Route 25"}']
err = io.StringIO()
with redirect_stderr(err):
    out = A.check_missing("Exit Mt. Moon", [(9, "Exit Mt. Moon")], "s", "m",
                          behind=[(8, "Reach Mt. Moon")], tries=2)
ck("a reason that asserts a rule of the game is turned down",
   "asserts a rule of the game" in err.getvalue(), err.getvalue()[-300:])
ck("...and one that says where a thing comes from is taken",
   out == "Help Bill in his house on Route 25", out)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

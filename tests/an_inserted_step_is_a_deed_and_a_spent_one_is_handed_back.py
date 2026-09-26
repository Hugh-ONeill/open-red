#!/usr/bin/env python3
"""A missing step is asked for as a deed, not a visit, and an insert that was
finished without unblocking its leg is handed back once.

Run of record 5, 2026-09-26: stuck on "Retrieve the S.S. Ticket", the
missing rung inserted "Visit Bill's house on Route 25". Its plan ended on
the house's map, check-done said "done: The run is currently standing in
BILLS_HOUSE", Bill's errand never happened, and the ticket leg failed again
with its one insert spent — sealed in Cerulean, whose only way south is
the trashed house the errand opens (user: "stop it, do b and c, and restart
clean").

Pinned: the question says a gate is a deed and a visit is met on arrival;
a proposal that only visits, enters or goes to a place is turned down with
that reason while "Reach <town>" and "Go through <place>" are not; an
earlier insert for this objective that the run has finished is shown as
not the gate; the chain lets such a leg be asked once more (two at most).
Synthetic."""
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


ck("the question says a gate is a deed and a visit is met on arrival",
   "A GATE IS A DEED, NOT A PLACE." in A.CHECKMISSING_SYS
   and "met the moment you stand there" in A.CHECKMISSING_SYS)

d = Path(tempfile.mkdtemp(prefix="miss_"))
(d / "run").mkdir()
TICKET = "Retrieve the S.S. Ticket"
BILL = "Visit Bill's house on Route 25"
(d / "run/outline_inserts").write_text(f"LEG={TICKET}|{BILL}\nLEG=Other leg|Something\n")
os.chdir(d)
behind = [(15, "Defeat Misty for the Cascade Badge"), (16, BILL)]
ck("an insert for this objective the run has finished is found",
   A.inserts_that_did_not_unblock(TICKET + " (a doubt you recorded when outlining: x)", behind) == [BILL])
ck("...and one not yet finished is not",
   A.inserts_that_did_not_unblock(TICKET, [(15, "Defeat Misty for the Cascade Badge")]) == [])

replies = []
seen = []


def chat(msgs, model, **kw):
    if msgs[0]["content"] != A.CHECKMISSING_SYS:     # the already-done check
        return '{"why": "not yet", "done": false}'
    seen.append(msgs[-1]["content"])
    return replies.pop(0)


A.brock_probe.chat = chat
ahead = [(17, TICKET), (18, "Reach Vermilion City")]
replies[:] = ['{"why": "Bill is there", "insert": "Visit Bill\'s house on Route 25"}',
              '{"why": "his errand gives the ticket", "insert": "Help Bill in his house on Route 25"}']
err = io.StringIO()
with redirect_stderr(err):
    out = A.check_missing(TICKET, ahead, "standing in CERULEAN_CITY", "m",
                          behind=behind, tries=3)
ck("a proposal that only visits is turned down, and says why",
   "turned down \"Visit Bill's house on Route 25\": it is met by arriving" in err.getvalue(),
   err.getvalue()[-400:])
ck("...and the deed asked for next is taken", out == "Help Bill in his house on Route 25", out)
ck("the question showed the earlier insert as not the gate",
   seen and "YOU INSERTED THESE FOR THIS OBJECTIVE BEFORE, AND FINISHED THEM, AND IT STILL FAILS"
   in seen[0] and BILL in seen[0], seen[0][-500:] if seen else "")
for good in ("Reach Cinnabar Island", "Go through the Seafoam Islands"):
    replies[:] = ['{"why": "x", "insert": "%s"}' % good]
    err = io.StringIO()
    with redirect_stderr(err):
        A.check_missing(TICKET, ahead, "s", "m", behind=behind, tries=1)
    ck(f"'{good}' is not turned down as a visit", "met by arriving" not in err.getvalue(),
       err.getvalue()[-300:])

sh = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain hands a finished insert back once, two at most",
   "_ins_allow=1" in sh and '_ins_allow=2' in sh
   and '[ "$_ip" -lt "$i" ]' in sh
   and '[ "${_ins_leg:-0}" -lt "$_ins_allow" ] || return 1' in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

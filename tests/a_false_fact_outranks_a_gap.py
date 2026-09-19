#!/usr/bin/env python3
"""When drawn outlines are laid side by side for a hand pick, a false fact
counts against a draft before a missing gate does.

Run 27 reached the Hall of Fame on a draw the judge would have passed over:
the parcel, SURF, the Secret Key and Victory Road never named, CUT after
Surge. Those were GAPS, and the chain closed them by writing the missing
leg when it got there (five inserts). A FALSE FACT sends the run somewhere
wrong for rounds, and the chain cannot be told "no" when the model builds
it out of true elements (user, 2026-09-19): the Coin Case is a real item
and the Game Corner a real place, and "Obtain the Coin Case from the Game
Corner" cost four attempts before it was voided.

Pinned: a real thing fetched from the wrong place, a badge the game never
prints and a garbled errand are each a false fact; the right source is not;
the thing is read before the preposition and the place after it, so CUT
got from the captain is not filed against the ticket; accents are folded;
a leg is counted once; a gate the judge marks as a wrong source is the same
fact, counted once; a draft with gaps outranks a draft with a false fact;
the table is printed in that order; the trends tool reads the same tables;
and none of it can reach a prompt. Synthetic."""
from __future__ import annotations

import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import compare_outlines as C  # noqa: E402
import outline_facts as F  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def kinds(*legs):
    return [(k, l) for k, l, _ in F.false_facts(list(legs))]


# ------------------------------------------------------------ what counts
ck("a real thing fetched from the wrong place is a false fact",
   kinds("Retrieve the Secret Key from the Game Corner")
   == [("source", "Retrieve the Secret Key from the Game Corner")])
ck("...run 27's own, built out of true elements",
   kinds("Obtain the Coin Case from the Game Corner")
   == [("source", "Obtain the Coin Case from the Game Corner")])
ck("the right source is not",
   kinds("Retrieve the Secret Key from the Pokemon Mansion",
         "Obtain the Coin Case from the man in the Celadon diner",
         "Retrieve the HM01 from the S.S. Anne",
         "Retrieve the Silph Scope from the Rocket Hideout",
         "Return the Gold Teeth to the Warden in the Safari Zone to obtain HM04")
   == [])
ck("a badge the game never prints is one",
   kinds("Defeat Erika for the Grass Badge")
   == [("badge", "Defeat Erika for the Grass Badge")])
ck("...and a real badge is not", kinds("Defeat Erika for the Rainbow Badge") == [])
ck("a garbled errand is one, accents folded",
   kinds("Retrieve the Poké Ball from the Pallet Town resident")
   == [("garbled", "Retrieve the Poké Ball from the Pallet Town resident")])
ck("the thing is read before the preposition and the place after it",
   kinds("Obtain the CUT HM from the S.S. Ticket/Captain") == [],
   kinds("Obtain the CUT HM from the S.S. Ticket/Captain"))
ck("...so a thing USED somewhere is not filed as got there",
   kinds("Use the Coin Case at the Game Corner") == [])
ck("a leg is counted once however many ways it is wrong",
   len(kinds("Retrieve the Ethereal Secret Key from the Game Corner")) == 1)
ck("an ordinary leg says nothing false",
   kinds("Reach Cerulean City", "every party member is at least level 20",
         "Defeat Misty for the Cascade Badge", "Traverse Mt. Moon") == [])

# ------------------------------------------------------------ the judge
GOOD_BUT_GAPPY = [
    "Choose a starter Pokemon", "Reach Pewter City",
    "Defeat Brock for the Boulder Badge",
    "Defeat Misty for the Cascade Badge",
    "Defeat Lt. Surge for the Thunder Badge",
    "Defeat Erika for the Rainbow Badge",
    "Defeat Koga for the Soul Badge", "Defeat Sabrina for the Marsh Badge",
    "Defeat Blaine for the Volcano Badge",
    "Defeat Giovanni for the Earth Badge", "Defeat the Elite Four"]
FULL_BUT_FALSE = GOOD_BUT_GAPPY[:8] + [
    "Reach Cinnabar Island",
    "Retrieve the Secret Key from the Game Corner",
    "Defeat Blaine for the Volcano Badge",
    "Defeat Giovanni for the Earth Badge", "Navigate Victory Road",
    "Defeat the Elite Four"]
jg, jf = C.judge(GOOD_BUT_GAPPY), C.judge(FULL_BUT_FALSE)
ck("the judge counts the false fact", len(jf["false"]) == 1 and not jg["false"],
   (jf["false"], jg["false"]))
ck("...once, though the gate is marked a wrong source too",
   jf["gates"]["secret key"] == "?" and len(jf["false"]) == 1)
ck("...and says it first among the flags",
   jf["flags"] and jf["flags"][0].startswith("FALSE FACT (source)"), jf["flags"][:2])
ck("a draft with gaps outranks a draft with a false fact",
   C.rank(jg) < C.rank(jf)
   and sum(1 for v in jg["gates"].values() if v == "✗")
   > sum(1 for v in jf["gates"].values() if v == "✗"), (C.rank(jg), C.rank(jf)))
MISPLACED = GOOD_BUT_GAPPY[:5] + ["Retrieve the HM01 from the S.S. Anne"] \
    + GOOD_BUT_GAPPY[5:]
ck("between two with no false fact, a misplaced gate counts before a gap",
   C.rank(jg)[0] == C.rank(C.judge(MISPLACED))[0] == 0
   and C.rank(jg) < C.rank(C.judge(MISPLACED)))

tmp = Path(tempfile.mkdtemp(prefix="outlines_"))
(tmp / "a_false.txt").write_text("\n".join(FULL_BUT_FALSE))
(tmp / "b_gappy.txt").write_text("\n".join(GOOD_BUT_GAPPY))
buf = io.StringIO()
with redirect_stdout(buf):
    C.main([str(tmp / "a_false.txt"), str(tmp / "b_gappy.txt")])
out = buf.getvalue()
table = [l for l in out.splitlines() if l.startswith(("a_false", "b_gappy"))]
ck("the table is printed the better pick first, with the count in it",
   table and table[0].startswith("b_gappy") and "false" in out.splitlines()[0],
   table)

# ----------------------------------------------------- one set of tables
import outline_trends as T  # noqa: E402
ck("the trends tool reads the same tables",
   T.SOURCES is F.SOURCES and T.NONSENSE is F.NONSENSE
   and T.WRONG_BADGE is F.WRONG_BADGE)
for f in ("author.py", "executor.py", "ledger.py", "state_text.py",
          "policy_author.py"):
    ck(f"nothing in {f} can put these tables in a prompt",
       "outline_facts" not in (ROOT / "planner" / f).read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

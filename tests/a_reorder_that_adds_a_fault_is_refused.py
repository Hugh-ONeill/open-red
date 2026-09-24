#!/usr/bin/env python3
"""A push, a pull or an insert that would give the outline a fault it does
not have is refused, in the judge's own words.

2026-09-23, run of record on run 34's outline. The later rung pushed
"Reach Vermilion City" from 11 to 20, behind Celadon and Erika, on the
reason "CUT is obtained from the gym leader in Celadon City"; the blocker
rung then pulled the HM01 leg to 12, in front of the city it is in. The
judge that screens the draw (compare_outlines, 1daf96b) names both faults
at once — a town reached before the town that opens it, a gate item before
its town — and nothing ran it on a rung. Six rounds of drink-hunting later
the run was stopped.

Now the three tools ask the judge before they write (planner/outline_gate):
a change that ADDS a fault is refused with exit 3 and the file untouched,
and the chain falls through to its next rung; a fault the list already
carries is not held against a move; an undo is never judged. Nothing
reaches a prompt.

Pinned: the Vermilion push is refused and the file is unchanged; a push
that adds no fault goes through; the HM01 pull is refused; a pull that
adds none goes through; an undo is never refused; an insert stating what
the game does not bear out is refused, a plain one is not; the chain's
pull is guarded by its exit code and falls through. Synthetic."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import outline_gate as G  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


OUTLINE = ["Choose a starter Pokemon",
           "Defeat Brock for the Boulder Badge",
           "Defeat Misty for the Cascade Badge",
           "Retrieve the S.S. Ticket from Bill",
           "Reach Vermilion City",
           "Retrieve the HM01 from the S.S. Anne",
           "Defeat Lt. Surge for the Thunder Badge",
           "every party member is at least level 30",
           "Navigate through the Rock Tunnel",
           "Reach Lavender Town",
           "Reach Celadon City",
           "Defeat Erika for the Rainbow Badge",
           "Reach Fuchsia City"]


def tool(args, outline=OUTLINE, files=None, done=0):
    d = Path(tempfile.mkdtemp())
    (d / "plans").mkdir(); (d / "run").mkdir()
    (d / "plans/outline.txt").write_text("\n".join(outline) + "\n")
    (d / "run/outline_leg").write_text(str(done))
    for k, v in (files or {}).items():
        (d / k).write_text(v)
    r = subprocess.run([sys.executable, str(ROOT / "planner" / args[0])]
                       + [str(a) for a in args[1:]],
                       cwd=d, capture_output=True, text=True)
    lines = [l for l in (d / "plans/outline.txt").read_text().splitlines()
             if l.strip()]
    return r.returncode, r.stdout + r.stderr, lines, d


# ---- the judge's word ----------------------------------------------------
ck("the list as drawn has no fault of these kinds", G.faults(OUTLINE) == set())
after = list(OUTLINE); after.remove("Reach Vermilion City")
after.insert(after.index("Defeat Erika for the Rainbow Badge") + 1, "Reach Vermilion City")
bad = G.added_faults(OUTLINE, after)
ck("Vermilion behind Celadon is a fault it did not have",
   bad and all("reach order" in b for b in bad), bad)

# ---- push -----------------------------------------------------------------
rc, out, lines, _ = tool(["push_leg.py", 5, 12])      # Vermilion after Erika
ck("the Vermilion push is refused", rc == 3 and "push refused" in out, out[:200])
ck("...and the file is untouched", lines == OUTLINE)
ck("...in the judge's own words",
   "Celadon is reached before Vermilion" in out, out[:300])
rc, out, lines, _ = tool(["push_leg.py", 8, 10])      # the level leg later
ck("a push that adds no fault goes through",
   rc == 0 and "pushed" in out and lines != OUTLINE, out[:200])

# ---- pull -----------------------------------------------------------------
rc, out, lines, _ = tool(["pull_leg.py", "pull", 9, 11])   # Celadon ahead of Lavender
ck("Celadon pulled ahead of Lavender is refused",
   rc == 3 and "pull refused" in out and "Celadon is reached before Lavender" in out,
   out[:300])
ck("...and the file is untouched", lines == OUTLINE)
rc, out, lines, _ = tool(["pull_leg.py", "pull", 4, 6])   # HM01 ahead of Vermilion
ck("HM01 pulled ahead of Vermilion is allowed: the judge holds Misty, not "
   "Vermilion, as the gate before Cut, and the leg can walk there itself",
   rc == 0 and "pulled forward" in out, out[:200])
GATED = list(OUTLINE); GATED.remove("Retrieve the HM01 from the S.S. Anne")
GATED.insert(GATED.index("Defeat Brock for the Boulder Badge") + 1, "Retrieve the HM01 from the S.S. Anne")
ck("...but ahead of Misty it is a gate item before its town",
   any("comes BEFORE" in f for f in G.added_faults(OUTLINE, GATED)),
   G.added_faults(OUTLINE, GATED))
rc, out, lines, _ = tool(["pull_leg.py", "pull", 4, 8])   # the level leg forward
ck("a pull that adds no fault goes through",
   rc == 0 and "pulled forward" in out and lines[3] == OUTLINE[7], out[:200])
# an undo puts a leg back and is never judged, even into a faulty order
FAULTY = list(OUTLINE); FAULTY.remove("Reach Vermilion City"); FAULTY.insert(3, "Reach Vermilion City")
rc, out, lines, _ = tool(["pull_leg.py", "undo", 4], outline=FAULTY,
                         files={"run/outline_pulls": "4\t12\tReach Vermilion City\n"})
ck("an undo is never refused", rc == 0 and "put back at" in out, out[:200])

# ---- insert ---------------------------------------------------------------
rc, out, _, _ = tool(["insert_guard.py", "Retrieve the Secret Key from the Game Corner",
                      "Reach Fuchsia City", "plans/outline.txt"])
ck("an insert that states what the game does not bear out is refused",
   rc == 3 and "insertion refused" in out and "FALSE FACT" in out, out[:300])
rc, out, _, _ = tool(["insert_guard.py", "the party has at least 4 Pokemon",
                      "Reach Vermilion City", "plans/outline.txt"])
ck("a plain insert goes through", rc == 0, out[:200])
rc, out, _, _ = tool(["insert_guard.py", "Reach Celadon City first",
                      "Reach Lavender Town", "plans/outline.txt"])
ck("an insert that arrives before the town that opens it is refused",
   rc == 3 and "insertion refused" in out, out[:300])

SURF = ["Choose a starter Pokemon", "Defeat Koga for the Soul Badge",
        "a party Pokemon knows SURF", "Reach Cinnabar Island",
        "Defeat Blaine for the Volcano Badge"]
rc, out, lines, _ = tool(["push_leg.py", 3, 4], outline=SURF)   # Surf behind Cinnabar
ck("a gate item pushed behind the thing that needs it is refused too "
   "(Surf after Cinnabar: the run arrives and cannot go on; 2026-09-24)",
   rc == 3 and "comes AFTER" in out, out[:300])
ck("...and the file is untouched", lines == SURF)

ck("Flash from Bill is a false fact the table now knows (inserted in the run of record, 2026-09-24)",
   any("FALSE FACT" in f for f in G.faults(OUTLINE + ["Obtain HM05 (FLASH) from Bill in his house on Route 25"])))
ck("...while Flash from the aide on Route 2 is not",
   not any("FALSE FACT" in f for f in G.faults(OUTLINE + ["Obtain HM05 (FLASH) from Oak's aide on Route 2"])))

# ---- the chain ------------------------------------------------------------
SH = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain's pull is guarded by its exit code and falls through",
   'if python planner/pull_leg.py pull "$i" "$blocker"; then' in SH
   and "the pull was refused by the judge; on to the next rung" in SH)
ck("...and the pull-back record is written only for a pull that happened",
   SH.index('if python planner/pull_leg.py pull "$i" "$blocker"; then')
   < SH.index("printf '%s\\n' \"$_btext\" >> run/outline_pullbacks"))
ck("every push the chain makes is already an if", SH.count("python planner/push_leg.py") == SH.count("if python planner/push_leg.py")
   + SH.count("&& python planner/push_leg.py"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

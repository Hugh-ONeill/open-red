#!/usr/bin/env python3
"""What the model concluded when a rung asked about a leg reaches the next
plan written for that leg, as its own words, and no other leg.

The wording rung kept "Retrieve the Gold Teeth for the Warden" because "the
Gold Teeth are an item found in a house in Fuchsia City", and the plan written
next for the same leg searched Pokemon Tower 3F again (run 41, 2026-10-09): the
rungs' reasons went to the chain log and nowhere else. They are kept now in
run/rung_said under the leg's wording and read back by objective_history_text,
the block build_prompt gives the author.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

d = tempfile.mkdtemp()
os.environ["RED_RUNG_SAID"] = str(Path(d) / "rung_said")
import author as A                                        # noqa: E402

G = "Retrieve the Gold Teeth for the Warden"
A.note_rung_said(G, "missing", "The Gold Teeth are not found by exploring the "
                 "Pokemon Tower, but are given by a specific NPC in the Pokemon "
                 "Tower after the ghost of Marowak is defeated.")
A.note_rung_said(G, "wording", "The objective is phrased correctly; the Gold "
                 "Teeth are an item found in a house in Fuchsia City and are "
                 "required to be given to the Warden of the Safari Zone.")
A.note_rung_said("Defeat Koga for the Soul Badge", "later", "Koga is next.")
A.note_rung_said(G + " (a doubt you recorded when outlining: where?)", "later",
                 "The run already possesses HM_STRENGTH, the reward.")
A.note_rung_said(G, "wording", "The objective is phrased correctly; the Gold "
                 "Teeth are an item found in a house in Fuchsia City and are "
                 "required to be given to the Warden of the Safari Zone.")

t = A.rung_said_text(G)
ck("the leg's own answers come back", "found in a house in Fuchsia City" in t)
ck("...framed as the model's own, not the game's",
   "your own answers" in t and "not something this game has told you" in t)
ck("...each with the question it answered",
   "you said the wording stands" in t and "you said it stays" in t)
ck("...an answer under the leg's doubt-noted wording is the same leg",
   "HM_STRENGTH" in t)
ck("...the same answer twice is said once", t.count("found in a house") == 1)
ck("...no more than three", t.count("\n  ") <= 3)
ck("...newest last (a repeat counts where it was last said)",
   t.find("Marowak") < t.find("HM_STRENGTH") < t.find("Fuchsia City"))
ck("another leg's answers stay with that leg", "Koga is next" not in t)
ck("a leg never asked about has nothing", A.rung_said_text("Reach Pewter City") == "")
ck("the author's history block carries it",
   "found in a house in Fuchsia City" in A.objective_history_text(G))

src = (ROOT / "planner/author.py").read_text()
for rung in ("blocker", "missing", "wording", "later"):
    ck(f"the {rung} rung keeps its reason", f'note_rung_said(goal, "{rung}"' in src)
ck("a fresh start clears the record",
   "run/rung_said" in (ROOT / "fresh_discovery.sh").read_text())
ck("the suite writes a throwaway, never the live run",
   'RED_RUNG_SAID="$RED_BRIDGE_DIR/rung_said"' in (ROOT / "tests/run_suite.sh").read_text())

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

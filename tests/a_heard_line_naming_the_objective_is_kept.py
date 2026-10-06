#!/usr/bin/env python3
"""In WHAT PEOPLE HAVE SAID, a room's lines that share a word with the
objective are kept before the newest others.

Run 37, 2026-10-06: Fuchsia held sixteen lines and the section showed the
newest four (zoo signs and a stray battle line), so "SAFARI ZONE WARDEN's
HOME" never reached the HM04 drafts, whose idea step wrote "The Warden is
located inside the Safari Zone (from: memory) — heard: nothing heard".

Pinned: the objective's naming words skip the verbs and generic nouns; a
matching line is shown however old; the newest fill the rest to four; with
no objective the newest four, as before. Synthetic."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("the naming words skip verbs and generic nouns",
   A._objective_words("Obtain HM04 from the Warden in the Safari Zone")
   >= {"WARDEN"} and "OBTAIN" not in A._objective_words("Obtain the HM04"), )
lines = ["SIGN_FUCHSIA_CITY_27_29: SAFARI ZONE WARDEN's HOME"] + [
    f"SIGN_FUCHSIA_CITY_{i}_1: Name: MON{i} a zoo sign number {i}" for i in range(8)]
# a world shaped like a run's, holding only this room's lines
d = {"explored": {"FUCHSIA_CITY|2,2": {}}, "visits": {"FUCHSIA_CITY|2,2": 9},
     "hints": {"FUCHSIA_CITY|2,2": lines}, "hints_at": {}, "flag_sites": {},
     "sightings": {}, "touched": {}, "frontier": {}, "dead_ends": {}}
with tempfile.TemporaryDirectory() as t:
    p = Path(t) / "explored.json"
    p.write_text(json.dumps(d))
    A._AUTHORING_GOAL = "Obtain HM04 from the Warden"
    w = A.people_said_text(p)
    ck("a line naming the objective is shown however old", "WARDEN's HOME" in w, w)
    ck("...and the newest fill the rest to four",
       "MON7" in w and "MON6" in w and "MON5" in w and "MON4" not in w, w)
    A._AUTHORING_GOAL = None
    w = A.people_said_text(p)
    ck("with no objective, the newest four as before",
       "WARDEN" not in w and "MON4" in w and "MON7" in w, w)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

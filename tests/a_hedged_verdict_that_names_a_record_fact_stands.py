#!/usr/bin/env python3
"""A hedged done verdict stands when its reason names a fact the record
confirms; one that names nothing is still refused.

Run 27, 2026-09-17: "Clear the Pokemon Tower" was judged done twice with
"the player ... possesses the Silph Scope and Poke Flute, indicating they
have reached the end of the tower", with EVENT_BEAT_GHOST_MAROWAK and
EVENT_RESCUED_MR_FUJI fired and POKE_FLUTE in the bag. The hedge-word
guard refused both on "indicating", and the leg was pushed down the list
as unconfirmed (user: "i thought it completed it because it got the poke
flute").

Pinned: a fired event named verbatim, a badge worn or an item in the bag
named in the reason lets the verdict stand, with the fact said; the Bill
and Rock Tunnel reasons, which name none, are refused as before; both
done rungs ask. Synthetic.
"""
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
    checks.append((name, bool(ok := cond), detail))


tmp = Path(tempfile.mkdtemp()) / "obs.json"
tmp.write_text(json.dumps({
    "flags": ["EVENT_BEAT_GHOST_MAROWAK", "EVENT_RESCUED_MR_FUJI", "EVENT_GOT_POKE_FLUTE"],
    "bag": {"POKE_FLUTE": 1, "SILPH_SCOPE": 1, "TM_REST": 1, "POTION": 3},
    "badges": ["BOULDERBADGE", "MARSHBADGE"]}))

TOWER = ("The player is in Mr. Fuji's house and possesses the Silph Scope and "
         "Poke Flute, indicating they have reached the end of the tower")
BILL = ("the player has already helped Bill, and the event record indicates they "
        "have left Bill's house, implying the thief sequence in Cerulean is complete")
TUNNEL = ("The run has previously exited Rock Tunnel to Route 10, indicating the "
          "tunnel has been traversed")
ck("the tower reason is hedged", A._inferred(TOWER))
ck("...but names an item the bag holds", A._record_fact_named(TOWER, tmp) in ("POKE_FLUTE in the bag", "SILPH_SCOPE in the bag"),
   A._record_fact_named(TOWER, tmp))
ck("a fired event named verbatim counts",
   A._record_fact_named("EVENT_GOT_POKE_FLUTE has fired, suggesting the tower is done", tmp) == "EVENT_GOT_POKE_FLUTE fired")
ck("a badge worn counts",
   A._record_fact_named("the Marsh Badge is held, implying Sabrina is beaten", tmp) == "MARSHBADGE worn")
ck("the Bill reason names nothing the record confirms", A._record_fact_named(BILL, tmp) == "")
ck("the Rock Tunnel reason names nothing either", A._record_fact_named(TUNNEL, tmp) == "")
ck("an item not in the bag does not count",
   A._record_fact_named("possesses the Card Key, indicating Silph is open", tmp) == "")
ck("a machine's name is not a fact of this kind",
   A._record_fact_named("holds TM_REST, indicating the tower is done", tmp) == "")
ck("no record, no fact", A._record_fact_named(TOWER, tmp.with_name("none.json")) == "")

src = (ROOT / "planner/author.py").read_text()
cd = src[src.index("def check_done("):]
cd = cd[:cd.index("\ndef main")]
ck("check-done lets a hedged reason stand when it names a record fact",
   "_fact = _record_fact_named(_why)" in cd and "which the record confirms" in cd
   and cd.index("if not _fact:") < cd.index("which the record confirms"))
ad = src[src.index("def check_already_done("):]
ad = ad[:ad.index("\ndef ", 10)]
ck("...and so does already-done", '_fact = _record_fact_named(ans.get("why"))' in ad)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""Authors are shown the party's levels beside the trainers it has fought.

Run 71, 2026-11-03: the outline asked for levels once ("every party member
is at least level 50", before the Plateau), the train rule never ran in
nine hours, and PIKACHU and PIDGEY were still L8 when Erika sent out a L29
VICTREEBEL beside a L39 GRAVELER. The outline that had played well had a
level leg every few badges (user: "part of what made that one outline with
the mistakes good was that it had regular leveling legs"). Nothing an
author was shown set the party's levels beside the levels it was meeting.

Pinned: the record reads the run's own fight recaps (every loss, the last
fight in each gym, the latest few), says won or lost, the strongest foe
and the party then; it is empty with no fights; observed_text carries it
from the log beside explored.json; the outline upkeep pass carries it.
Synthetic: no game.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))


def recap(who, where, foes, party, lost=False):
    return {"kind": "fight_recap", "who": who, "where": where, "lost": lost,
            "foes": foes, "party": party, "text": ""}


tmp = Path(tempfile.mkdtemp())
log = tmp / "executor_log.jsonl"
rows = [recap("JR.TRAINER♂", "PEWTER_GYM", ["DIGLETT L11"],
              ["BULBASAUR L10", "PIKACHU L3"], lost=True),
        recap("BROCK", "PEWTER_GYM", ["GEODUDE L12", "ONIX L14"],
              ["BULBASAUR L14", "PIKACHU L3"])]
rows += [recap("BEAUTY", "CELADON_GYM", ["ODDISH L21"],
               ["VENUSAUR L36", "PIKACHU L8"]),
         recap("ERIKA", "CELADON_GYM", ["VICTREEBEL L29", "TANGELA L24"],
               ["VENUSAUR L37", "PIKACHU L8", "GRAVELER L39"])]
rows += [recap("BUG CATCHER", "ROUTE_16", [f"WEEDLE L{9 + i}"],
               ["VENUSAUR L37", "PIKACHU L8", "GRAVELER L39"]) for i in range(8)]
log.write_text("\n".join(json.dumps(r) for r in rows)
               + "\n" + json.dumps({"kind": "battle_start"}) + "\n")

t = A.level_record_text(log)
ck("the record is headed and says how levels are gained",
   "YOUR LEVELS AGAINST THE TRAINERS YOU HAVE FOUGHT" in t
   and "RARE CANDY" in t and "took part in it" in t, t[:400])
ck("a loss is kept and said", "JR.TRAINER♂ at PEWTER_GYM (LOST)" in t, t)
ck("a gym's last fight is its leader's, with the strongest foe",
   "BROCK at PEWTER_GYM (won): strongest sent out ONIX L14" in t, t)
ck("...and only the last fight of a gym is kept",
   "BEAUTY at CELADON_GYM" not in t and "ERIKA at CELADON_GYM (won)" in t, t)
ck("the party then, with its highest and lowest",
   "ERIKA at CELADON_GYM (won): strongest sent out VICTREEBEL L29; your "
   "party then: VENUSAUR L37, PIKACHU L8, GRAVELER L39 "
   "(highest L39, lowest L8)" in t, t)
ck("the latest few road fights are kept, older ones are not",
   "WEEDLE L16" in t and "WEEDLE L13" in t and "WEEDLE L12" not in t, t)
ck("the party at the last fight closes it",
   t.rstrip().endswith("YOUR PARTY AT THE LAST OF THESE: VENUSAUR L37, "
                       "PIKACHU L8, GRAVELER L39"), t[-200:])

empty = tmp / "empty.jsonl"
empty.write_text(json.dumps({"kind": "battle_start"}) + "\n")
ck("no fights, no record", A.level_record_text(empty) == "")
ck("no log, no record", A.level_record_text(tmp / "missing.jsonl") == "")

exp = tmp / "explored.json"
exp.write_text(json.dumps({"explored": {"PEWTER_CITY|4,2": {"north": {"n": 1, "to": "ROUTE_2|3,0"}}},
                           "visits": {"PEWTER_CITY|4,2": 3}}))
ck("observed_text carries it from the log beside explored.json",
   "ERIKA at CELADON_GYM (won)" in A.observed_text(exp))

src = (ROOT / "planner/author.py").read_text()
up = src[src.index("def _outline_upkeep_once"):][:6000]
ck("the outline upkeep pass carries it",
   'body += level_record_text(_RunPath("executor_log.jsonl"))' in up)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

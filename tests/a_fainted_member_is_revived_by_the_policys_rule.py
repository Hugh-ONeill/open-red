#!/usr/bin/env python3
"""A policy can write a field revive, and after a battle every fainted member
the bag and the reserve allow is brought back in the field.

Option A of the revive (user, 2026-09-30: "gotta be both to be consistent ...
queue A for when we can do a policy rewrite"). Run 19 walked Lorelei to Bruno
with members down and REVIVEs in the bag; option B put the op on the page and
the model never sent it outside a battle. field_heal has been a rule the model
writes; field_revive is the same for a fainted member, everywhere (not an E4
rule: feedback_no_area_specific_policy).
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import battle_policy as B  # noqa: E402


def mon(hp, mx=100):
    return {"species": "X", "hp": hp, "max_hp": mx}


def ow(party, bag, mode="overworld"):
    return {"mode": mode, "party": party, "bag": bag}


RULE = dict(B.DEFAULT_SPEC, field_revive={"item": "revive"})
ck("no rule, no revive", B.should_field_revive(
    ow([mon(50), mon(0)], {"REVIVE": 3}), B.DEFAULT_SPEC) is None)
B.reset_run_budget()
ck("the first fainted member in party order, with the weakest revive",
   B.should_field_revive(ow([mon(50), mon(0), mon(0)], {"REVIVE": 2, "MAX_REVIVE": 1}),
                         RULE) == ("REVIVE", 2))
B.reset_run_budget()
ck("prefer best_available reaches for the MAX_REVIVE",
   B.should_field_revive(ow([mon(50), mon(0)], {"REVIVE": 2, "MAX_REVIVE": 1}),
                         dict(RULE, field_revive={"item": "revive",
                                                  "prefer": "best_available"})) == ("MAX_REVIVE", 2))
ck("nobody down, nothing done", B.should_field_revive(ow([mon(50), mon(90)], {"REVIVE": 2}), RULE) is None)
ck("the whole party down is a blackout's to wake, not ours",
   B.should_field_revive(ow([mon(0), mon(0)], {"REVIVE": 2}), RULE) is None)
ck("not in a battle", B.should_field_revive(ow([mon(50), mon(0)], {"REVIVE": 2}, "battle"), RULE) is None)
ck("not without the item", B.should_field_revive(ow([mon(50), mon(0)], {"POTION": 5}), RULE) is None)
B.reset_run_budget()
RES = dict(B.DEFAULT_SPEC, field_revive={"item": "revive", "reserve": 2})
ck("the reserve holds back what the model kept (4 held, reserve 2: two spendable)",
   B.should_field_revive(ow([mon(50), mon(0)], {"REVIVE": 4}), RES) == ("REVIVE", 2))
ck("...and stops at it",
   B.should_field_revive(ow([mon(50), mon(0)], {"REVIVE": 2}), RES) is None)
B.reset_run_budget()
ck("...but never more than half of what the bag held when the party was made whole",
   B.should_field_revive(ow([mon(50), mon(0)], {"REVIVE": 1}), RES) == ("REVIVE", 2))

ok_spec = dict(B.DEFAULT_SPEC, field_revive={"item": "revive", "prefer": "best_available", "reserve": 1})
ck("a well-formed rule validates", B.validate_spec(ok_spec) == [], B.validate_spec(ok_spec))
bad = B.validate_spec(dict(B.DEFAULT_SPEC, field_revive={"item": "heal"}))
ck("a revive rule naming a potion is told what a fainted Pokemon takes",
   any("field_revive.item must be revive" in p for p in bad), bad)
bad2 = B.validate_spec(dict(B.DEFAULT_SPEC, field_revive={"item": "revive", "hp_below": 0.5}))
ck("...and a key it does not have is named", any("field_revive keys" in p for p in bad2), bad2)

import executor as E  # noqa: E402
src = inspect.getsource(E.Executor)
i_cure = src.index("pick = battle_policy.should_field_cure(obs, ACTIVE_SPEC)")
i_rev = src.index("battle_policy.should_field_revive(")
i_heal = src.index("pick = battle_policy.should_field_heal(obs, ACTIVE_SPEC)")
ck("after a battle: cure, then revive, then heal", i_cure < i_rev < i_heal)
blk = src[i_rev - 600:i_heal]
ck("the train rule's 'never' keeps medicine off a wild grind for it too",
   "_rp = None if _no_meds else" in blk and "if _no_meds:\n            pick = None" in src[i_rev:i_heal + 80])
ck("every fainted member, one item each, stopping when the game says no",
   "for _rv in range(6):" in blk and "if not _ok:" in src[i_rev:i_heal])
import calibrate_arenas as C  # noqa: E402
ck("the no-medicine arm takes the revive out too",
   C.strip_medicine(ok_spec)["field_revive"] is None)
doc = (ROOT / "planner/policy_author.py").read_text()
ck("the policy author is told the rule exists", 'field_revive: null or {"item": "revive"' in doc)
ck("...and it is not a league rule", "league" not in doc[doc.index("field_revive: null"):
                                                        doc.index("field_cure: list of")].lower())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

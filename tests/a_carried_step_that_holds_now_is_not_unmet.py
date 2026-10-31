#!/usr/bin/env python3
"""A carried step whose condition holds now is not said as unmet.

Run 69, 2026-10-31: withdraw_surf (has_item HM_SURF) was carried past
without the HM; a later step got HM03 from the Secret House, and every page
after went on saying "PREMISE UNMET: step withdraw_surf ... was NOT
achieved" beside "HM_SURF x1" in the bag.
"""
import sys, types
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E   # noqa: E402
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

plan = {"subgoals": [{"id": "withdraw_surf", "done_when": {"has_item": {"HM_SURF": 1}}},
                     {"id": "teach_surf", "done_when": {"knows_move": "SURF"}},
                     {"id": "go_to_route_19", "done_when": {"map": "ROUTE_19"}}]}
fake = types.SimpleNamespace(plan=plan, _carried_ids=["withdraw_surf", "teach_surf"],
                             _where=lambda o: "SAFARI_ZONE_CENTER|14,0")
party = [{"species": "GRAVELER", "moves": [{"id": "STRENGTH"}]}]
with_hm = {"map": {"id": "SAFARI_ZONE_CENTER"}, "bag": {"HM_SURF": 1}, "party": party}
no_hm = {"map": {"id": "SAFARI_ZONE_CENTER"}, "bag": {}, "party": party}
n1 = E.Executor._carried_premise_note(fake, plan["subgoals"][2], with_hm)
ck("the step that holds now is not said as unmet", "withdraw_surf" not in n1, n1)
ck("...the one still unmet is", "teach_surf" in n1 and "PREMISE UNMET" in n1, n1)
n2 = E.Executor._carried_premise_note(fake, plan["subgoals"][2], no_hm)
ck("without the item both are said", "withdraw_surf" in n2 and "teach_surf" in n2, n2)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok  " if ok else "FAIL"), n)
    if not ok and d: print("      ", str(d)[:300])
sys.exit(1 if bad else 0)

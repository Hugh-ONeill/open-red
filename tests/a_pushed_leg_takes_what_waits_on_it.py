#!/usr/bin/env python3
"""When a leg is moved later, the legs that cannot be done until it is move
with it.

Run 28 was stuck in Cerulean: no Cut, and the trashed house shut until the
Bill errand. The ladder read it right — "HM01 (CUT) is obtained from the
S.S. Anne in Vermilion City, creating a circular dependency" — and pushed
"Reach Vermilion City" behind "Retrieve the S.S. Ticket from Bill". It left
"Defeat Lt. Surge for the Thunder Badge" standing in front of both, and his
gym is IN Vermilion, so the next leg was exactly as unreachable as the one
just moved (user, 2026-09-20).

Which legs wait on another is the model's knowledge, so the question asks
for them ("with"). The harness only bounds the answer: a number must name a
leg that stands between the pushed one and its new place, at most three,
never the leg itself, and each is pushed to sit after the same leg.

Pinned: the ask is in the question; the answer is read and bounded; the
names are kept by TEXT, not position; the chain pushes each of them to the
same anchor; no answer, no change. Synthetic."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import brock_probe  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


OUTLINE = [
    (13, "Defeat Lt. Surge for the Thunder Badge"),
    (14, "Retrieve the S.S. Ticket from Bill"),
    (15, "Reach Vermilion City"),
    (16, "Retrieve the HM01 from the S.S. Anne"),
    (17, "every party member is at least level 30"),
]


def ask(answer, goal="Reach Vermilion City", n=13, ahead=OUTLINE):
    brock_probe.chat = lambda msgs, model, **kw: json.dumps(answer)
    A.LATER_WITH[:] = []
    at = A.check_later(goal, n, ahead, "", "", "m")
    return at, list(A.LATER_WITH)


_sys = " ".join(A.LATER_SYS.split())      # the prompt is wrapped
ck("the question asks what moves with it",
   '"with": [N, N]' in _sys
   and "cannot be done until it is" in _sys
   and "at most three" in _sys)

at, with_ = ask({"why": "the ticket comes first", "after": 15, "with": [14]})
ck("a leg that waits on the pushed one is carried",
   at == 15 and with_ == ["Retrieve the S.S. Ticket from Bill"], (at, with_))
ck("...by its words, not its number",
   all(isinstance(w, str) for w in with_))

at, with_ = ask({"why": "x", "after": 15, "with": []})
ck("no companion named, nothing carried", at == 15 and with_ == [])
at, with_ = ask({"why": "x", "after": 15})
ck("...and the key may be left out entirely", at == 15 and with_ == [])

at, with_ = ask({"why": "x", "after": 15, "with": [17]})
ck("a leg already past the new place is refused", at == 15 and with_ == [],
   with_)
at, with_ = ask({"why": "x", "after": 15, "with": [13]})
ck("...and so is the leg being moved itself", at == 15 and with_ == [])
at, with_ = ask({"why": "x", "after": 15, "with": [99]})
ck("...and a number that is no leg at all", at == 15 and with_ == [])
at, with_ = ask({"why": "x", "after": 15, "with": ["14"]})
ck("a number written as text still counts",
   with_ == ["Retrieve the S.S. Ticket from Bill"], with_)

BIG = [(13, "A")] + [(i, f"leg {i}") for i in range(14, 20)]
at, with_ = ask({"why": "x", "after": 19, "with": [14, 15, 16, 17, 18]},
                goal="A", ahead=BIG)
ck("at most three ride along", at == 19 and len(with_) == 3, with_)
at, with_ = ask({"why": "x", "after": 19, "with": [14, 14, 15]},
                goal="A", ahead=BIG)
ck("...and a repeat is not two of them", len(with_) == 2, with_)

at, with_ = ask({"why": "it belongs here", "after": None, "with": [14]})
ck("a leg that is not moved carries nothing", at == 0 and with_ == [])

# ---- an arrival takes the deeds done in that place, named or not -------
# Run 28 pushed "Reach Celadon City" to 31 and the model named the Game
# Corner and the Silph Scope but forgot the department store, which then
# stood fifteen legs before the city it is in (user, 2026-09-20).
CEL = [(16, "Reach Celadon City"),
       (17, "Visit the Celadon Department Store"),
       (18, "Infiltrate the Rocket Game Corner"),
       (19, "every party member is at least level 30"),
       (20, "Reach Lavender Town"),
       (21, "Clear the Pokemon Tower")]
at, with_ = ask({"why": "the guard wants a drink", "after": 21, "with": [18]},
                goal="Reach Celadon City", n=16, ahead=CEL)
ck("the deed in that place is carried even though nobody named it",
   at == 21 and "Visit the Celadon Department Store" in with_, with_)
ck("...and what the model did name is carried too",
   "Infiltrate the Rocket Game Corner" in with_, with_)
ck("...while a leg that is about somewhere else stays",
   "Reach Lavender Town" not in with_ and "Clear the Pokemon Tower" not in with_
   and "every party member is at least level 30" not in with_, with_)
at, with_ = ask({"why": "x", "after": 21, "with": []},
                goal="Clear the Pokemon Tower", n=16,
                ahead=[(16, "Clear the Pokemon Tower"),
                       (17, "Reach Lavender Town"), (21, "Reach Fuchsia City")])
ck("a leg that is not an arrival carries nothing by place",
   with_ == [], with_)
at, with_ = ask({"why": "x", "after": 19, "with": []},
                goal="Reach Celadon City", n=16,
                ahead=[(16, "Reach Celadon City"),
                       (17, "Reach Celadon City again"),
                       (19, "Defeat Erika for the Rainbow Badge")])
ck("...and an arrival does not drag another arrival along",
   with_ == [], with_)

src = (ROOT / "planner/author.py").read_text()
ck("the names are written where the chain can read them",
   'Path("run/outline_push_with").write_text(' in src)
sh = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain pushes each of them to the same leg",
   "run/outline_push_with" in sh
   and 'python planner/push_leg.py "$_ci" "$_ai"' in sh
   and '_anchor=$(sed -n "${at}p" plans/outline.txt)' in sh)
ck("...and finds them by text, because the first push moved the numbers",
   'grep -nxF -- "$_co" plans/outline.txt' in sh
   and 'grep -nxF -- "$_anchor" plans/outline.txt' in sh)
ck("...and clears the list afterwards", ": > run/outline_push_with" in sh)
ck("their plans are archived like the pushed leg's own",
   'archive_plans_of "$_co"' in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

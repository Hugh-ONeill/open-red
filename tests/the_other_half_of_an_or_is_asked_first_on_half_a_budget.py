#!/usr/bin/env python3
"""The other half of an "or" is asked for first, and tried on half a budget.

Run of record 3, 2026-09-24: "the party holds a FIGHTING or GRASS type" was
true on arrival (Bulbasaur), so the chain ran its one try at FIGHTING. The
plan beat Brock, the gym the leg was for, and then spent the rest of a
full attempt hunting a Mankey on Route 2, where there are none (user: "for
some reason it picked up a rat and its looking for a mankey now even
though it already defeated brock" ... "do both, half budget and ask
first").

Pinned: what the leg was for is read against the banked list the outline
pass numbered, not the live outline that has since lost a leg; the model
is shown the leg, the half missing, that purpose and what is ahead, and
its no is kept; an unreadable or failed ask keeps the try; the author asks
before writing a bonus plan and writes none on a no; the executor halves
the round budget for a bonus plan. Synthetic, the model stubbed."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import brock_probe  # noqa: E402
import or_leg as O  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


LEG = "the party holds a FIGHTING or GRASS type"
d = Path(tempfile.mkdtemp(prefix="orask_"))
(d / "plans").mkdir()
(d / "run").mkdir()
(d / "plans/outline.upkeep").write_text(f"{LEG}\nthe party has at least 2 Pokemon\n")
# the banked list: five story legs, Brock the fifth
(d / "plans/outline.authored").write_text("\n".join([
    "Pick a starter", "Battle the rival", "Reach Viridian City", "Reach Pewter City",
    "the party has at least 2 Pokemon", LEG, "Defeat Brock for the Boulder Badge",
    "Reach Mt. Moon"]) + "\n")
# the live outline has since lost "Reach Viridian City"
(d / "plans/outline.txt").write_text("\n".join([
    "Pick a starter", "Battle the rival", "Reach Pewter City",
    "the party has at least 2 Pokemon", LEG, "Defeat Brock for the Boulder Badge",
    "Reach Mt. Moon"]) + "\n")
(d / "plans/outline.notes").write_text(
    f"{LEG}\tfor: 5\nthe party has at least 2 Pokemon\tfor: getting through the forest\n"
    "the party holds a FLYING type\tfor: 99\n")
(d / "run/outline_leg").write_text("5")
(d / "run/obs.json").write_text(json.dumps(
    {"party": [{"types": ["GRASS", "POISON"]}, {"types": ["NORMAL"]}]}))
os.chdir(d)

ck("what a leg was for is read against the banked list the pass numbered",
   O.purpose(LEG) == "Defeat Brock for the Boulder Badge", O.purpose(LEG))
ck("...a purpose in words is passed through as said",
   O.purpose("the party has at least 2 Pokemon") == "getting through the forest")
ck("...and a number the list does not have is left as said",
   O.purpose("the party holds a FLYING type") == "for: 99")

seen = {}


def stub(reply):
    def chat(msgs, model, **kw):
        seen["body"] = msgs[-1]["content"]
        seen["sys"] = msgs[0]["content"]
        if isinstance(reply, Exception):
            raise reply
        return reply
    return chat


brock_probe.chat = stub('Sure. {"why": "Brock is beaten already.", "try": false}')
go, why = O.ask(LEG, "the party holds a FIGHTING type", "standing in PEWTER_GYM, BOULDERBADGE", "m")
ck("the model's no is kept, with its words", go is False and why == "Brock is beaten already.", (go, why))
b = seen.get("body", "")
ck("it is shown the half it lacks and what the leg was for",
   "catch a FIGHTING type." in b and "FOR: Defeat Brock for the Boulder Badge" in b, b)
ck("...where the run stands, and what is ahead on the live outline",
   "BOULDERBADGE" in b and "6. Defeat Brock for the Boulder Badge" in b
   and "7. Reach Mt. Moon" in b, b)
ck("...and that the leg counts as done either way",
   "counts as done either way" in seen.get("sys", ""))
brock_probe.chat = stub("I think so")
ck("an unreadable answer keeps the try", O.ask(LEG, "x", "s", "m")[0] is True)
brock_probe.chat = stub(OSError("refused"))
ck("a failed ask keeps the try", O.ask(LEG, "x", "s", "m")[0] is True)
O.record_ask(LEG, "the party holds a FIGHTING type", False, "no")
(d / "run/executor_log.jsonl").open("a").write(json.dumps(
    {"kind": "or_leg_bonus", "leg": LEG, "bonus": "the party holds a FIGHTING type"}) + "\n")
ck("the author finds which leg a bonus goal came from",
   O.last_bonus_leg("the party holds a FIGHTING type") == LEG)

au = (ROOT / "planner/author.py").read_text()
hook = au[au.index('THE OTHER HALF OF AN "OR" IS ASKED FOR BEFORE IT IS PLANNED'):]
hook = hook[:hook.index("    if args.check_done:")]
ck("the author asks before writing a bonus plan, and writes none on a no",
   '"_bonus_" in args.out.name' in hook and "or_leg.ask(" in hook
   and "if not _go:\n                sys.exit(3)" in hook)
ex = (ROOT / "planner/executor.py").read_text()
ck("the executor gives a bonus plan half the rounds",
   '"_bonus_" in Path(str(getattr(self, "plan_path", "") or "")).name' in ex
   and "rounds = max(1, (rounds + 1) // 2)" in ex)
sh = (ROOT / "fresh_discovery.sh").read_text()
ck("...which is the name the chain gives it",
   '_bp="plans/leg_$(printf \'%02d\' "$i")_bonus_' in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

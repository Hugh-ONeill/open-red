#!/usr/bin/env python3
"""A slot_level check follows the Pokemon that stood in that slot when the
plan began, by its DVs and trainer id, through reorders and evolution.

Run 27 (2026-09-19): leg 26's steps said "Level up Graveler" and checked
"slot 4"; the model's own swaps put Pidgeot there, and the trainee switch-in
sent Pidgeot in 63 times in one Graveler step. Across runs the harness
switched "the slot's occupant" in 5,128 times, which with a drifting slot is
switch-feeding by accident (user: "we also have to combat the accidental
switch-feeding behavior").

Pinned: an unpinned check reads the slot as before; a pinned one follows
its Pokemon when moved; through an evolution (species changes, DVs do not);
the pin is written once and never re-pinned; the check, the switch-in and
the page line all read the same slot. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def mon(sp, lv, dv):
    return {"species": sp, "level": lv, "dvs": dv, "otId": 777, "hp": 50, "max_hp": 50}


GRAV = mon("GRAVELER", 37, {"atk": 9, "def": 3, "spd": 14, "spc": 7})
PIDG = mon("PIDGEOT", 40, {"atk": 1, "def": 2, "spd": 3, "spc": 4})
LAPR = mon("LAPRAS", 41, {"atk": 5, "def": 5, "spd": 5, "spc": 5})
start = [LAPR, PIDG, mon("KADABRA", 44, {"atk": 8, "def": 8, "spd": 8, "spc": 8}), GRAV]

ck("an unpinned check reads the slot as written", E.slot_of({"slot": 4, "min": 40}, start) == 4)

ex = object.__new__(E.Executor)
ex.logs = []
ex.log = lambda k, **kw: ex.logs.append((k, kw))
ex.plan_path = None
subs = [{"id": "train_graveler", "done_when": {"slot_level": {"slot": 4, "min": 40}}}]
ex.plan = {"subgoals": subs}
ex._pin_slot_levels(subs, {"party": start})
want = subs[0]["done_when"]["slot_level"]
ck("the pin records who stood there", want.get("who", {}).get("species") == "GRAVELER"
   and want["who"].get("dvs") == GRAV["dvs"], want)
moved = [GRAV, PIDG, start[2], LAPR]
ck("a pinned check follows its Pokemon when it is moved to the front", E.slot_of(want, moved) == 1)
ck("...so the check reads Graveler, not the Pokemon now in slot 4",
   not E.pred_holds({"slot_level": want}, {"party": moved})
   and E.pred_holds({"slot_level": dict(want, min=37)}, {"party": moved}))
evolved = [dict(GRAV, species="GOLEM", level=40), PIDG, start[2], LAPR]
ck("...and through an evolution", E.slot_of(want, evolved) == 1
   and E.pred_holds({"slot_level": want}, {"party": evolved}))
ex._pin_slot_levels(subs, {"party": moved})
ck("the pin is never re-pinned from a reordered party", want["who"]["species"] == "GRAVELER")
src = (ROOT / "planner/executor.py").read_text()
ck("the trainee switch-in reads the pinned slot",
   'slot_of(dw0.get("slot_level"), (obs or {}).get("party") or []))' in src)
ck("...and so does the page line", '_slot = (slot_of(dw_val, party)' in src)
ck("the plan pins its checks at start", "self._pin_slot_levels(subgoals, self.settle())" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

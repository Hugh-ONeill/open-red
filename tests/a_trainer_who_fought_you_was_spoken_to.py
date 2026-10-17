#!/usr/bin/env python3
"""A trainer beaten in a fight he started is not "never spoken to".

Run 58, 2026-10-17: ROCKETHIDEOUTB4F_ROCKET3 came at the run by sight and
was beaten (EVENT_BEAT_ROCKET_HIDEOUT_4_TRAINER_2 set). In this game the
LIFT KEY falls only when he is spoken to after the fight, and his row on
the page read "never spoken to", which was false; the run rode the dead
lift back and forth (user: "it looks like the rocket didnt drop the lift
key").

Pinned: a beaten trainer never pressed reads as beaten and not spoken to
since; an unbeaten one still reads unbeaten; a person who is not a
trainer still reads never spoken to. Ranking is unchanged: the beaten one
keeps the unspoken status. Synthetic: no game.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import ledger                                          # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

HERE = "ROCKET_HIDEOUT_B4F|17,1"


class _Ex:
    frontier = {}
    _inert_objs = {}
    def __init__(self):
        self.explored = {HERE: {}}
        self.visits = {HERE: 2}
        self.hints = {}
        self.hints_at = {}
    def _where(self, _o): return HERE
    def _taken_here(self, h): return {}
    def _spent_exits(self, h): return {}
    def _sealed(self, h): return set()
    def _untaken(self, m, t): return set()
    def _worth_another_word(self, h, o, backfill=True): return []
    def _door_groups(self, w): return {}
    def _frontage(self, d): return ""
    def _seen_cells_words(self, h): return ""
    def _walked_dest(self, mid, key): return None
    def _snapshot_anywhere(self, o): return None
    def _frontier_left(self, r): return set()
    def dead_for(self, t, r): return 0
    def _not_for_explore_to_press(self, k, kind, h): return False
    def __getattr__(self, _n): return {}


def row(obj):
    obs = {"party": [], "mode": "overworld", "player": {"x": 17, "y": 1},
           "map": {"id": "ROCKET_HIDEOUT_B4F", "region": "17,1",
                   "objects": [obj], "connections": {}, "warps": []}}
    ex = _Ex()
    cands = ledger.build(ex, obs)
    c = next((c for c in cands if c.key == obj["name"]), None)
    try:
        ln = next((ln for ln in ledger.render(cands, ex, obs).splitlines()
                   if obj["name"] + " (" in ln), "")
    except Exception as e:                               # noqa: BLE001
        ln = f"render raised {e!r}"
    return c, ln


c, ln = row({"name": "ROCKETHIDEOUTB4F_ROCKET3", "kind": "trainer",
             "x": 11, "y": 2, "reachable": True, "beaten": True})
ck("a beaten trainer never pressed is not said never spoken to",
   "— never spoken to" not in ln, ln)
ck("...it is said beaten, and not spoken to since",
   "beaten in a fight they started; never spoken to since" in ln, ln)
ck("...and keeps the unspoken status, so nothing ranks differently",
   c is not None and c.status == "unspoken", c and c.status)

c, ln = row({"name": "ROCKETHIDEOUTB4F_ROCKET1", "kind": "trainer",
             "x": 13, "y": 4, "reachable": True, "beaten": False})
ck("an unbeaten trainer still reads unbeaten",
   c is not None and c.status == "unbeaten" and "beaten in a fight" not in ln,
   (c and c.status, ln))

c, ln = row({"name": "ROCKETHIDEOUTB4F_GIRL", "kind": "npc",
             "x": 13, "y": 4, "reachable": True})
ck("a person who is not a trainer still reads never spoken to",
   "never spoken to" in ln and "beaten" not in ln, ln)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

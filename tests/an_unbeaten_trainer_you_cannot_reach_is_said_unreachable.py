#!/usr/bin/env python3
"""A trainer you have not beaten and cannot walk to reads as both.

Run 29, 2026-10-02: MTMOONB2F_ROCKET4 stood on Mt Moon B2F ground that
neither part of B2F the run had stood in reaches. The row's "unreachable"
was overwritten by "unbeaten", so it read "pressed 0x and still standing
here" from both parts, and the run went between them by B1F for twenty
rounds, each part sure the other reached him (user: "its just pingponging
between the two incorrect bf2 rooms").

Pinned: the verdict stays "unreachable" with "not beaten" beside it; a
reachable unbeaten trainer still reads unbeaten; and the shim's flood of
the other stood-in parts is said for things as it is for doors.
Synthetic: no game.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import ledger                                          # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

HERE = "MT_MOON_B2F|27,5"


class _Ex:
    frontier = {}
    _inert_objs = {}
    def __init__(self):
        self.explored = {HERE: {}}
        self.visits = {HERE: 12}
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


def cand(obj):
    obs = {"party": [], "mode": "overworld", "player": {"x": 27, "y": 5},
           "map": {"id": "MT_MOON_B2F", "region": "27,5", "objects": [obj],
                   "connections": {}, "warps": []}}
    for c in ledger.build(_Ex(), obs):
        if c.key == obj["name"]:
            return c
    return None


far = cand({"name": "MTMOONB2F_ROCKET4", "kind": "trainer", "x": 29, "y": 17,
            "reachable": False, "beaten": False, "stood_parts": 1})
ck("an unbeaten trainer no walk reaches keeps the unreachable verdict",
   far is not None and far.status == "unreachable", far and far.status)
ck("...with not-beaten said beside it",
   far is not None and "you have not beaten them" in (far.note or ""), far and far.note)
ck("...and that no other stood-in part of the floor reaches him either",
   far is not None and "nor does any of the 1 other part(s)" in (far.note or ""),
   far and far.note)

near = cand({"name": "MTMOONB2F_ROCKET1", "kind": "trainer", "x": 27, "y": 7,
             "reachable": True, "beaten": False})
ck("a reachable unbeaten trainer still reads unbeaten",
   near is not None and near.status == "unbeaten", near and near.status)

other = cand({"name": "MTMOONB2F_ROCKET4", "kind": "trainer", "x": 29, "y": 17,
              "reachable": False, "beaten": False, "stood_parts": 1,
              "from": ["MT_MOON_B2F|23,21"]})
ck("a stood-in part that does reach him is named",
   other is not None and "MT_MOON_B2F|23,21 DOES reach it" in (other.note or ""),
   other and other.note)

lua = (ROOT / "harness/shim.lua").read_text()
ck("the shim floods the other stood-in parts for things, as for doors",
   "ob.from[#ob.from + 1] = m.id .. \"|\" .. name" in lua
   and "ob.stood_parts = nparts" in lua)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

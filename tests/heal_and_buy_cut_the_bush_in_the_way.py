#!/usr/bin/env python3
"""heal and buy cut the bush their walk blames, the way go does.

Both walk to a door, and a Cut tree across the way left them saying only
"could not get through the Center door at 11,3" — the walk's own reason
dropped, nothing cut (user, 2026-09-16: "the 'heal' op doesnt cut through
bushes in the way, it eventually got through but it should work like go
does shouldnt it? same with buy i guess"). Pinned: the shim keeps the
walk's reason on heal's and the shop door's refusal; the executor cuts only
the bush that reason blames, only when a party Pokemon knows CUT, and tries
the op once more.

Synthetic: source anchors and the blame reader; no game, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


SH = (ROOT / "harness/shim.lua").read_text()
SRC = (ROOT / "planner/executor.py").read_text()

ck("heal keeps the walk's reason on its refusal",
   'local _okw, _whyw = OPS.use_warp(G, { x = d.x, y = d.y })' in SH
   and '.. (_whyw and (" — " .. tostring(_whyw)) or "")' in SH)
ck("the shop door keeps it too, as a third return",
   'return false, "door", ("could not get through the shop door at "' in SH)
ck("buy and sell both pass it on",
   SH.count('if shop_why == "door" then return false, shop_door_why end') == 2
   and SH.count("went_in, shop_why, shop_door_why = enter_shop(G)") == 2)

ex = object.__new__(E.Executor)
PARTY_CUT = {"party": [{"species": "IVYSAUR",
                        "moves": [{"id": "BODY_SLAM"}, {"id": "CUT"}]}]}
PARTY_NO = {"party": [{"species": "PIDGEY", "moves": [{"id": "GUST"}]}]}
DET = ("could not get through the Center door at 11,3 — couldn't reach the "
       "warp tile (no path — the ground you have SEEN and can walk from here "
       "is 40 cell(s) ... standing between the ground you can reach and the "
       "rest of this map: CUT_TREE (a bush CUT clears) at (15,17))")
ck("the blamed bush is read out of heal's refusal",
   ex._blamed_bush(DET, PARTY_CUT) == (15, 17))
ck("...and not when nobody knows CUT", ex._blamed_bush(DET, PARTY_NO) is None)
ck("...and not a bush the shim ruled out",
   ex._blamed_bush("could not get through the Center door at 11,3 — no path. "
                   "Also near that edge, though not what stopped you: CUT_TREE "
                   "(a bush CUT clears) at (15,17)", PARTY_CUT) is None)

blk = SRC[SRC.index("A BUSH ACROSS THE WAY TO A COUNTER IS CUT, AS GO CUTS IT."):]
blk = blk[:blk.index("# the op's OWN detail, before settle/battles replace it")]
ck("the executor cuts for heal, buy and sell only",
   'op in ("heal", "buy", "sell")' in blk)
ck("...the bush the refusal blames, then tries the op once more",
   'self._blamed_bush(_rrb.get("detail"), obs)' in blk
   and 'self._send_safe("field_move", move="CUT"' in blk
   and blk.count("self.b.send(op, **self._named(op, step))") == 1
   and '_op_bush_retried' in blk)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

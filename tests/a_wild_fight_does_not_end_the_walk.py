#!/usr/bin/env python3
"""A walk or crossing the model sent, cut short by a wild fight, goes on
after the fight from where it left the party.

Run 27, 2026-09-18, Route 21: walk_to(4,0) said "ok" from 78 cells short
(the fight was still up when the position was read, so the stopped-short
check saw a blank), and cross north ended its round at "a fight started 78
cell(s) short ... nothing has been learned" — one wild Tentacool per round
up ninety cells of sea.

Pinned: after a fight the same op is sent again, up to three times, while
each try moves the party; a crossing that lands after a fight reports ok and
the fights; no fight, no resend. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ow(x, y, mid="ROUTE_21"):
    return {"mode": "overworld", "player": {"x": x, "y": y}, "map": {"id": mid}}


BATTLE = {"mode": "battle"}


def fake(script):
    """script: list of (reply, obs-after) per send; each obs-after may be a
    battle, which handle_battle turns into the next queued overworld obs."""
    ex = object.__new__(E.Executor)
    ex.sent, ex.logs = [], []
    st = {"o": None, "after_battle": None}
    q = list(script)

    def send(op, **kw):
        ex.sent.append(op)
        reply, after, post = q.pop(0) if q else ({"result": {"ok": False, "detail": "no path"}}, st["o"], None)
        st["o"], st["after_battle"] = after, post
        return reply
    ex._send_safe = send
    ex.settle = lambda *a, **k: st["o"]

    def hb(sg, o):
        st["o"] = st["after_battle"]
        return st["o"]
    ex.handle_battle = hb
    ex.log = lambda k, **kw: ex.logs.append(k)
    return ex, st


ok = {"result": {"ok": True, "detail": ""}}
ex, st = fake([(ok, BATTLE, ow(4, 30)), (ok, ow(4, 0), None)])
st["o"], st["after_battle"] = BATTLE, ow(14, 71)
o, n = ex._walk_on_after_fights({"id": "t"}, "walk_to", {"x": 4, "y": 0}, BATTLE)
ck("a walk cut by fights is sent again until it arrives", o["player"] == {"x": 4, "y": 0}, (o, ex.sent))
ck("...counting the fights", n == 2, n)
ck("...two resends", ex.sent == ["walk_to", "walk_to"], ex.sent)

ex, st = fake([])
o, n = ex._walk_on_after_fights({"id": "t"}, "walk_to", {"x": 4, "y": 0}, ow(9, 9))
ck("no fight, no resend", ex.sent == [] and n == 0, (ex.sent, n))

cut = {"result": {"ok": False, "detail": "a fight started 20 cell(s) short of the north edge gap (7,0) — the walk stopped at (7,20) because of the battle"}}
land = {"result": {"ok": True, "detail": "crossed — now on PALLET_TOWN"}}
ex, st = fake([(cut, BATTLE, ow(7, 20)), (land, ow(10, 17, "PALLET_TOWN"), None)])
st["o"], st["after_battle"] = BATTLE, ow(14, 71)
o, n, r = ex._cross_on_after_fights({"id": "t"}, {"dir": "north", "surf": True}, BATTLE)
ck("a crossing cut by fights goes on until it lands", (r.get("result") or {}).get("ok") and o["map"]["id"] == "PALLET_TOWN", (o, r))
ck("...and counts them", n == 2, n)

stuck = {"result": {"ok": False, "detail": "a fight started 5 cell(s) short — because of the battle"}}
ex, st = fake([(stuck, BATTLE, ow(14, 71)), (stuck, BATTLE, ow(14, 71))])
st["o"], st["after_battle"] = BATTLE, ow(14, 71)
o, n, r = ex._cross_on_after_fights({"id": "t"}, {"dir": "north"}, BATTLE)
ck("a crossing that gets no further stops", len(ex.sent) == 1, ex.sent)

src = (ROOT / "planner/executor.py").read_text()
ck("the runner's walk_to reads through the fights before judging arrival",
   "obs, _fights = self._walk_on_after_fights(sg, \"walk_to\"," in src)
ck("the runner's cross goes on after fights before failing",
   "obs, _fights, _r0 = self._cross_on_after_fights(sg, step, obs)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

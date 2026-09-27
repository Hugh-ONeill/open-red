#!/usr/bin/env python3
"""A heal or shop trip that ends away from where it began leaves one line on
the page, and for the author, until the party is back there or the leg
changes.

Run of record 11 (2026-09-27): out of Rock Tunnel's south mouth, the next
plan's first step was a heal; the only Center it knew was at the north
mouth, six legs back through the tunnel, and once healed nothing said
where it had been standing. It set off somewhere else entirely (user: "i
wish it remembered what it was doing and went right back").

Pinned: a heal step that walks away over several rounds is one trip, from
where its first round stood; a heal where the party already stands is no
detour; a shop op is a trip too; the page line names where it left from,
where the trip ended and the walk back, and leaves the choice to the
model; it clears when the party is back and when the leg changes; the
author gets it for the same leg only. Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def fake():
    ex = object.__new__(E.Executor)
    ex._leg_goal = "Reach Lavender Town"
    ex.logged = []
    ex.log = lambda kind, **kw: ex.logged.append((kind, kw))
    ex._save_memory = lambda: None
    ex._where = lambda obs: obs["_region"]
    ex._route = lambda a, b: [("8,53", b)] * 6
    return ex


def obs(region, healthy):
    hp = 50 if healthy else 10
    return {"_region": region, "party": [{"hp": hp, "max_hp": 50, "status": None}]}


HEAL = {"party_healthy": True}
sg = {"id": "heal_party"}
ex = fake()
ex._detour_before(sg, HEAL, [{"op": "go", "to": "ROUTE_10|0,4"}],
                  obs("ROUTE_10|14,52", False))
ex._detour_after(sg, [{"op": "go"}], obs("ROUTE_10|0,4", False))
ck("a heal step still walking keeps its trip open",
   getattr(ex, "_detour", None) is None and ex._detour_open["from"] == "ROUTE_10|14,52")
ex._detour_before(sg, HEAL, [{"op": "heal"}], obs("ROUTE_10|0,4", False))
ex._detour_after(sg, [{"op": "heal"}], obs("ROCK_TUNNEL_POKECENTER|0,3", True))
ck("...and one that heals away from its first round's ground is a detour from there",
   ex._detour == {"from": "ROUTE_10|14,52", "to": "ROCK_TUNNEL_POKECENTER|0,3",
                  "why": "heal", "leg": "Reach Lavender Town"}
   and ex.logged and ex.logged[-1][0] == "detour", getattr(ex, "_detour", None))

line = ex._detour_line("ROUTE_9|0,8")
ck("the page names where it left from and where the trip ended",
   "YOU LEFT ROUTE_10|14,52 TO HEAL, and finished at ROCK_TUNNEL_POKECENTER|0,3"
   in line, line)
ck("...with the walk back over walked ground",
   '{"op":"go","to":"ROUTE_10|14,52"} walks back over ground you have walked (6 leg(s))'
   in line, line)
ck("...and leaves the choice to the model", "is yours to judge" in line
   and "should" not in line)
ck("it clears when the party is back",
   ex._detour_line("ROUTE_10|14,52") == "" and ex._detour is None)

ex = fake()
ex._detour_before(sg, HEAL, [{"op": "heal"}], obs("CERULEAN_CITY|20,0", False))
ex._detour_after(sg, [{"op": "heal"}], obs("CERULEAN_CITY|20,0", True))
ck("a heal where the party already stands is no detour",
   getattr(ex, "_detour", None) is None)

ex = fake()
buy = {"id": "reach_route_11"}
ex._detour_before(buy, {"map": "ROUTE_11"}, [{"op": "buy", "item": "POTION"}],
                  obs("ROUTE_10|14,52", True))
ex._detour_after(buy, [{"op": "buy"}], obs("CERULEAN_MART|0,2", True))
ck("a shop op is a trip too", (ex._detour or {}).get("why") == "shop")
ex._leg_goal = "Obtain the POKE FLUTE"
ck("it clears when the leg changes",
   ex._detour_line("ROUTE_9|0,8") == "" and ex._detour is None)

tmp = Path(tempfile.mkdtemp(prefix="detour_"))
(tmp / "explored.json").write_text(json.dumps({"detour": {
    "from": "ROUTE_10|14,52", "to": "ROCK_TUNNEL_POKECENTER|0,3", "why": "heal",
    "leg": "Reach Lavender Town (a doubt you recorded when outlining: for: X)"}}))
t = A.detour_text("Reach Lavender Town", tmp)
ck("the author gets it for the same leg",
   "YOU LEFT ROUTE_10|14,52 TO HEAL during this objective" in t, t)
ck("...and not for another", A.detour_text("Obtain the POKE FLUTE", tmp) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("every escalation round is bracketed by the trip record",
   "self._detour_before(sg, done, macro, self.settle() or obs)" in src
   and "self._detour_after(sg, macro, self.settle() or obs)" in src)
ck("the ledger keeps it", '"detour": getattr(self, "_detour", None)' in src
   and 'self._detour = data.get("detour") or None' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

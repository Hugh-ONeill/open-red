#!/usr/bin/env python3
"""A fall on record is a route leg, and the walker takes it by walking onto
the hole. Run 27, 2026-09-18, Mansion 3F: with the 3F hole's fall on record
every `go` routed through (16,14), the walker looked for a door there,
found none, and ended with "this map has no such way out any more"; the
route hint called the hole "door (16,14)".

Pinned: the hop sends walk_to onto the hole and carries on when the fall
lands on the next leg; a hop that does not drop is abandoned with its
reason; a hole's first leg is worded as a hole, a door's as a door.
Synthetic, no game."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def obs(mid, x, y):
    return {"mode": "overworld", "player": {"x": x, "y": y},
            "map": {"id": mid, "warps": [{"x": 6, "y": 1}], "connections": {}}}


def fake(lands):
    ex = object.__new__(E.Executor)
    ex.map_holes = {"POKEMON_MANSION_3F": ["16,14", "19,14"]}
    ex.sent = []
    ex.logs = []
    state = {"o": obs("POKEMON_MANSION_3F", 10, 6)}

    class B:
        def obs(self_b):
            return state["o"]
    ex.b = B()

    def send(op, **kw):
        ex.sent.append((op, kw))
        if op == "walk_to" and (kw.get("x"), kw.get("y")) == (16, 14):
            state["o"] = lands
        return {"result": {"ok": True, "detail": ""}}
    ex._send_safe = send
    ex.settle = lambda *a, **k: state["o"]
    ex._where = lambda o: (f"{o['map']['id']}|12,14" if o["map"]["id"] == "POKEMON_MANSION_1F"
                           else f"{o['map']['id']}|1,1")
    ex.log = lambda kind, **kw: ex.logs.append((kind, kw))
    ex.WHY_BUDGET = 300
    return ex


ex = fake(obs("POKEMON_MANSION_1F", 16, 14))
got = ex._walk_route({"id": "t"}, [("16,14", "POKEMON_MANSION_1F|12,14")])
ck("the hop walks onto the hole", ("walk_to", {"x": 16, "y": 14}) in ex.sent, ex.sent)
ck("...never a use_warp", not any(op == "use_warp" for op, _ in ex.sent), ex.sent)
ck("...and a fall that lands on the next leg is not abandoned",
   not any(k == "route_abandoned" for k, _ in ex.logs), ex.logs)

ex = fake(obs("POKEMON_MANSION_3F", 15, 14))
ex._send_safe = lambda op, **kw: (ex.sent.append((op, kw)) or {"result": {"ok": False, "detail": "no path"}})
ex._walk_route({"id": "t"}, [("16,14", "POKEMON_MANSION_1F|12,14")])
ck("a hop that does not drop is abandoned with its reason",
   any(k == "route_abandoned" and "hole" in kw.get("why", "") for k, kw in ex.logs), ex.logs)
ck("...and the reason names the hole", "is a hole in this floor" in str(getattr(ex, "_route_why", "")))

h = fake(None)
ck("a hole's first leg is worded as a hole",
   ledger.leg_words(h, "POKEMON_MANSION_3F|1,1", "16,14") == "hole (16,14), walked onto")
ck("a door's first leg is still a door", ledger.leg_words(h, "POKEMON_MANSION_3F|1,1", "6,1") == "door (6,1)")
ck("the same cell on another map is a door",
   ledger.leg_words(h, "POKEMON_MANSION_1F|1,1", "16,14") == "door (16,14)")
ck("an edge is a walk", ledger.leg_words(h, "ROUTE_1|0,0", "north") == "walk north")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

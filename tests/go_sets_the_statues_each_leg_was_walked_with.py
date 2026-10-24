#!/usr/bin/env python3
"""`go` replays a leg with the switch statues set the way the run walked it,
pressing a statue on that floor a walk reaches when they stand the other way.

Run 62, 2026-10-24: the walked way to Mansion B1F climbs 2F's (6,1) stair
(walked UNPRESSED) and drops down 3F's hole (16,14) (walked PRESSED); go
replayed the legs but not the presses between them, stopped at whichever leg
disagreed, and the model flipped statues and re-ran go for hours (user: "it
SHOULD have the exact information it needs to get into the basement, its a
matter of putting it together and making sure its actually following
through the plan"). Probed on the leg 45 checkpoint with this executor: one
go from 1F|1,1 pressed 2F's statue, then 3F's, fell through (16,14) and
arrived at B1F|10,9.

Pinned (a fake bridge): a leg walked the other way presses the reachable
statue before the hop; a leg walked this way presses nothing; no statue in
reach presses nothing; a floor with no statues is untouched.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

F2 = "POKEMON_MANSION_2F|10,1"
F3 = "POKEMON_MANSION_3F|1,1"


class Stop(Exception):
    pass


def run(edge_sw, on, reachable=True, statues=True):
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {F2: {"6,1": {"to": F3, "n": 3, **({"switches": edge_sw} if edge_sw else {})}}}
    ex.map_holes = {}
    sent = []
    objs = ([{"name": "SWITCH_POKEMON_MANSION_2F_2_11", "kind": "fixture", "x": 2, "y": 11,
              "reachable": reachable}] if statues else [])
    obs = {"mode": "overworld", "player": {"x": 5, "y": 11},
           "map": {"id": "POKEMON_MANSION_2F", "region": "10,1", "warps": [],
                   "objects": objs, "switches_on": on}}

    class B:
        def obs(self):
            return obs
    ex.b = B()
    ex._where = lambda o: F2
    ex.log = lambda *a, **k: sent.append(("log", a[0] if a else "", k))

    def _send_safe(op, **kw):
        sent.append((op, kw))
        if op == "interact":
            obs["map"]["switches_on"] = not obs["map"]["switches_on"]
            return {}
        raise Stop()            # the hop itself: stop here, we only test the setting
    ex._send_safe = _send_safe
    try:
        ex._walk_route({"id": "t"}, [("6,1", F3)])
    except Stop:
        pass
    except Exception:
        pass                    # anything past the hop's first send is not under test
    return [s for s in sent if s[0] == "interact"], obs["map"]["switches_on"]


pr, now = run("UNPRESSED", True)
ck("a leg walked the other way presses the reachable statue first",
   pr and pr[0][1].get("name") == "SWITCH_POKEMON_MANSION_2F_2_11"
   and pr[0][1].get("answer") == "yes" and now is False, (pr, now))
ck("a leg walked this way presses nothing", run("UNPRESSED", False)[0] == [])
ck("no statue in reach presses nothing", run("UNPRESSED", True, reachable=False)[0] == [])
ck("a leg with no setting on record presses nothing", run(None, True)[0] == [])
ck("a floor with no statues is untouched", run("UNPRESSED", None, statues=False)[0] == [])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

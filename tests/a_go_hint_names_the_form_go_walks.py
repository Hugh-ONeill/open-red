"""The go hint names the op go actually walks, long:true when go would refuse.

Run 70, 2026-11-02, leg 45 cross_route_12: from Route 11 the walked chain to
Route 12 was 27 legs while the printed map drew it next door. Round 5's note
said {"op":"go","to":"ROUTE_12"} walks the whole way in ONE round; round 6
sent exactly that and go refused it as NOT WALKED, asking for "long": true.

Pinned: with a town map held and the walked chain far longer than the
printed one, the hint names {"op":"go","to":<region>,"long":true} and both
lengths; a short walked chain keeps the plain form. Synthetic.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

HERE = "ROUTE_11|9,0"


def fake(hops, printed, held=True):
    ex = object.__new__(E.Executor)
    ex.explored = {HERE: {}, "ROUTE_12|10,21": {}}
    ex.visits = {HERE: 3}
    ex.settle = lambda: {"map": {"id": "ROUTE_11"}}
    ex._where = lambda obs: HERE
    ex._route = lambda frm, to, avoid=None, ignore_blocked=False: (
        [None] * hops if to == "ROUTE_12|10,21" else None)
    ex._printed_legs = lambda a, b: printed
    ex._holding_town_map = lambda obs: held
    return ex


SAID = "I will manually follow the known route to reach Route 12."
OPS = [{"op": "use_warp", "x": 4, "y": 5}]
s = fake(27, 1)._go_would_have(OPS, SAID)
ck("a chain go would refuse is offered with long:true",
   '{"op":"go","to":"ROUTE_12|10,21","long":true}' in s, s)
ck("...with both lengths", "27 legs" in s and "1 leg(s)" in s, s)
ck("...and never the bare form go refuses", '{"op":"go","to":"ROUTE_12"}' not in s, s)
s = fake(4, 2)._go_would_have(OPS, SAID)
ck("a walked chain go accepts keeps the plain form",
   '{"op":"go","to":"ROUTE_12"}' in s and "long" not in s, s)
s = fake(27, 1, held=False)._go_would_have(OPS, SAID)
ck("no town map held: go does not refuse, plain form",
   '{"op":"go","to":"ROUTE_12"}' in s, s)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""A way the party can now open is listed however far it is, outside the
nearest-five and farthest-two caps.

Run of record 11 (2026-09-27): CUT was learned in Vermilion. The only bush
that led on was on ROUTE_9|0,8, walked onto before CUT and turned back by
it, eight legs away. The "ways never taken" list keeps the nearest five and
the two farthest; the far slots went to Route 25's bush and a Cerulean
pocket at nine legs, so Vermilion's bush and Route 25's were on the page
and Route 9's never was. The run circled Route 11 looking for Route 10.

Pinned: an openable place that fell between the caps is shown, under its
own words, with its distance; one already shown is not repeated; a place
no walk reaches is not offered; the list builder records which places are
openable from the same record the "knows CUT" words come from. Synthetic.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def row(reg, legs, routable=True, bush=False):
    what = ("bush (5,8) with ground past it no walk there reaches — a party "
            "Pokemon knows CUT" if bush else "north")
    return ((not routable, legs, -1, reg),
            f"{reg} ({what} — {legs} leg(s) away, first: walk west to X)")


NEAR = [row(f"NEAR_{c}|0,0", n) for c, n in zip("ABCDE", (1, 1, 2, 2, 2))]
R25 = row("ROUTE_25|10,2", 9, bush=True)
CER = row("CERULEAN_CITY|8,7", 9)
R9 = row("ROUTE_9|0,8", 8, bush=True)
MID = row("ROUTE_5|6,0", 7)

ns = types.SimpleNamespace(_openable_here={"ROUTE_25|10,2", "ROUTE_9|0,8"})
line = types.MethodType(E.Executor._elsewhere_line, ns)
out = line(NEAR + [R25, CER, R9, MID])

ck("an openable place between the caps is shown",
   "ROUTE_9|0,8" in out, out)
ck("...under its own words, after the farthest",
   "AND EVERY WAY THE PARTY CAN NOW OPEN, however far:" in out
   and out.index("AND THE FARTHEST") < out.index("ROUTE_9|0,8"), out)
ck("...with its distance, like every entry", "ROUTE_9|0,8 (bush (5,8)" in out
   and "8 leg(s) away" in out)
ck("one already in the far slots is not repeated", out.count("ROUTE_25|10,2") == 1)
ck("a place that is not openable still falls between the caps as before",
   "ROUTE_5|6,0" not in out)

ns2 = types.SimpleNamespace(_openable_here={"NOWHERE|0,0"})
UNR = row("NOWHERE|0,0", 99, routable=False, bush=True)
out2 = types.MethodType(E.Executor._elsewhere_line, ns2)(NEAR + [R25, CER, MID, UNR])
ck("a place no walk reaches is not offered", "NOWHERE" not in out2
   and "CAN NOW OPEN" not in out2, out2)

ns3 = types.SimpleNamespace()
out3 = types.MethodType(E.Executor._elsewhere_line, ns3)(NEAR + [R25, CER, R9, MID])
ck("with nothing openable the list is as it was", "CAN NOW OPEN" not in out3)

src = (ROOT / "planner/executor.py").read_text()
ck("the builder records what is openable from the bush record the CUT words use",
   "self._openable_here = set(bushes)" in src
   and src.index("self._openable_here = set(bushes)")
   < src.index('+ " — a party Pokemon knows CUT"'))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A pad ride kept out of the walked graph is still a way home for go.

Run 70, 2026-11-02, after Sabrina: the first ride into Saffron Gym's pad
maze, SAFFRON_GYM|7,13 -(11,15)-> 14,13, was filed with no way back because
the pad it left from opened past seen ground (pad_arrival_not_reversed,
opens_past True; the run 19 Silph 5F rule that keeps such a pad unridden).
The landing went to pad_lands, which the router never read, so `go` from
14,1 said "the chain breaks inside SAFFRON_GYM" and the model pad-hopped out
for ~10 rounds. Riding 14,13's (19,17) back sets the party on 11,15, which it
walked onto from 7,13.

Pinned on that ledger shape: with the landing recorded the router walks
14,1 -> 14,13 -> 7,13 -> SAFFRON_CITY; without it there is no route; an old
pad_lands row with no parts adds nothing; and note_transition records the
parts the ride joins.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

EX = {
    "SAFFRON_GYM|7,13": {"8,17": {"to": "SAFFRON_CITY|12,0", "n": 1},
                         "11,15": {"to": "SAFFRON_GYM|14,13", "n": 1}},
    "SAFFRON_GYM|14,13": {"15,15": {"to": "SAFFRON_GYM|14,1", "n": 1}},
    "SAFFRON_GYM|14,1": {"19,3": {"to": "SAFFRON_GYM|14,13", "n": 1}},
    "SAFFRON_CITY|12,0": {"34,3": {"to": "SAFFRON_GYM|7,13", "n": 1}},
}


def route(pad_lands):
    ex = E.Executor.__new__(E.Executor)
    ex.log = lambda *a, **k: None
    ex.explored = {k: dict(v) for k, v in EX.items()}
    ex.pad_lands = pad_lands
    r = None
    for _ in range(80):
        try:
            r = ex._route("SAFFRON_GYM|14,1", "SAFFRON_CITY|12,0")
            break
        except AttributeError as e:
            setattr(ex, str(e).split("'")[-2], {})
    return r


land = {"SAFFRON_GYM|19,17": {"map": "SAFFRON_GYM", "at": "11,15",
                              "frm": "SAFFRON_GYM|14,13", "to": "SAFFRON_GYM|7,13"}}
r = route(land)
ck("with the landing recorded, go has a way out",
   r and [str(t) for _k, t in r][-1] == "SAFFRON_CITY|12,0"
   and ("19,17", "SAFFRON_GYM|7,13") in [(str(k), str(t)) for k, t in r], r)
ck("...without it there is none (the run 70 page)", not route({}))
ck("...and an old row with no parts adds nothing",
   not route({"SAFFRON_GYM|19,17": {"map": "SAFFRON_GYM", "at": "11,15"}}))
src = (ROOT / "planner/executor.py").read_text()
ck("note_transition records the parts the ride joins",
   '"frm": dst, "to": src}' in src)
i = src.index("    def _edges_of(self, region: str) -> dict:")
ck("the landing is offered by the router's edge rule only",
   'getattr(self, "pad_lands", None)' in src[i:i + 4000])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

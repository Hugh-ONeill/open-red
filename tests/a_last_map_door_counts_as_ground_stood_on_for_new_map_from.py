#!/usr/bin/env python3
"""A LAST_MAP door leads back outside, to a map already stood on, when the
author asks whether {"new_map_from": X} can come true.

Run 63, 2026-10-24: next226 files LAST_MAP doors as LAST_MAP; read as a map
name, it was never one stood on, so the "every way out of X leads where you
have stood" refusal could never fire for a floor with a mouth (Mt Moon 1F's
entrance doors), and leg 9's descend_to_b1f (new_map_from MT_MOON_1F) went
through.

Pinned: a floor whose doors lead to stood maps and LAST_MAP is shut, said
plainly; one with a door to a map never stood on is not.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))


def shut(b1f_stood=True):
    d = {"map_doors": {"MT_MOON_1F": ["14,35", "15,35", "5,5"]},
         "door_dests": {"MT_MOON_1F": {"14,35": "LAST_MAP", "15,35": "LAST_MAP",
                                       "5,5": "MT_MOON_B1F"}},
         "explored": {"MT_MOON_1F|3,2": {"5,5": {"to": "MT_MOON_B1F|1,1"}}},
         "frontier_here": {"MT_MOON_1F|3,2": 0},
         "visits": {"MT_MOON_1F|3,2": 3, "ROUTE_4|10,0": 2,
                    **({"MT_MOON_B1F|1,1": 1} if b1f_stood else {})}}
    p = Path(tempfile.mkdtemp()) / "explored.json"
    p.write_text(json.dumps(d))
    return A._new_map_from_shut("MT_MOON_1F", str(p))


t = shut()
ck("doors to stood maps and LAST_MAP are shut", t and "the outdoor map you came in from" in t
   and "MT_MOON_B1F" in t, t)
ck("a door to a map never stood on is not", shut(b1f_stood=False) == "")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""Wild-ground rows tied on distance come most-recently-stood-on first.

From inside the league no walked route leads anywhere, every row tied, and
the alphabet put DIGLETTS_CAVE and MT_MOON (L6-L31) ahead of Victory Road for
a party in its fifties and sixties (run 19, 2026-09-30).

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


x = object.__new__(E.Executor)
x._wild_lv = {"DIGLETTS_CAVE": {"lo": 15, "hi": 31, "n": 35},
              "MT_MOON_1F": {"lo": 6, "hi": 11, "n": 30},
              "VICTORY_ROAD_1F": {"lo": 22, "hi": 43, "n": 300}}
x._map_last_t = {"DIGLETTS_CAVE": 100.0, "MT_MOON_1F": 50.0, "VICTORY_ROAD_1F": 900.0}
x.explored = {}
x._grind_exp = {}
x._offered = {}
x._route = lambda a, b: None
x._where = lambda o: "AGATHAS_ROOM|0,1"
x._wild_unknown_words = lambda *a, **k: ""
t = E.Executor._wild_elsewhere_fought_note(x, "AGATHAS_ROOM", {"map": {"id": "AGATHAS_ROOM"}})
ck("the most recently stood-on ground leads a tie",
   t.index("VICTORY_ROAD_1F") < t.index("DIGLETTS_CAVE") < t.index("MT_MOON_1F"), t[:300])
x._route = lambda a, b: [1] if b.startswith("MT_MOON") else None
x.explored = {"MT_MOON_1F|0,0": {}}
t = E.Executor._wild_elsewhere_fought_note(x, "AGATHAS_ROOM", {"map": {"id": "AGATHAS_ROOM"}})
ck("...but distance still comes first", t.index("MT_MOON_1F") < t.index("VICTORY_ROAD_1F"), t[:300])
src = (ROOT / "planner/executor.py").read_text()
ck("the stamp is set on every visit and saved",
   'self._map_last_t[str(region).split("|")[0]] = round(time.time(), 1)' in src
   and '"map_last_t": getattr(self, "_map_last_t", {})' in src)
ck("an old ledger is rebuilt from the journal", "_map_last_t_from_journal()" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

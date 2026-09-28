#!/usr/bin/env python3
"""The booklet says what each item is for (audit PT-41, 2026-09-28).

The author got a seven-line spelling aid; the booklet (pp.40-43) gives every
item's effect and each key item's job, in words every player had. The author
prompt carries the tables; the exploration page says the job of each held
thing whose purpose is not plain from its name. Nothing says where to find
anything.

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import booklet_items as B  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


eng = {l.strip() for l in (ROOT / "planner/engine_items.txt").read_text().splitlines() if l.strip()}
ck("every booklet item is an id this game defines",
   all(k in eng for k in B.ITEMS if k not in ("TM", "HM")), [k for k in B.ITEMS if k not in eng])
p = A.build_prompt("Retrieve the S.S. Ticket")
ck("the author reads the booklet's tables, the ticket spelled as the game spells it",
   "S_S_TICKET: A boarding ticket for the S.S. Anne." in p
   and "GOLD_TEETH: These belong to the warden of Safari Zone." in p)
x = object.__new__(E.Executor)
line = x._booklet_line({"bag": {"GOLD_TEETH": 1, "POTION": 3, "TM34": 1, "SILPH_SCOPE": 1}})
ck("the page says the job of a held key item",
   "GOLD_TEETH: These belong to the warden of Safari Zone." in line
   and "SILPH_SCOPE: This allows you to identify a ghostly Pokemon." in line, line)
ck("...and not of a Potion or a numbered machine", "POTION" not in line and "TM34" not in line)
ck("a bag with nothing of the kind says nothing", x._booklet_line({"bag": {"POTION": 2}}) == "")
ck("no line says where anything is found",
   not any(w in v.lower() for v in B.ITEMS.values() for w in (" route", " city", " town", " floor")))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A flag the game sets without a word is not history (audit 6a, 2026-09-28).

User's test: a flag whose change the game announces in text is on-screen
knowledge; one set silently is not. EVENT_ROUTE22_RIVAL_WANTS_BATTLE is set
by Oak's lab script at the Pokedex hand-over and names a fight on Route 22
that has not happened. Silent flags are journalled as flag_set_silently,
kept out of flag_sites and every page, and never cut a macro; predicates
and counts still read RAM.

Synthetic, plus source checks.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import executor as E  # noqa: E402
import silent_flags as S  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("the Route 22 arming flags are silent, the Pokedex is not",
   {"EVENT_ROUTE22_RIVAL_WANTS_BATTLE", "EVENT_1ST_ROUTE22_RIVAL_BATTLE"} <= S.SILENT
   and "EVENT_GOT_POKEDEX" not in S.SILENT)
ck("announced() keeps the order and drops only the silent",
   S.announced(["EVENT_GOT_POKEDEX", "EVENT_ROUTE22_RIVAL_WANTS_BATTLE", "EVENT_BEAT_BROCK"])
   == ["EVENT_GOT_POKEDEX", "EVENT_BEAT_BROCK"])

x = object.__new__(E.Executor)
logged = []
x.log = lambda kind, **kw: logged.append((kind, kw))
x._save_memory = lambda: None
x._where = lambda obs: "OAKS_LAB|4,1"
x.flag_sites = {}
x._known_flags = {"EVENT_GOT_STARTER"}
x.note_flag_site({"flags": ["EVENT_GOT_STARTER", "EVENT_GOT_POKEDEX",
                             "EVENT_ROUTE22_RIVAL_WANTS_BATTLE"]})
kinds = {(k, kw.get("flag")) for k, kw in logged}
ck("a silent flag is journalled under its own kind, not flag_fired",
   ("flag_set_silently", "EVENT_ROUTE22_RIVAL_WANTS_BATTLE") in kinds
   and ("flag_fired", "EVENT_GOT_POKEDEX") in kinds
   and ("flag_fired", "EVENT_ROUTE22_RIVAL_WANTS_BATTLE") not in kinds, kinds)
ck("...and kept out of flag_sites",
   "EVENT_ROUTE22_RIVAL_WANTS_BATTLE" not in x.flag_sites and "EVENT_GOT_POKEDEX" in x.flag_sites)

d = Path(tempfile.mkdtemp(prefix="silent_"))
(d / "run").mkdir()
(d / "run/executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"kind": "flag_fired", "flag": "EVENT_GOT_POKEDEX", "region": "OAKS_LAB|4,1"},
    {"kind": "flag_fired", "flag": "EVENT_ROUTE22_RIVAL_WANTS_BATTLE", "region": "OAKS_LAB|4,1"},
]) + "\n")
here = os.getcwd()
os.chdir(d)
try:
    ck("an older journal's silent flag is not volunteered as history either",
       A.fired_flags() == ["EVENT_GOT_POKEDEX"], A.fired_flags())
finally:
    os.chdir(here)

exs = (ROOT / "planner/executor.py").read_text()
ck("a silent flag never cuts a macro",
   '_f1 = set(_announced((obs or {}).get("flags") or [])) | _f0' in exs)
ck("the blocker since-words read announced flags only",
   'self._flags_now = sorted(str(f) for f in _announced(obs.get("flags") or []))' in exs)
aus = (ROOT / "planner/author.py").read_text()
ck("the missing rung's done list and the objective-words list are announced only",
   'done = sorted(_announced(cur.get("flags") or []))' in aus
   # next9 (2026-09-29) turned the comprehension into a ranked loop
   and 'for f in _announced(cur.get("flags") or []):' in aus)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

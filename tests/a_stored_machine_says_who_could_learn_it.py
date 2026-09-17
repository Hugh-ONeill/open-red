#!/usr/bin/env python3
"""A TM in the PC that somebody in the party could learn is on the page,
with the machine's own ABLE list and what the run said last time.

Run 27, 2026-09-17: TM_THUNDERBOLT, TM_BUBBLEBEAM and TM_REST were stored
under a party with no WATER type; a LAPRAS joined and the rest evolved, and
the stored TMs reached the page as bare names in the PC list (user: "it has
several stored in the computer which might be useful for the new/newly
evolved roster").

Pinned: the shim reads the machine screen for stored TMs too and marks them
stored; the teach question still considers only the bag; the page lists
stored TMs somebody is ABLE to learn and nobody knows, with the retrieve
op and the last answer about that TM. Synthetic.
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


shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim reads the machine screen for stored TMs too",
   'for k, v in pairs((G.save and G.save.pcItems) or {}) do\n    if type(k) == "string" and (tonumber(v) or 0) > 0 and not _mach_src[k] then' in shim
   and 'stored = (_src == "pc") or nil' in shim)

ex = object.__new__(E.Executor)
ex._tm_asked = {"TM_REST|GEODUDE,IVYSAUR,KADABRA,PIDGEOTTO":
                {"teach": None, "forget": None, "why": "Rest is too risky for these party members."}}
obs = {"bag": {"TM_PSYWAVE": 1},
       "pc_items": {"TM_THUNDERBOLT": 1, "TM_BUBBLEBEAM": 1, "TM_REST": 1, "TM_COUNTER": 1, "POTION": 3},
       "party": [{"species": "LAPRAS", "moves": [{"id": "WATER_GUN"}, {"id": "BODY_SLAM"}]},
                 {"species": "KADABRA", "moves": [{"id": "PSYCHIC_M"}, {"id": "REST"}]}],
       "machines": {
           "TM_THUNDERBOLT": {"move": "THUNDERBOLT", "able": ["LAPRAS", "KADABRA"], "not_able": [],
                              "type": "ELECTRIC", "power": 95, "max_pp": 15, "stored": True},
           "TM_BUBBLEBEAM": {"move": "BUBBLEBEAM", "able": ["LAPRAS"], "not_able": ["KADABRA"],
                             "type": "WATER", "power": 65, "max_pp": 20, "stored": True},
           "TM_REST": {"move": "REST", "able": ["LAPRAS", "KADABRA"], "not_able": [],
                       "type": "PSYCHIC_TYPE", "power": 0, "max_pp": 10, "stored": True},
           "TM_COUNTER": {"move": "COUNTER", "able": [], "not_able": ["LAPRAS", "KADABRA"],
                          "type": "FIGHTING", "power": 1, "max_pp": 20, "stored": True},
           "TM_PSYWAVE": {"move": "PSYWAVE", "able": ["LAPRAS", "KADABRA"], "not_able": []}}}
line = ex._stored_machines_line(obs)
ck("stored TMs somebody could learn are listed with the machine's ABLE list",
   "TM_THUNDERBOLT (THUNDERBOLT: ELECTRIC, 95 power, PP 15) [ABLE: LAPRAS, KADABRA]" in line
   and "TM_BUBBLEBEAM (BUBBLEBEAM: WATER, 65 power, PP 20) [ABLE: LAPRAS]" in line, line)
ck("...a stored TM nobody can learn is not", "TM_COUNTER" not in line)
ck("...nor one whose move somebody already knows", "TM_REST" not in line)
ck("...nor a bag TM, which the teach question already covers", "TM_PSYWAVE" not in line)
ck("...and the retrieve op is named", '{"op":"retrieve_item","item":X}' in line)
obs["party"][1]["moves"] = [{"id": "PSYCHIC_M"}]
line2 = ex._stored_machines_line(obs)
ck("a TM asked about under an earlier party carries that answer",
   "TM_REST (REST" in line2 and "asked once, when the able ones were GEODUDE,IVYSAUR,KADABRA,PIDGEOTTO, and declined: Rest is too risky" in line2, line2)
ck("no stored machines, no line", ex._stored_machines_line({"pc_items": {"POTION": 1}, "machines": {}, "party": []}) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("it rides the PC section of every page", "_rs_line = self._stored_machines_line(obs) + _rs_line" in src)
tn = src[src.index("    def _teachable_now(self, obs):"):]
tn = tn[:tn.index("\n    def ", 10)]
ck("the teach question still reads only the bag", "for item in sorted(bag):" in tn)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""A part on a floor with switch statues, stood in under one setting only,
keeps its unseen count; stood in both ways, it is done as before.

Run 62, 2026-10-24: B1F's corner, stood in only with the statues PRESSED,
read as looked out from (frontier 0) while the Secret Key's ball sat behind
its statue walls; with next218/223 a lever flip no longer reopens such a part
at all (user: "explore should count ground hidden behind a lever as
unfinished but only if its never been there before").

Pinned: one setting stood -> "changed" with the count; both -> "done"; a
floor with no statues -> "done"; the ledger backfill reads the settings off
walked edges leaving and arriving; a stand records the setting.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R = "POKEMON_MANSION_B1F|10,9"
WM = E.Executor._world_mark


def verdict(stood):
    ex = object.__new__(E.Executor)
    ex.region_seen = {R: 11}
    ex.frontier_here = {R: 0}
    ex.visits = {R: 2}
    ex._water_unseen = lambda r: 0
    ex._toggled_flags = []
    o = {"badges": ["A"], "flags": ["X"], "bag": {}}
    ex._region_mark = {R: WM(o)}
    ex._mark_now = WM(o)
    ex._region_mark_nt = {R: WM(o)}
    ex._mark_now_nt = WM(o)
    ex._stood_switches = {R: set(stood)} if stood is not None else {}
    return ex._unseen_there(R)


ck("stood in one setting only keeps the count", verdict(["PRESSED"]) == (11, "changed"))
ck("stood in both ways is done", verdict(["PRESSED", "UNPRESSED"]) == (0, "done"))
ck("a floor with no statues is done", verdict(None) == (0, "done"))

ex = {"POKEMON_MANSION_B1F|10,9": {"23,22": {"to": "POKEMON_MANSION_1F|12,14",
                                             "switches": "PRESSED"}},
      "POKEMON_MANSION_1F|12,14": {"21,23": {"to": "POKEMON_MANSION_B1F|10,9",
                                             "switches": "PRESSED"}},
      "POKEMON_MANSION_2F|10,1": {"6,1": {"to": "POKEMON_MANSION_3F|1,1", "switches": "UNPRESSED"},
                                  "5,10": {"to": "POKEMON_MANSION_1F|1,1", "switches": "PRESSED"}},
      "VIRIDIAN_CITY|17,0": {"south": {"to": "ROUTE_1|0,0"}}}
st = E.stood_switches_from_edges(ex)
ck("the backfill reads leaving and arriving edges",
   st.get("POKEMON_MANSION_B1F|10,9") == {"PRESSED"}
   and st.get("POKEMON_MANSION_2F|10,1") == {"PRESSED", "UNPRESSED"}
   and st.get("POKEMON_MANSION_1F|1,1") == {"PRESSED"}, st)
ck("...and a floor with no statues gets nothing", "VIRIDIAN_CITY|17,0" not in st)

src = (ROOT / "planner" / "executor.py").read_text()
ck("a stand records the setting",
   'self._stood_switches.setdefault(_hr, set()).add(' in src
   and '"PRESSED" if _sw else "UNPRESSED")' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

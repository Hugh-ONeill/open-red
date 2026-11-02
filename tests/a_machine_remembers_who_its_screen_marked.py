"""A machine remembers, by species, who its screen marked across past parties.

Run 70, 2026-11-02, leg 45: HM_SURF rode through parties holding DIGLETT,
GASTLY, CUBONE, EEVEE and the core six, each read NOT ABLE off the machine's
own screen, but the page said only "NOBODY IN THIS PARTY CAN TAKE: HM_SURF"
for the party of the moment, and the model went back to the PC "to check if
any stored Pokemon can learn SURF" round after round (Fuchsia, then Viridian).

Pinned: each observation's ABLE / NOT ABLE is kept per species, a later read
of the same species wins, and the bag line and the NOBODY CAN TAKE line name
the species NOT in the party now; a species never carried is never named;
the record is saved with the ledger.
"""
import sys
from pathlib import Path
sys.path.insert(0, "planner")
import executor as E

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex._machine_seen = {}


def obs(party, able):
    return {"party": [{"species": s} for s in party],
            "machines": {"HM_SURF": {"move": "SURF", "able": able}}}


core = ["VENUSAUR", "GRAVELER", "PIKACHU", "PIDGEOT", "BEEDRILL"]
ex._note_machine_seen(obs(core + ["KADABRA"], []))
ex._note_machine_seen(obs(core + ["DIGLETT"], []))
ex._note_machine_seen(obs(core + ["GASTLY"], []))
now = obs(core + ["EEVEE"], [])
ex._note_machine_seen(now)
note = ex._able_note("HM_SURF", now)
ck("the bag line names the species marked NOT ABLE in earlier parties",
   "NOT ABLE: KADABRA, DIGLETT, GASTLY" in note, note)
ck("...not the ones in the party now", "VENUSAUR" not in note.split("earlier parties")[1], note)
ck("...and never a species the run never carried", "CUBONE" not in note and "LAPRAS" not in note, note)
ex._note_machine_seen(obs(core + ["EEVEE"], []))
ex._note_machine_seen(obs(core + ["VAPOREON"], ["VAPOREON"]))
n2 = ex._machine_seen_note("HM_SURF", obs(core + ["KADABRA"], []))
ck("a species marked ABLE before is named ABLE", "ABLE: VAPOREON" in n2, n2)
ex._note_machine_seen(obs(core + ["KADABRA"], ["KADABRA"]))
ck("a later read of the same species wins",
   "KADABRA" in ex._machine_seen["HM_SURF"]["able"]
   and "KADABRA" not in ex._machine_seen["HM_SURF"]["not_able"])
src = Path("planner/executor.py").read_text()
ck("the record is saved and loaded with the ledger",
   '"machine_seen": getattr(self, "_machine_seen", {})' in src
   and 'self._machine_seen = data.get("machine_seen") or {}' in src)
ck("the NOBODY CAN TAKE line carries it",
   "+ self._machine_seen_note(_it, start))" in src
   and "self._note_machine_seen(start)" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

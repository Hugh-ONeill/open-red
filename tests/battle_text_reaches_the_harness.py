#!/usr/bin/env python3
"""The battle's own lines reach the observation, and the harness reads them.

The battle prints through BattleState:startMessage, never through the
dialog pages the shim read, so no battle line reached any observation: the
self-KO reader never fired in any run, and run of record 4 threw ten balls
at the Pokemon Tower's MAROWAK, each answered "This POKeMON can't be
caught!" unseen (user, 2026-09-26: "battle text first").

Checked in the game on 2026-09-26 (isolated saves, contract.start_game):
a GHOST on Tower 3F gave "SAGE used POKé BALL! / It dodged the thrown BALL!
/ This POKéMON can't be caught!"; a RATTATA on Route 1 gave "ROCKY used
SELFDESTRUCT! / ROCKY fainted! / Enemy RATTATA fainted!" and the self-KO
reader returned True; last_text stayed the overworld's.

Pinned: the shim wraps startMessage once, keeps the current battle's last
lines apart from last_text and starts again on a new battle; the observation
carries battle_text and its counter; the self-KO reader reads battle_text
first; a catch told "can't be caught" turns the battle into a fight.
Synthetic, the game side source-anchored."""
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
hb = shim[shim.index("local function hook_battle_text()"):]
hb = hb[:hb.index("\nend\n") + 5]
ck("the shim wraps the battle's startMessage, once",
   'pcall(require, "src.battle.BattleState")' in hb
   and "BS.startMessage = function(self, item)" in hb
   and "return orig(self, item)" in hb and "battle_hooked = true" in hb)
ck("...keeps the last lines of THIS battle, apart from last_text",
   "if self ~= battle_owner then" in hb and "battle_lines = {}" in hb
   and "table.remove(battle_lines, 1)" in hb and "last_text" not in hb)
ck("the observation carries them and a counter",
   'o.battle_text = table.concat(battle_lines, " / ")' in shim
   and "o.battle_text_seq = battle_seq" in shim)

E.SELF_KO.clear()
import tempfile
E.SELF_KO_PATH = Path(tempfile.mkdtemp()) / "self_ko.json"
seen = {"mode": "ui", "last_text": "Welcome to our POKEMON CENTER!",
        "battle_text": ("Wild RATTATA appeared! / Go! ROCKY! / ROCKY used "
                        "SELFDESTRUCT! / ROCKY fainted! / Enemy RATTATA fainted!")}
ck("the self-KO reader reads the battle's lines (the game's own, 2026-09-26)",
   E._journal_self_ko({"me": {"hp": 70}}, seen, "SELFDESTRUCT") is True, E.SELF_KO)
src = (ROOT / "planner/executor.py").read_text()
ck("a catch the game answers \"can't be caught\" becomes a fight",
   "\"can't be caught\" in str((obs or {}).get(\"battle_text\") or \"\")" in src
   and 'ctx["intent"] = "fight"' in src and 'log("uncatchable"' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

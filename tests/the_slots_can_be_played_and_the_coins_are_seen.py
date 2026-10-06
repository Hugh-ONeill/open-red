#!/usr/bin/env python3
"""A slot machine can be played, and the COIN CASE's coins are seen.

2026-10-06, run 37 holding the COIN CASE with 60 coins nothing showed
(user: "for consistencies sake build a slot op ... also the coin stuff
since it did pick up the case"). Proven in-game on a copy of the live
save: 3 spins at 1 coin on SLOT_MACHINE_17 ("Not this time!" x3, coins
60 -> 57), and 20 at 3 coins on SLOT_MACHINE_7 (BAR lined up on spin 15,
coins 60 -> 100), the party back in the overworld both times.

Pinned: the observation carries coins only with the COIN CASE; the start
line says them; the op is in the shim and in the vocabulary, refuses a
bad bet and an unknown machine, answers YES, stops wheels with A, and
answers "One more go?"; shim.lua still compiles under the local cap."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def line(state):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "run").mkdir()
        (Path(d) / "run/last_state.json").write_text(json.dumps(state))
        return subprocess.run([sys.executable, str(ROOT / "planner/state_text.py")],
                              cwd=d, capture_output=True, text=True).stdout


base = {"map": "CELADON_CITY", "region": "1,1",
        "party": [{"species": "VENUSAUR", "level": 37, "hp": 1, "max_hp": 1}],
        "badges": [], "bag": {"COIN_CASE": 1}, "money": 10}
w = line(dict(base, coins=60))
ck("the start line says the coins", "60 coin(s) in the COIN CASE" in w, w)
ck("...and nothing without them", "COIN CASE" not in line(base).split("bag")[0])

shim = (ROOT / "harness/shim.lua").read_text()
ck("coins are observed only with the case",
   "if G.save and G.save.inventory and G.save.inventory.COIN_CASE then\n"
   "    o.coins = G.save.coins or 0" in shim)
ck("the op exists", "function OPS.slots(G, c)" in shim)
ck("...refuses a bad bet", 'return false, "bet is 1, 2 or 3 coins a spin"' in shim)
ck("...names the machines when it does not know one",
   "named SLOT_MACHINE_1, SLOT_MACHINE_2, ..." in shim)
blk = shim[shim.index("function OPS.slots(G, c)"):shim.index("function OPS.toss(G, c)")]
ck("...says YES to the machine, stops wheels with A, answers One more go",
   'ui_cursor_to(G, "index", 1)' in blk
   and 'if sm.stage == "spin" then U.tap(G, "a") end' in blk
   and 'U.tap(G, i < spins and "a" or "b")' in blk)
ck("...and walks the way the other ops do", "thaw = c.thaw, blind = c.blind" in blk)
ex = (ROOT / "planner/executor.py").read_text()
ck("the op is in the vocabulary", '{"op":"slots","name":"SLOT_MACHINE_1","bet":1,"spins":N}' in ex)
lj = shutil.which("luajit")
if lj:
    r = subprocess.run([lj, "-b", str(ROOT / "harness/shim.lua"), "/dev/null"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       text=True, errors="replace")
    ck("shim.lua still compiles under LuaJIT's local cap", r.returncode == 0, r.stderr[-300:])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

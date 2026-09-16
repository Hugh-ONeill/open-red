#!/usr/bin/env python3
"""A save is the engine's own write, and a round that fires a flag is saved.

Run 27 logged 46 failed subgoal saves in a day — the harness drove the Start
menu's SAVE, and its confirm, "Now saving..." and "SAGE saved the game!"
boxes kept being left up — and the one save that mattered, after Lt.
Surge's locks were opened inside a long step, never landed, so the next
attempt booted from before the first lock (user, 2026-09-16: "we have to fix
saving because its already like a burst of three saves every time"; "it
reset the locks because it didnt save being stuck in the menus").

Pinned: save_game calls game:writeSave (the call the menu makes on "Now
saving...") and keeps the menu path only as a fallback; a fresh event flag
marks the world unsaved; an escalation round that ends with unsaved flags,
in the overworld and not walking back to a faint, saves and clears the mark.
Verified once against a live isolated game (0.05s a save, file written, no
box left up); these are source and unit checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


SH = (ROOT / "harness/shim.lua").read_text()
sv = SH[SH.index("function OPS.save_game(G)"):]
ck("save_game makes the engine's own write",
   "if G.writeSave then" in sv and "pcall(G.writeSave, G)" in sv
   and sv.index("pcall(G.writeSave, G)") < sv.index('U.tap(G, "start")'))
SM = (Path.home() / "Developer/gen1recomp/src/ui/StartMenu.lua").read_text()
ck("...which is the call the Start menu's SAVE makes", "game:writeSave()" in SM)

ex = object.__new__(E.Executor)
ex._known_flags = {"EVENT_A"}
ex.flag_sites = {}
ex.logged = []
ex.log = lambda k, **kw: ex.logged.append((k, kw))
ex._save_memory = lambda: None
ex._where = lambda obs: "VERMILION_GYM|4,5"
note = getattr(ex, "note_flag_site", None)
if note:
    note({"flags": ["EVENT_A", "EVENT_1ST_LOCK_OPENED"],
          "map": {"id": "VERMILION_GYM", "region": "4,5"}})
    ck("a fresh flag marks the world unsaved",
       getattr(ex, "_flags_unsaved", None) == ["EVENT_1ST_LOCK_OPENED"])
else:
    ck("note_flag_site exists", False)

SRC = (ROOT / "planner/executor.py").read_text()
blk = SRC[SRC.index("A ROUND THAT MOVED THE WORLD IS SAVED WHEN IT ENDS."):]
blk = blk[:blk.index('self.log("escalate_end", subgoal=sg["id"], success=False)')]
ck("a round ending with unsaved flags saves, in the overworld, not mid walk-back",
   "_fu and self.save_each and not self._faint_at" in blk
   and '(cur or {}).get("mode") == "overworld"' in blk
   and 'self._send_safe("save_game")' in blk)
ck("...logs it and clears the mark only when the save landed",
   'self.log("round_save"' in blk and 'if _rs.get("ok"):' in blk
   and "self._flags_unsaved = []" in blk)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

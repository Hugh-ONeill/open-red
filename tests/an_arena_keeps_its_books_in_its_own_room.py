#!/usr/bin/env python3
"""An arena keeps its journal and its memory in its own room.

Each arena already ran its GAME in its own bridge directory. Its books
did not follow: the arena runner set RED_BRIDGE_DIR after it had imported
the executor, so the journal, the exploration memory, the checkpoint root
and the footprint path were still the live run's. A day of arena rooms
beside a live chain (2026-09-15, 08:01 to 17:10) left run 17's journal
99.5% arena rows and put the league and four gyms the run had never
entered into its explored.json, which the next leg launch read back as
its own. The runner also deleted the live run's obs.json at every boot.

No game here: the executor's rebinding is checked directly, and the
runner's boot order is checked in its source.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402
import policy_author as PA    # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


live = E.RUN
tmp = Path(tempfile.mkdtemp(prefix="arena_books_"))

# ---- the executor can be pointed at a room --------------------------------
got = E.bind_run(tmp)
ck("bind_run returns the room it bound", got == tmp)
ck("the run directory moved", E.RUN == tmp)
ck("the checkpoint root moved with it", E.CHECKPOINTS == tmp / "saves")
ck("the exploration memory moved with it",
   E.Executor.MEMORY == tmp / "explored.json")
SRC = (ROOT / "planner/executor.py").read_text()
ck("the footprint is read from the run directory, not a literal run/",
   'or "run/seen.json"' not in SRC and 'RUN / "seen.json"' in SRC)
ck("the journal is opened from RUN at construction, so it follows too",
   'self.logf = open(RUN / "executor_log.jsonl", "a")' in SRC)

# ---- the runner binds its books before the game or the executor exists ----
PS = (ROOT / "planner/policy_author.py").read_text()
boot = PS[PS.index("    def boot(self):"):PS.index("    def ", PS.index("    def boot(self):") + 10)]
ck("boot binds the books to the arena's room",
   "_bind_books(self.run_dir)" in boot)
ck("...after the room is named and before the game starts",
   boot.index("self.run_dir = REPO") < boot.index("_bind_books(self.run_dir)")
   < boot.index("start_game(self.run_dir"))
ck("...and before the executor is built",
   boot.index("_bind_books(self.run_dir)") < boot.index("ex_mod.Executor("))
ck("a from-save arena never touches the live run's obs.json",
   boot.index('(RUN / "obs.json").unlink()') > boot.index("        else:"))

# ---- the books start empty: a clean room has nothing to read back --------
for f in ("executor_log.jsonl", "explored.json", "explored.json.prev"):
    (tmp / f).write_text("stale\n")
(tmp / "seen.json").write_text("return {}\n")
PA._bind_books(tmp)
ck("binding the books clears a stale journal and memory",
   not (tmp / "executor_log.jsonl").exists()
   and not (tmp / "explored.json").exists()
   and not (tmp / "explored.json.prev").exists())
ck("...but leaves the shim's footprint alone", (tmp / "seen.json").exists())
ck("the runner's own journal handle follows the room",
   PA.LOG == tmp / "executor_log.jsonl")
ck("the executor is bound to the same room", E.RUN == tmp
   and E.Executor.MEMORY == tmp / "explored.json")

# ---- and the live run's files were never named --------------------------
ck("nothing above was the live run's directory", tmp != live)

# ---- the arena table is two paths through the same rooms -----------------
ck("every gym has a real and an ideal room",
   all(f"{r}_{p}" in PA.ARENAS for r in PA.GYM_ROOMS for p in PA.PATHS))
ck("room_of strips a path and nothing else",
   PA.room_of("cinnabar_ideal") == "cinnabar"
   and PA.room_of("e4_real") == "e4" and PA.room_of("brock") == "brock"
   and PA.room_of("erika_found") == "erika_found")

E.bind_run(live)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

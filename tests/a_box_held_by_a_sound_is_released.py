#!/usr/bin/env python3
"""A box held open by a sound that does not end is released, and a macro
the interface stopped is not refused as a repeat.

Run 27, 2026-09-18, Seafoam: "ROCKY used STRENGTH." is an auto-advancing
box that waits on ROCKY's cry (TextBox opts.auto); A and B do nothing to
it, and with the cry never reporting finished it never closed. The next
explore failed "not in overworld (a box was up and would not close)", and
the six identical explores after it were refused as repeats until the step
died with its budget untouched (user: "did the escalations run out on that
last bit? it was exploring and seeing new ground though?").

Pinned: the back-out stops a still-playing sound that holds an auto box
after a stall, and the field-move text loop does the same; the helper runs
in Lua against a fake source; the repeat gate lets through a macro whose
last failure was the interface. Synthetic.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("local function release_held_sound(G, t)")
j = shim.index("\nend\n", i) + 5
helper = shim[i:j]
prog = helper + """
local stopped = 0
local function src(playing)
  return { isPlaying = function(self) return playing end,
           stop = function(self) stopped = stopped + 1 end }
end
print(release_held_sound(nil, { auto = {}, autoSrc = src(true) }), stopped)
print(release_held_sound(nil, { auto = {}, autoSrc = src(false) }), stopped)
print(release_held_sound(nil, { pages = {} }), stopped)
print(release_held_sound(nil, nil), stopped)
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
r = subprocess.run(["lua", f.name], capture_output=True, text=True, timeout=20)
lines = r.stdout.split("\n")
ck("the helper runs", r.returncode == 0, r.stderr[:200])
if r.returncode == 0:
    ck("a still-playing sound holding an auto box is stopped", lines[0] == "true\t1", lines[0])
    ck("...a finished one is left alone", lines[1] == "false\t1", lines[1])
    ck("...a plain box and no box are left alone", lines[2] == "false\t1" and lines[3] == "false\t1", lines[2:4])
ck("the back-out releases it after a stall",
   "if stall > 10 and release_held_sound(G, t) then stall = 0 end" in shim
   and shim.index("local function release_held_sound") < shim.index("ui_back_out = function(G)"))
ck("the field-move text loop releases it too",
   "if _fi > 60 and _fi % 30 == 0 then release_held_sound(G, t) end" in shim)
src = (ROOT / "planner/executor.py").read_text()
ck("the repeat gate lets through a macro the interface stopped",
   'for w in ("not in overworld",\n                                       "would not close")):' in src
   and '"repeat_allowed_ui_blocked"' in src
   and src.index('"repeat_allowed_ui_blocked"') < src.index('self.log("escalate_repeat_refused"'))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

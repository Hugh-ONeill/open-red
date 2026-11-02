#!/usr/bin/env python3
"""A TM nobody in the party can learn is not offered for use by the toss refusal.

Run 70, Safari Zone (2026-11-02), search_safari_zone_for_teeth r7: toss
TM_BUBBLEBEAM was refused with "TM_BUBBLEBEAM is something this game will
let you USE on a party member ... using it spends it and keeps whatever it
is worth ... teaching it frees this bag slot exactly as tossing it would",
beside "the teach screen would say NOT COMPATIBLE for every one of them".
Both claims are false for that party; the run spent a round, then tossed it
with confirm.

Runs the refusal block under LuaJIT on a synthetic all-incompatible party
and on one with a compatible member (unchanged).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "harness/shim.lua").read_text()
toss = src[src.index("function OPS.toss(G, c)"):]
toss = toss[:toss.index("\nfunction OPS.", 10)]
a = toss.index("    local why = c.item")
b = toss.index("    -- the same count the ITEM screen shows")
block = toss[a:b]


def run(party):
    lua = """
local c = {item = "TM_BUBBLEBEAM"}
local G = {
  data = {items = {TM_BUBBLEBEAM = {machine = {move = "BUBBLEBEAM"}}},
          pokemon = {KADABRA = {tmhm = {"PSYWAVE"}}, LAPRAS = {tmhm = {"BUBBLEBEAM"}},
                     GRAVELER = {tmhm = {"EARTHQUAKE"}}}},
  save = {party = %s},
}
""" % party + block + "\nprint('WHY|' .. why)\n"
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(lua)
    out = subprocess.run(["luajit", f.name], capture_output=True, text=True)
    return next((l[4:] for l in out.stdout.splitlines() if l.startswith("WHY|")),
                out.stdout + out.stderr)


if not shutil.which("luajit"):
    ck("luajit is on the path", False)
else:
    w = run('{{species="KADABRA", moves={{id="PSYBEAM"}}}, {species="GRAVELER", moves={}}}')
    ck("nobody compatible: no claim the game lets you USE it", "will let you USE" not in w, w)
    ck("...nor that teaching it frees the slot", "teaching it frees" not in w, w)
    ck("...and the teach screen's verdict is said", "NOT COMPATIBLE for every one of them" in w, w)
    w = run('{{species="LAPRAS", moves={{id="SURF"}}}, {species="GRAVELER", moves={}}}')
    ck("a compatible member: the use line stands", "will let you USE" in w
       and "compatible for LAPRAS (slot 1)" in w, w)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""The TM toss refusal says, for each party member that can take the TM, what
the teach screen would ask: a full moveset forgets one of its four (named), a
shorter one learns it without forgetting, and one that has it already says so.

The refusal said "compatible for VENUSAUR (slot 2)" and "using it ... keeps
whatever it is worth", which read as a free slot: run 41 taught RAGE over
RAZOR_LEAF and TOXIC over its powder to clear the bag, and VENUSAUR ended on
CUT / TOXIC / LEECH_SEED / RAGE with no Grass attack (2026-10-10). Names
only: no ratings, no record of a move's use (the TM-question rule).

Runs the shim's own per-member loop under LuaJIT on a synthetic party.
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
a = toss.index("      local can, cannot = {}, {}")
b = toss.index('      why = why .. " It teaches "')
loop = toss[a:b]
ck("the loop names the moves a full moveset would forget",
   "teaching it FORGETS one of those four" in loop)
ck("...compatible entries are joined so their own lists stay readable",
   'table.concat(can, "; ")' in toss)
ck("...and nothing in it rates a move or reads a run record",
   not any(w in loop.lower() for w in ("power", "used ", "times", "record")))

lua = """
local _mv = "RAGE"
local G = {
  data = {pokemon = {
    VENUSAUR = {tmhm = {"RAGE", "TOXIC"}},
    KADABRA  = {tmhm = {"RAGE"}},
    LAPRAS   = {tmhm = {"RAGE"}},
    GRAVELER = {tmhm = {"TOXIC"}},
  }},
  save = {party = {
    {species = "VENUSAUR", moves = {{id="CUT"},{id="TOXIC"},{id="LEECH_SEED"},{id="RAZOR_LEAF"}}},
    {species = "KADABRA",  moves = {{id="PSYBEAM"},{id="DISABLE"}}},
    {species = "LAPRAS",   moves = {"SURF", "RAGE", "BODY_SLAM"}},
    {species = "GRAVELER", moves = {{id="EARTHQUAKE"}}},
  }},
}
""" + loop + """
print("CAN|" .. table.concat(can, "; "))
print("CANNOT|" .. table.concat(cannot, ", "))
"""
if not shutil.which("luajit"):
    ck("luajit is on the path", False)
else:
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(lua)
    out = subprocess.run(["luajit", f.name], capture_output=True, text=True)
    txt = out.stdout + out.stderr
    can = next((l[4:] for l in txt.splitlines() if l.startswith("CAN|")), "")
    cannot = next((l[7:] for l in txt.splitlines() if l.startswith("CANNOT|")), "")
    ck("the loop runs", out.returncode == 0, txt[-300:])
    ck("a full moveset names its four and says one is forgotten",
       "VENUSAUR (slot 1) — knows CUT, TOXIC, LEECH_SEED, RAZOR_LEAF: teaching it "
       "FORGETS one of those four" in can, can)
    ck("a short moveset learns it without forgetting",
       "KADABRA (slot 2) — knows PSYBEAM, DISABLE: learns it without forgetting any" in can, can)
    ck("a member that already knows it says so (moves as plain strings too)",
       "LAPRAS (slot 3) — already knows RAGE" in can, can)
    ck("an incompatible member stays a bare name",
       cannot == "GRAVELER (slot 4)", cannot)
    print("  example:", "compatible for " + can)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("  ok   " if ok else "  FAIL ") + n + ("" if ok or not d else "  -- " + d))
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

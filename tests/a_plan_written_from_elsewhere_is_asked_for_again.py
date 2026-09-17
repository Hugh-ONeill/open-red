#!/usr/bin/env python3
"""A plan picked up from somewhere other than where it was written is
asked for again from here.

Run 27, 2026-09-17: "Obtain the FRESH WATER" v1 was a rewrite written in
Rock Tunnel (exit_rock_tunnel -> ROUTE_10 -> CELADON_CITY -> ...). After
the bag-space leg it was found again by its objective, from the Celadon
Pokemon Center, and the run walked thirteen legs back through Lavender
and the tunnel to satisfy its first step, then thirteen legs forward.

Pinned: the author stamps the map a plan was written from; a plan whose
stamp differs from where the run stands is reported, one with no stamp or
the same map is not; the chain reads that before keeping an existing plan
and authors the next version instead, keeping the old file. Synthetic.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp())


def run(plan: dict, here: str):
    f = tmp / "p.json"
    f.write_text(json.dumps(plan))
    r = subprocess.run([sys.executable, str(ROOT / "planner/plan_written_elsewhere.py"),
                        str(f), here], capture_output=True, text=True, cwd=ROOT)
    return r.returncode, r.stdout.strip()


rc, out = run({"goal": "Obtain the FRESH WATER", "written_from": "ROCK_TUNNEL_B1F",
               "subgoals": [{"id": "a"}]}, "CELADON_POKECENTER")
ck("a plan written elsewhere is reported, naming both places",
   rc == 0 and out == "ROCK_TUNNEL_B1F (the run stands on CELADON_POKECENTER)", (rc, out))
ck("the same place makes no claim",
   run({"written_from": "CELADON_POKECENTER", "subgoals": []}, "CELADON_POKECENTER")[0] == 3)
ck("a plan with no record makes no claim",
   run({"goal": "x", "subgoals": []}, "CELADON_POKECENTER")[0] == 3)
ck("an unknown present place makes no claim",
   run({"written_from": "ROCK_TUNNEL_B1F", "subgoals": []}, "")[0] == 3)

src = (ROOT / "planner/author.py").read_text()
ck("the author stamps where a plan was written from",
   'plan["written_from"] = _wf' in src and "_wf = _map_now()" in src)
sh = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain asks before keeping an existing plan",
   'plan_written_elsewhere.py "$plan"' in sh
   and sh.index('plan_written_elsewhere.py "$plan"') < sh.index('keeping existing $plan'))
ck("...and authors the next version, keeping the old file",
   'plan="${_pb}.v$((_pv+1)).json"' in sh and "asking for it again from here" in sh)
ck("the chain script parses",
   subprocess.run(["bash", "-n", str(ROOT / "fresh_discovery.sh")]).returncode == 0)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

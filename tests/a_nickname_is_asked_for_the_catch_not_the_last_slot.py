#!/usr/bin/env python3
"""A nickname is asked for the Pokemon the game named, not the last party slot.

With a full party every catch goes to the box, and the prompt took the newest
PARTY member: eleven Goldeen and Poliwag were named EMBER and CINDER after
the Growlithe in slot 6, and the Growlithe BOULDER after the Graveler (run
19, 2026-09-29). The shim now hooks the game's "give a nickname to X?" and
publishes X with the naming screen.

Synthetic, plus source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


party = [{"species": "GRAVELER", "level": 54}, {"species": "GROWLITHE", "level": 15}]
obs = {"party": party, "naming": {"title": "NICKNAME?", "max": 10,
                                  "for_species": "GOLDEEN", "for_level": 10}}
p = E._naming_prompt(obs)
ck("the prompt names the catch", "for the GOLDEEN L10 you just got" in p, p)
ck("...not the last party slot", "GROWLITHE L15 that just joined" not in p, p)
obs["naming"].pop("for_species")
obs["naming"].pop("for_level")
p = E._naming_prompt(obs)
ck("with no species published it falls back as before",
   "for the GROWLITHE L15 that just joined you" in p, p)

shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim hooks the game's nickname question",
   "BS.askNicknameUI = function(self, mon, displayName, ...)" in shim)
ck("...and publishes it only while fresh",
   "for_species = nf and nf.species or nil" in shim and "<= 120" in shim)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

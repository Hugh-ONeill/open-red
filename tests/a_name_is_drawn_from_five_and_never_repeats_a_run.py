#!/usr/bin/env python3
"""Every naming screen draws one of five names the model offers, framed per
screen, and turns away names earlier runs had.

Sampled 2026-10-01: temperature changed nothing (SPROUT 8/8 at 1.3, the
rival JERK 6/8), and runs read SPROUT, JERK, SAGE, KAI over and over (user:
"id be fine with a bulba named carl its just like naming a pet ... just like
its named rival jerk every time ... the only one ive disliked is kai").
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
td = Path(tempfile.mkdtemp())
os.environ.setdefault("RED_BRIDGE_DIR", str(td))
os.environ["RED_NAMES_USED"] = str(td / "used")
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sent = []


def fake(names):
    def chat(msgs, model, temp=None):
        sent.append(msgs[0]["content"])
        return json.dumps({"names": names})
    return chat


E.NAMES_USED = td / "used"
CLING = "nickname\tSPROUT\n" * 3 + "rival\tJERK\n" * 3 + "nickname\tTRIPLE-T\n"
E.NAMES_USED.write_text(CLING)
starter = {"naming": {"title": "NICKNAME?", "max": 10, "for_species": "BULBASAUR"},
           "party": [{"species": "BULBASAUR", "level": 5}]}
E.brock_probe.chat = fake(["Sprout", "Bulby", "Carl", "Mochi", "BULBASAUR"])
got = set()
for _ in range(30):
    E.NAMES_USED.write_text(CLING)
    got.add(E.ask_name(starter, "m"))
ck("the name is drawn from the five offered", got <= {"BULBY", "CARL", "MOCHI"} and len(got) >= 2, got)
ck("...never a name an earlier run had, nor the species", "SPROUT" not in got and "BULBASAUR" not in got)
ck("...and each name drawn is written down for the next run",
   E.NAMES_USED.read_text().count("nickname\t") > 4)
E.NAMES_USED.write_text(CLING)
E.brock_probe.chat = fake(["Triple-T"])
ck("a one-off chosen before stays open (only a name chosen 3+ times is turned away)",
   E.ask_name(starter, "m") == "TRIPLE-T")
E.NAMES_USED.write_text("nickname\tCARL\n")
held = dict(starter, party=[{"species": "PIDGEY", "nickname": "CARL"}, {"species": "BULBASAUR"}])
E.brock_probe.chat = fake(["Carl", "Dot"])
ck("a name worn in this run's party is not drawn twice", E.ask_name(held, "m") == "DOT")
ck("a Pokemon is named like a pet", "names a pet" in sent[0] and "five different names" in sent[0])

rival = {"naming": {"title": "HIS NAME?", "max": 7, "presets": ["GARY", "JOHN"]}, "party": []}
E.NAMES_USED.write_text(CLING)
E.brock_probe.chat = fake(["JERK", "GARY", "Dusty"])
ck("the rival is a kid from your town, and JERK is turned away",
   E.ask_name(rival, "m") == "DUSTY" and "kid from your own town" in sent[-1])

player = {"naming": {"title": "YOUR NAME?", "max": 7, "presets": ["RED"]}, "party": []}
E.brock_probe.chat = fake(["Kai", "Kai"])
n = E.ask_name(player, "m")
ck("KAI is never taken, even as the last resort (the game's default instead)", n == "", n)
ck("the player keeps the wording that named ZELDA", "naming their own team" in sent[-1])

E.brock_probe.chat = lambda msgs, model, temp=None: json.dumps({"name": "Carl"})
ck("a reply with one name still works", E.ask_name(starter, "m") == "CARL")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

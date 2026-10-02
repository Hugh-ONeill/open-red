#!/usr/bin/env python3
"""Only a move the game's own table says faints its user is a self-KO move.

Run 25 (2026-10-02): the self-KO record learned from battle text and counted
"Wild VOLTORB fainted!" after our THUNDERBOLT as THUNDERBOLT fainting its
user. It ended up naming thirty ordinary attacks (Thunderbolt, Psybeam, Mega
Punch, Earthquake, Surf, Fly...), so the policy's "self-KO moves go last" had
nothing left to prefer, and Electrode used SELFDESTRUCT 106 times with
Thunderbolt at full PP (user: "widget is selfdestructing during training when
it has pp for other moves").
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


ck("SELFDESTRUCT and EXPLOSION faint their user", B.faints_its_user("SELFDESTRUCT")
   and B.faints_its_user("EXPLOSION"))
ck("THUNDERBOLT, MEGA_PUNCH, FLY and TAKE_DOWN do not",
   not any(B.faints_its_user(m) for m in ("THUNDERBOLT", "MEGA_PUNCH", "FLY", "TAKE_DOWN")))

# run 25's record, as it stood
polluted = {"SELFDESTRUCT": 179, "EXPLOSION": 20, "THUNDERBOLT": 4, "PSYBEAM": 4,
            "MEGA_PUNCH": 1, "FLY": 9, "EARTHQUAKE": 2, "SURF": 3}
ck("a polluted record names only the two", B.self_ko_moves({"self_ko": polluted})
   == {"SELFDESTRUCT", "EXPLOSION"}, B.self_ko_moves({"self_ko": polluted}))

spec = B.load_spec(str(ROOT / "plans/policy_model_v20.json"))
MOVES = [{"index": 1, "id": "SELFDESTRUCT", "pp": 5, "power": 130, "type": "NORMAL", "accuracy": 100},
         {"index": 2, "id": "SCREECH", "pp": 40, "power": 0, "type": "NORMAL", "accuracy": 85},
         {"index": 3, "id": "THUNDERBOLT", "pp": 15, "power": 95, "type": "ELECTRIC", "accuracy": 100},
         {"index": 4, "id": "LIGHT_SCREEN", "pp": 30, "power": 0, "type": "PSYCHIC_TYPE", "accuracy": 100}]
o = {"battle": {"kind": "wild", "me": {"species": "ELECTRODE", "level": 34, "hp": 95, "maxhp": 95,
                                        "types": ["ELECTRIC"], "moves": MOVES, "slot": 1},
                "foe": {"species": "VOLTORB", "level": 16, "hp": 40, "maxhp": 40, "types": ["ELECTRIC"]}},
     "party": [{"species": "ELECTRODE", "level": 34, "hp": 95, "max_hp": 95}]}
d = B.choose(o, spec, {"turn": 1, "used": {}, "intent": "fight", "self_ko": polluted})
ck("Electrode against a wild Voltorb uses Thunderbolt even with that record loaded",
   d.get("index") == 3, d)

td = Path(tempfile.mkdtemp())
E.SELF_KO_PATH = td / "self_ko.json"
E.SELF_KO.clear()
before = {"me": {"species": "ELECTRODE", "hp": 95}}
ck("a wild foe fainting after our THUNDERBOLT is not journaled",
   not E._journal_self_ko(before, {"battle_text": "WIDGET used THUNDERBOLT! / Wild VOLTORB fainted!"},
                          "THUNDERBOLT") and "THUNDERBOLT" not in E.SELF_KO)
ck("our own SELFDESTRUCT that faints us is",
   E._journal_self_ko(before, {"battle_text": "WIDGET used SELFDESTRUCT! / WIDGET fainted!"},
                      "SELFDESTRUCT") and E.SELF_KO.get("SELFDESTRUCT") == 1)
ck("...but not when the faint line is the wild foe's",
   not E._journal_self_ko(before, {"battle_text": "WIDGET used SELFDESTRUCT! / Wild VOLTORB fainted!"},
                          "SELFDESTRUCT") or E.SELF_KO.get("SELFDESTRUCT") == 1)
src = (ROOT / "planner/executor.py").read_text()
ck("a stale record is filtered on load", "if battle_policy.faints_its_user(k)})" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

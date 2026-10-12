#!/usr/bin/env python3
"""A replacement after a faint is chosen against the foe still out, though the
forced pick's screen shows no foe.

Run 54 (2026-10-12), BROCK's ONIX: PIDGEY fainted, the party menu's
observation carried no foe, best_matchup found no types and fell back to
health, and a full PIKACHU (slot 2) tied a full BULBASAUR (slot 3): eight
THUNDERSHOCKs at no effect, three blackouts. The foe the fight last showed is
remembered and read instead.

Synthetic: a stub bridge plays one turn, the faint and the forced pick.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as BP  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


def mon(sp, lv, hp, mx, types, moves):
    return {"species": sp, "level": lv, "hp": hp, "max_hp": mx, "types": types,
            "moves": [{"id": m, "pp": 20} for m in moves]}


ONIX = {"species": "ONIX", "level": 14, "hp": 5, "max_hp": 40, "types": ["ROCK", "GROUND"]}
PIK = mon("PIKACHU", 12, 33, 33, ["ELECTRIC"], ["THUNDERSHOCK", "GROWL", "THUNDER_WAVE"])
BUL = mon("BULBASAUR", 12, 35, 35, ["GRASS", "POISON"], ["TACKLE", "GROWL", "LEECH_SEED"])
PID_UP = mon("PIDGEY", 13, 3, 35, ["NORMAL", "FLYING"], ["GUST", "SAND_ATTACK"])
PID_DOWN = dict(PID_UP, hp=0)

spec = {"replacement": {"order": "best_matchup", "min_hp_frac": 0.4}}
with_foe = {"party": [PID_DOWN, PIK, BUL], "battle": {"foe": ONIX}}
ck("with the foe on screen, best_matchup sends BULBASAUR",
   BP.choose_replacement(with_foe, spec) == 3)
no_foe = {"party": [PID_DOWN, PIK, BUL], "battle": {}}
ck("with no foe it falls back to health, and the tie goes to slot 2",
   BP.choose_replacement(no_foe, spec) == 2)

turn = {"mode": "battle", "party": [PID_UP, PIK, BUL],
        "battle": {"kind": "trainer", "trainer": "BROCK", "leader": True,
                   "foe": ONIX, "me": dict(PID_UP)}}
forced = {"mode": "battle", "party": [PID_DOWN, PIK, BUL],
          "battle": {"kind": "trainer", "behind_a_menu": "PartyMenu", "me": None},
          "ui": {"screenId": "PartyMenu"}}
done = {"mode": "overworld", "party": [PID_DOWN, PIK, BUL]}
sent = []


class Stub:
    def send(self, op, **kw):
        sent.append((op, kw))
        if op == "pick_party":
            return dict(done, result={"ok": True})
        return dict(forced, result={"ok": True})

    def obs(self):
        return done


full = dict(E.ACTIVE_SPEC or {}, **spec) if isinstance(E.ACTIVE_SPEC, dict) else spec
E._run_policy(full, Stub(), turn, lambda *a, **k: None, max_turns=4)
picks = [kw.get("slot") for op, kw in sent if op == "pick_party"]
ck("in the fight, the forced pick sends BULBASAUR (slot 3)", picks == [3], sent)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

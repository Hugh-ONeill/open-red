#!/usr/bin/env python3
"""The TM and level-up questions say when the battle policy in force would
never choose a move, read off that policy's own rules.

Run 62, 2026-10-24: the party carried DOUBLE_TEAM, SWORDS_DANCE, MEDITATE,
REST and METRONOME under a policy (v20) whose setup rules cover paralyze,
sleep and raise_speed only, and choose() picks a move that does no damage
only through a setup rule or once nothing damaging has PP: five of
twenty-four slots no fight would use (user: "maybe we should warn the bot
against letting them learn a move the policy doesnt use").

Pinned: a damaging move is never flagged; a status move named by a rule, or
in a rule's class, is not flagged; one in neither is; no spec says nothing;
the level-up question says it of the offered move and of known moves; the
TM question carries the line.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

SPEC = {"name": "TestPolicy", "setup": [{"move": "paralyze"}, {"move": "sleep"},
                                         {"move": "raise_speed"}, {"move": "LEECH_SEED"}]}
ck("a damaging move is never flagged", B.policy_never_picks("THUNDERBOLT", SPEC) is None)
ck("a status move in a rule's class is not", B.policy_never_picks("THUNDER_WAVE", SPEC) is None
   and B.policy_never_picks("AGILITY", SPEC) is None)
ck("a status move a rule names is not", B.policy_never_picks("LEECH_SEED", SPEC) is None)
w = B.policy_never_picks("DOUBLE_TEAM", SPEC)
ck("a status move in no rule is flagged, naming the rules",
   w and "never picks DOUBLE_TEAM" in w and "paralyze" in w and "TestPolicy" in w, w)
ck("no policy says nothing", B.policy_never_picks("DOUBLE_TEAM", None) is None)
ck("an unknown name says nothing", B.policy_never_picks("NOT_A_MOVE", SPEC) is None)

q = E.Executor._forget_user("PIKACHU", "ELECTRIC", "DOUBLE_TEAM",
                            ["THUNDERBOLT", "AGILITY", "REST", "SURF"], "win", spec=SPEC)
ck("the level-up question flags the offered move", "MIND: your battle policy" in q, q)
ck("...and names known moves it never picks", "never picks REST" in q, q)
q0 = E.Executor._forget_user("PIKACHU", "ELECTRIC", "DOUBLE_TEAM",
                             ["THUNDERBOLT"], "win")
ck("...and says nothing without a policy", "MIND" not in q0, q0)

src = (ROOT / "planner" / "executor.py").read_text()
ck("the TM question carries the line",
   "_never = battle_policy.policy_never_picks(move, ACTIVE_SPEC)" in src
   and 'f"MIND: {_never}.\\n"' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

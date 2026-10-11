#!/usr/bin/env python3
"""What was said before the harness's medicine is kept.

Run 47, Cerulean (2026-10-10): the rival's fight ended, a field POTION
went in at once, and only then did EVENT_BEAT_CERULEAN_RIVAL fire. The
round quoted "TRUFFLE recovered by 20!" and nothing else; "I went to
BILL's ... Since you're using his system, go thank him!", the game's one
pointer to the S.S. Ticket, reached neither the round nor the run's record
of what people said. Probed from run 47's own Cerulean save: when the
speech has printed first, the hints ledger keeps it under the rival.

Pinned: a dialog after the fight is ridden out before any field item;
the words on screen are kept only when an item is used, and only if they
were printed in this op; the op's speech puts them back in front of the
medicine's line. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


hb = SRC[SRC.index("    def handle_battle("):]
hb = hb[:hb.index("\n    def ", 10)]
i_settle = hb.index('if (obs or {}).get("mode") == "dialog":\n            obs = self.settle() or obs')
i_cure = hb.index("pick = battle_policy.should_field_cure(obs, ACTIVE_SPEC)")
ck("a dialog after the fight is ridden out before any field item", i_settle < i_cure)
ck("the words are kept with their print counter",
   '(obs or {}).get("text_seq"))' in hb and "def _keep_said():" in hb)
ck("...and only when an item is used: cure, revive and heal each keep them",
   hb.count("_keep_said()") == 4)            # the def's own line + three uses
rt = SRC[SRC.index("    def _run_traced("):]
rt = rt[:rt.index("\n    def ", 10)]
ck("each op starts with nothing kept", "self._said_before_meds = None" in rt)
ck("the op's speech puts them in front, only if printed in this op",
   '_sbm[1] != (pre_obs or {}).get("text_seq")' in rt
   and 'said = _sbm[0] + " / " + said' in rt)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"{len(checks) - len(failed)}/{len(checks)} passed")
sys.exit(1 if failed else 0)

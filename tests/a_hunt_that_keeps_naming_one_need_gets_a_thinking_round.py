#!/usr/bin/env python3
"""A hunt whose plan sentences keep naming the same lacking thing gets a
deliberating round, even though it never stands still.

RED_THINK_ON_STUCK turns thinking on after N rounds that changed nothing
the run carries, knows or is. A drink hunt that walks Cerulean to Viridian
to Route 5 and back changes the map every round, so it is never stale by
that meter: run 34's Fresh Water hunt and the run of record's on
2026-09-23 (43 rounds from 11:34, think_on 0) never got one, while every
plan sentence said "I need FRESH WATER". The sentences are kept per target
(_plan_hist); when the latest THINK_ON_NEED of them all name one thing the
bag lacks, the step is stuck in the sense that matters.

Pinned: the streak is read back from the latest sentence and counts only
what every sentence in it names; a sentence naming nothing, or a thing the
bag now holds, ends it; the gate reads it beside the stale count; the
thinking it buys is capped per NEED, with its own counter, so a hunt that
travels does not deliberate every round for free; the row says the need
and the streak. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ex_with(sentences, target="map:VERMILION_CITY"):
    ex = E.Executor.__new__(E.Executor)
    ex._cur_target = target
    ex._plan_hist = {target: [[i, "ROUTE_6", s] for i, s in enumerate(sentences)]}
    return ex


NEED = ["I need FRESH WATER to pass the guard.",
        "I need Fresh Water; the Cerulean Mart does not sell it.",
        "I must obtain FRESH WATER to pass the Route 6 gate.",
        "I need FRESH WATER, so I will go to Viridian.",
        "I need FRESH WATER to pass the guards on Route 5 and 6."]

ck("five sentences naming one lacking thing are a streak of five",
   ex_with(["I will explore south."] + NEED)._need_streak({"bag": {}})
   == ("FRESH_WATER", 5))
ck("...counted back from the latest, so an older sentence about something else is not in it",
   ex_with(["I need the S.S. TICKET."] + NEED)._need_streak({"bag": {}})[1] == 5)
ck("a latest sentence naming nothing ends the streak",
   ex_with(NEED + ["I will walk south to Vermilion."])._need_streak({"bag": {}}) == (None, 0))
ck("...and so does the bag holding the thing",
   ex_with(NEED)._need_streak({"bag": {"FRESH_WATER": 1}}) == (None, 0))
ck("a sentence naming a different thing breaks it",
   ex_with(NEED[:3] + ["I need the SECRET KEY."] + NEED[3:])._need_streak({"bag": {}})
   == ("FRESH_WATER", 2))
ck("no history is no streak",
   E.Executor.__new__(E.Executor)._need_streak({"bag": {}}) == (None, 0))
ck("the threshold is five sentences", E.Executor.THINK_ON_NEED == 5)

SRC = (ROOT / "planner/executor.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
i = _code.index("_need, _streak = self._need_streak(obs)")
j = _code.index('self.log("think_on"', i)
gate = _code[i:j]
ck("the gate reads the streak beside the stale count",
   "_by_need = (_streak >= self.THINK_ON_NEED" in gate
   and "self._stale_rounds >= brock_probe.THINK_ON_STUCK" in gate
   and "or _by_need))" in gate)
ck("...and the thinking it buys is capped per need, with its own counter",
   "self._thought_need < _cap" in gate
   and "self._need_key, self._thought_need = _need, 0" in gate
   and "self._thought_need += 1" in _code[i:j + 400])
ck("the row says the need and the streak",
   "need=_need, need_streak=_streak" in _code[j:j + 400])
ck("the stale gate is untouched: RED_THINK_ON_STUCK still turns the whole thing on and off",
   "brock_probe.THINK_ON_STUCK > 0\n                      and ((self._stale_rounds" in _code)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

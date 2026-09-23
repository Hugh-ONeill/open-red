#!/usr/bin/env python3
"""A REORDER THE LADDER IS ABOUT TO MAKE IS JUDGED LIKE THE DRAW.

Since 1daf96b the outline is judged when it is composed: a fact the game
does not bear out, a town arrived at before the town that opens it, a gate
item fetched before the town it is got in. The rungs that rewrite the list
in play — push, pull, insert — were not. On 2026-09-23 (run of record, run
34's outline) the later rung pushed "Reach Vermilion City" from 11 to 20,
behind Celadon and Erika, on the reason "CUT is obtained from the gym
leader in Celadon City"; the blocker rung then pulled the HM01 leg to 12,
in front of the city it is in. Both are the very faults the judge names,
and the run spent the rest of its morning hunting a drink for a gate it
did not need.

So the three tools ask the same judge before they write: a change that
ADDS a fault the list did not have is refused, and the caller falls
through to its next rung, exactly as a refused pull already does. A fault
the list already carries is not held against a move (the draw may have
left one in, and the rungs must still be able to work around it). Nothing
here reaches a prompt: the judge speaks to the log, and the model is asked
its next question as before.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def faults(legs: list) -> set:
    """The judge's flags that are faults, in its own words: a false fact,
    a reach-order pair, a gate item placed before the town it is got in."""
    from compare_outlines import judge
    j = judge([str(l).strip() for l in legs if str(l).strip()])
    return {f for f in (j.get("flags") or [])
            if f.startswith("FALSE FACT") or f.startswith("reach order")
            or "comes BEFORE" in f}


def added_faults(before: list, after: list) -> list:
    """Faults `after` has that `before` did not; empty when the change adds
    none. A judge that cannot run adds none either — the gate never
    blocks on its own failure."""
    try:
        return sorted(faults(after) - faults(before))
    except Exception:
        return []


def refusal(what: str, bad: list) -> str:
    return (f"{what} refused: it would put the list in an order the run "
            f"cannot walk, or state what the game does not bear out — "
            + "; ".join(bad))

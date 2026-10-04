#!/usr/bin/env python3
"""A done_when condition as the MODEL may read it.

A slot_level check is pinned at plan start to the Pokemon standing in that
slot, by its DVs and its trainer id (executor.slot_of): those never change,
evolution included, so the check follows the Pokemon wherever the party is
reordered. They are the harness's own bookkeeping — no screen in gen 1
shows a DV — and the pin lives in the plan file, which is quoted back to
the model in the status line, in the plan echo, in the draft skeletons and
in the carried-gate notes. So it leaked, everywhere a condition is printed
(user, 2026-09-20: "were still leaking the DVs in the donewhen/carried
text").

Used ONLY where a condition becomes text. Where one is compared with
another — carry_gates matching a gate across a rewrite, the plan digest —
the whole thing is compared, pin and all, or two checks pinned to
different Pokemon would read as one.
"""
from __future__ import annotations

import json

# what a Pokemon carries in the save and shows on no screen
HIDDEN = ("dvs", "otId")


def for_model(pred):
    """The condition with the pin's hidden numbers taken out."""
    if isinstance(pred, dict):
        out = {}
        for k, v in pred.items():
            # THE FROZEN LIST IS BOOKKEEPING, TOO. new_map_from freezes every
            # map stood on when the step begins (Executor._freeze_new_part),
            # and the whole list was printed wherever the condition was: 99
            # map names on the status line and the page for one step (run 36,
            # 2026-10-03, user: "also check out the DONEWHEN for that"). Said
            # as what it means.
            if k == "not_maps" and isinstance(v, list) and len(v) > 12:
                out[k] = f"the {len(v)} map(s) stood on when this step began"
                continue
            if k == "who" and isinstance(v, dict):
                v = {a: b for a, b in v.items() if a not in HIDDEN}
                if not v:
                    continue
            out[k] = for_model(v)
        return out
    if isinstance(pred, list):
        return [for_model(x) for x in pred]
    return pred


def dumps(pred, **kw) -> str:
    """json.dumps of a condition, for a page or a prompt."""
    return json.dumps(for_model(pred if pred is not None else {}), **kw)

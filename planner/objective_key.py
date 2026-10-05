"""THE THING AN OBJECTIVE NAMES, so its rewordings share one record.

The ladder rewrites an objective it moves later, and the per-objective
search record was filed under the exact words: run 36 hunted HM04 as
"Retrieve the HM04 from the Safari Zone", "Obtain HM04 from the Safari
Zone" and "Obtain HM04 from the Warden in the Safari Zone", three records
of one search, and each fresh draft saw only its own (2026-10-05, user:
"its easy to get caught up in the trap of the safari zone"). On-screen
tier: the bag names a machine HM04 and a key item SECRET KEY, so the
words an objective spells them with are the bag's own."""
from __future__ import annotations

import re
from pathlib import Path


def _names(fname: str) -> set:
    try:
        p = Path(__file__).with_name(fname)
        return {l.strip() for l in p.read_text().splitlines() if l.strip()}
    except OSError:
        return set()


_KEY_ITEMS = _names("engine_key_items.txt")
# "HM04 STRENGTH" rows: the bag spells a machine by its move (HM_STRENGTH,
# TM_REST) and the objectives by its number (HM04), so both name one key
# (run 36's Victory Road drafts wrote HM_STRENGTH, 2026-10-05).
_MACHINES = {}
for _row in _names("engine_machines.txt"):
    _num, _, _move = _row.partition(" ")
    if _num and _move:
        _MACHINES[f"{_num[:2]}_{_move.strip()}"] = _num
_MACHINE = re.compile(r"\b([HT]M)\s?0*(\d{1,2})\b", re.I)


def objective_items(goal) -> frozenset:
    """The machines and key items an objective's words name, as bag ids.
    Empty when it names none: such an objective is matched by its words."""
    g = str(goal or "")
    out = {f"{m.group(1).upper()}{int(m.group(2)):02d}"
           for m in _MACHINE.finditer(g)}
    flat = "_" + re.sub(r"[^A-Z0-9]+", "_", g.upper().replace("É", "E")) + "_"
    flat = flat.replace("_SS_", "_S_S_")
    for bag, num in _MACHINES.items():
        if f"_{bag}_" in flat:
            out.add(num)
    for it in _KEY_ITEMS:
        if f"_{it}_" in flat:
            out.add(it)
    return frozenset(out)


def same_objective(a, b, norm=lambda g: " ".join(str(g or "").split()).lower()) -> bool:
    """One objective under two wordings: the same named things when either
    names any, the same words otherwise."""
    ia, ib = objective_items(a), objective_items(b)
    if ia or ib:
        return ia == ib
    return norm(a) == norm(b)

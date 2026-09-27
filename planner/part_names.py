#!/usr/bin/env python3
"""A MAP IN SEVERAL WALKED PARTS NAMES EACH PART BY WHERE IT LIES.

The page names a part of a map by the map and an anchor cell: Route 2's
halves were "ROUTE_2|8,0" and "ROUTE_2|3,43", and nothing said which was
which. Run of record 7 (2026-09-26), in Viridian Forest: "avoiding the North
Gate (which I know leads back to Route 2)" — the gate leads to Route 2's
NORTH half, a screen from Pewter, and the model read "Route 2" as the half it
had come up (run 4 did the same on 2026-09-25; user: "put it on the next stop
list").

So the first time a text mentions a part of a map the run has walked in two
or more parts, the mention gains where that part lies among them: "ROUTE_2|8,0
(the north part of ROUTE_2)". Later mentions are left alone, and the key
itself is never changed, because ops take it. The place is read from the
parts' own anchor cells against each other — geometry the run walked, not
the game's map."""
from __future__ import annotations

import json
import re
from pathlib import Path

REGION = re.compile(r"\b([A-Z][A-Z0-9_]*[A-Z0-9])\|(\d+),(\d+)\b")


def labels(regions) -> dict:
    """{"MAP|x,y": "north"} for each part of a map with 2+ parts."""
    by: dict = {}
    for r in regions or ():
        m = REGION.fullmatch(str(r))
        if m:
            by.setdefault(m.group(1), set()).add((int(m.group(2)), int(m.group(3))))
    out = {}
    for mp, cells in by.items():
        if len(cells) < 2:
            continue
        cells = sorted(cells)
        xs = [x for x, _ in cells]
        ys = [y for _, y in cells]
        # RANKED ALONG THE WIDER SPREAD, so every part gets its own word:
        # Route 9's three parts are west, middle and east, not west twice
        ns = (max(ys) - min(ys)) >= (max(xs) - min(xs))
        order = sorted(cells, key=(lambda c: (c[1], c[0])) if ns else (lambda c: (c[0], c[1])))
        lo, hi = ("north", "south") if ns else ("west", "east")
        n = len(order)
        for k, (x, y) in enumerate(order):
            if n == 2:
                lab = lo if k == 0 else hi
            elif n == 3:
                lab = (lo, "middle", hi)[k]
            else:
                lab = (f"{lo}most" if k == 0 else f"{hi}most" if k == n - 1
                       else f"number {k + 1} from the {lo}")
            out[f"{mp}|{x},{y}"] = lab
    return out


def name_parts(text: str, regions) -> str:
    """The text with each labelled part's FIRST mention said with its place."""
    lab = labels(regions)
    if not lab or not text:
        return text
    done: set = set()

    def sub(m):
        key = m.group(0)
        if key in lab and key not in done:
            done.add(key)
            return f"{key} (the {lab[key]} part of {m.group(1)})"
        return key
    return REGION.sub(sub, text)


def walked_regions(path="run/explored.json") -> list:
    """The parts this run has walked, from its memory file (the author,
    which runs outside the executor)."""
    try:
        d = json.loads(Path(path).read_text() or "{}")
    except (OSError, ValueError):
        return []
    ex = d.get("explored") if isinstance(d.get("explored"), dict) else d
    return list((ex or {}).keys()) + list((d.get("visits") or {}).keys())

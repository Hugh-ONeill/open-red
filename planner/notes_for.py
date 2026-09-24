#!/usr/bin/env python3
"""WHAT A PARTY LEG IS FOR, AS THE LEG, NOT ITS NUMBER.

The outline's party pass is shown the story legs numbered and says what
each party leg is for; it answers "5" as often as in words. The number is
its index into the list it was shown, and it went into plans/outline.notes
as "for: 5". That note rides into the leg's goal string ("a doubt you
recorded when outlining: for: 5"), where it names nothing: the plan author
has never seen that numbering, and the live outline stops matching it the
first time a leg is added or dropped (run of record 3 lost "Reach Viridian
City", so every number was one off). User, 2026-09-24: "show it the leg
text". A number, or a list of numbers, becomes the leg(s) it indexes; a
number past the end, or words, stay as they were said.

  notes_for.py NOTES AUTHORED UPKEEP    # rewrite a notes file in place
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

NUMS = re.compile(r"^(?:legs?|objectives?)?\s*#?(\d+)((?:\s*(?:,|and|&)\s*#?\d+)*)\.?$", re.I)


def resolve(value: str, story: list) -> str:
    """"5" -> story[4]; "5 and 9" -> both, joined with "; "."""
    v = " ".join(str(value or "").split())
    m = NUMS.match(v)
    if not m:
        return v
    ns = [int(x) for x in re.findall(r"\d+", v)]
    if not all(1 <= n <= len(story) for n in ns):
        return v
    return "; ".join(story[n - 1] for n in ns)


def story_legs(authored: Path, upkeep: Path) -> list:
    def lines(p):
        try:
            return [l.strip() for l in p.read_text().splitlines() if l.strip()]
        except OSError:
            return []
    up = set(lines(upkeep))
    return [l for l in lines(authored) if l not in up]


def rewrite(notes: Path, story: list) -> int:
    out, n = [], 0
    for line in notes.read_text().splitlines():
        leg, tab, note = line.partition("\t")
        if tab and note.lower().startswith("for:"):
            new = "for: " + resolve(note[4:], story)
            n += new != note
            note = new
        out.append(leg + tab + note)
    # the chain reads this file at every leg boundary: never half-written
    tmp = notes.with_name(notes.name + ".tmp")
    tmp.write_text("\n".join(out) + "\n")
    tmp.replace(notes)
    return n


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    _n = rewrite(Path(sys.argv[1]), story_legs(Path(sys.argv[2]), Path(sys.argv[3])))
    print(f"{_n} note(s) now name their leg")

#!/usr/bin/env python3
"""A party leg's note names the leg it is for, not that leg's number.

The party pass answers "for: 5" by its index into the story list it was
shown; the note rode into the goal string as "a doubt you recorded when
outlining: for: 6", a number no reader of it had seen, and one leg off
once the live outline dropped "Reach Viridian City" (run of record 3,
2026-09-24; user: "show it the leg text").

Pinned: a number, or a list of them, becomes the leg(s); words and a
number past the end stay as said; a notes file is rewritten in place
against the banked story list, whole; the party pass resolves at write
time against the list it numbered. Synthetic."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import notes_for as N  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


STORY = ["Pick a starter", "Reach Viridian City", "Reach Pewter City",
         "Defeat Brock for the Boulder Badge", "Reach Mt. Moon"]
ck("a number becomes the leg it indexes", N.resolve("4", STORY) == STORY[3])
ck("...however it is written",
   N.resolve(" leg 4. ", STORY) == STORY[3] and N.resolve("#4", STORY) == STORY[3])
ck("a list of numbers becomes each leg",
   N.resolve("4 and 5", STORY) == f"{STORY[3]}; {STORY[4]}"
   and N.resolve("4, 5", STORY) == f"{STORY[3]}; {STORY[4]}")
ck("words stay as said",
   N.resolve("navigating the world", STORY) == "navigating the world"
   and N.resolve("reaching level 12 by Brock", STORY) == "reaching level 12 by Brock")
ck("a number past the end stays as said",
   N.resolve("9", STORY) == "9" and N.resolve("0", STORY) == "0")

d = Path(tempfile.mkdtemp(prefix="notes_"))
(d / "a").write_text("\n".join(STORY[:3] + ["the party holds a GRASS type"] + STORY[3:]) + "\n")
(d / "u").write_text("the party holds a GRASS type\n")
(d / "n").write_text("the party holds a GRASS type\tfor: 4\n"
                     "every party member is at least level 12\tfor: beating Brock\n"
                     "Some reworded leg\tsaid differently in the draft\n")
n = N.rewrite(d / "n", N.story_legs(d / "a", d / "u"))
got = (d / "n").read_text().splitlines()
ck("a notes file is rewritten against the banked story list",
   got[0] == "the party holds a GRASS type\tfor: Defeat Brock for the Boulder Badge"
   and n == 1, got)
ck("...and every other line is kept as it was",
   got[1:] == ["every party member is at least level 12\tfor: beating Brock",
               "Some reworded leg\tsaid differently in the draft"], got)

au = (ROOT / "planner/author.py").read_text()
ck("the party pass resolves at write time, against the list it numbered",
   "_for = notes_for.resolve(_for, legs)" in au
   and 'OUTLINE_NOTES.append((item, f"for: {_for}"))' in au
   and au.index("_for = notes_for.resolve(_for, legs)")
   < au.index('OUTLINE_NOTES.append((item, f"for: {_for}"))'))

failed = [n for n, ok, _ in checks if not ok]
for nm, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + nm + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""Keep the lines of an outline sidecar that still name a banked objective.

plans/outline.upkeep and plans/outline.stages name legs by wording, and a
fresh chain puts the outline back as authored (plans/outline.authored). The
fresh block used to keep a sidecar only when EVERY line matched and archive
it whole otherwise, silently. Run 19's wording rung had written one upkeep
line with the page's outline note baked in, so at run 20's launch the whole
upkeep list went to the archive without a word and every party leg became
fatal (2026-10-01). Now: the note is stripped, matching lines stay, the rest
are archived and named.

Usage: sidecar_keep.py SIDECAR AUTHORED ARCHIVE_PATH
Prints what it did; exit 0 always (a sidecar is never worth stopping for).
"""
import re
import shutil
import sys
from pathlib import Path

NOTE = re.compile(r"\s*\((?:a doubt you recorded when outlining:|you added this "
                  r"when outlining,).*$")


def leg_of(line: str) -> str:
    parts = line.split("\t")
    return parts[1] if len(parts) > 1 else parts[0]


def keep(side: Path, authored: Path) -> tuple:
    banked = {l for l in authored.read_text().splitlines() if l.strip()} \
        if authored.exists() else set()
    kept, dropped, fixed = [], [], 0
    for line in side.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        i = 1 if len(parts) > 1 else 0
        bare = NOTE.sub("", parts[i]).strip()
        if bare != parts[i]:
            parts[i], fixed = bare, fixed + 1
        if bare in banked:
            kept.append("\t".join(parts))
        else:
            dropped.append(line)
    return kept, dropped, fixed


def main(argv):
    side, authored, archive = (Path(a) for a in argv[:3])
    if not side.exists():
        return
    kept, dropped, fixed = keep(side, authored)
    if not dropped and not fixed:
        print(f"kept {side}: every leg it names is the banked wording")
        return
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(side, archive)
    side.write_text("\n".join(kept) + ("\n" if kept else ""))
    print(f"kept {len(kept)} line(s) of {side}"
          + (f", {fixed} with an outline note stripped" if fixed else "")
          + (f"; archived {len(dropped)} that name no banked leg: "
             + "; ".join(leg_of(d)[:70] for d in dropped) if dropped else "")
          + f" (the original is {archive})")


if __name__ == "__main__":
    main(sys.argv[1:])

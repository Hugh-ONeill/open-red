#!/usr/bin/env python3
"""go's one-part note reads the part's own verdict, not the map's pocket count.

Run 70, 2026-11-02: go's arrival note on CELADON_MANSION_ROOF|6,1 said "1
spot(s) where that seen ground ends can be reached from the part you have
walked" while the region's page said EVERYTHING YOU CAN REACH HERE IS DONE
(frontier_here 0, its unseen spot unreachable). map_seen is the pocket rule,
positive while the map has unseen ground anywhere; _unseen_there is the one
relation every ledger row reads. Pinned by source.
"""
import sys
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
i = src.index("...AND THE PART'S OWN VERDICT, NOT THE MAP'S COUNT.")
blk = src[i:i + 2200]
checks = [
    ("the note asks _unseen_there for the part walked",
     "self._unseen_there(best[0])[1]" in blk),
    ("a done part says nothing could be reached from it",
     'if _uv == "done" else' in blk and "none of the" in blk),
    ("...otherwise the count stands", "spot(s) where that seen ground" in blk),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""The toss refusal says what using and tossing do, without ranking them.

Runs 69 and 70 (2026-10-31 / 2026-11-02, Safari Zone): "using it spends it
and keeps whatever it is worth, tossing it destroys that" read as "teach it
rather than toss it", and run 70 taught TM_PSYWAVE over REFLECT to free one
slot. Pamphlet standard: say what each op does; the choice is the model's.
Pinned by source on the shim's toss guard.
"""
import sys
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
i = src.index("function OPS.toss(G, c)")
body = src[i:src.index("\nfunction OPS.", i + 10)]
# the words the model is sent, not the comments that quote the old line
body = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("--"))
checks = [
    ("no worth ranking", "keeps whatever it is" not in body and "destroys that" not in body),
    ("both ops are said", "using it spends it on that Pokemon; tossing it" in body
     and "throws it away." in body),
    ("the confirm gate is unchanged", 'send the same "\n      .. "toss again with \\"confirm\\":true' in body
     or 'toss again with \\"confirm\\":true' in body),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)

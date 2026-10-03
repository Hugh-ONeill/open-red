#!/usr/bin/env python3
"""A bonus leg gets one try in all, so no rewrite is written after it.

Every other leg's closing rewrite is the plan its next run loads; a bonus
leg (the other half of an "or" that already held) never comes back, and
its rewrite was authored and never played (run 36, 2026-10-03, user: "but i
thought i saw it rewriting?"). Pinned: only the bonus call asks for it; the
skip comes after the objective-met check and only on the last attempt."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
fd = (ROOT / "fresh_discovery.sh").read_text()
cs = (ROOT / "campaign.sh").read_text()
checks = [
    ("the bonus leg's campaign asks for no closing rewrite",
     'RED_CONTINUE=1 RED_NO_CLOSING_REWRITE=1 \\\n            ./campaign.sh 1 "$_bp"' in fd),
    ("...and it is the only caller that does", fd.count("RED_NO_CLOSING_REWRITE=1") == 1),
    ("campaign skips only on its last attempt",
     '[ "${RED_NO_CLOSING_REWRITE:-0}" = 1 ] && [ "$attempt" -ge "$ATTEMPTS" ]' in cs),
    ("...after the objective-met check, before any authoring",
     cs.index('pred_holds(last, obs)') < cs.index("RED_NO_CLOSING_REWRITE")
     < cs.index('goal=$(python - "plans/$failed_plan"')),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)

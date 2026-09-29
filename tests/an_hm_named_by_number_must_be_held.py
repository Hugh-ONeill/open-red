#!/usr/bin/env python3
"""An objective naming an HM by its number is not done without that HM.

"Retrieve the HM04 from the Safari Zone" was judged done on "the player has
HM_STRENGTH (HM04) in their possession as confirmed by the plans record"
with no HM04 in the bag and the GOLD TEETH still held (run 19, 2026-09-29):
the item guard dropped digits and skipped every HM.

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ST = "standing in SAFARI_ZONE_CENTER with ..., and HM_CUT (HM01) x1, HM_SURF (HM03) x1, GOLD_TEETH x1"
ck("HM04 named, not held: refused", A._item_not_held("Retrieve the HM04 from the Safari Zone", ST) == "HM04")
ck("HM03 named and held: not refused", A._item_not_held("Obtain HM03 Surf from the Safari Zone", ST) is None)
ck("an HM spelled out, not held: refused",
   A._item_not_held("Retrieve the HM_STRENGTH from the Warden", ST) == "HM_STRENGTH")
ck("\"HM 05\" with a space: refused", A._item_not_held("Obtain HM 05 Flash", ST) == "HM05")
ck("a give leg is still the model's",
   A._item_not_held("Give the GOLD_TEETH to the Warden for HM04", ST) is None)
ck("a move leg names no item", A._item_not_held("a party Pokemon knows STRENGTH", ST) is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

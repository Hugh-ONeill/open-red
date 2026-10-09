#!/usr/bin/env python3
"""An item the record shows handed over is not asked of the bag.

"Retrieve the Gold Teeth for the Warden" was refused twice as done with
EVENT_GAVE_GOLD_TEETH fired and HM04 in hand: the objective's verb is RETRIEVE,
so the give-verb exemption never heard it, and the teeth were gone because they
had been given (run 41, 2026-10-09).
"""
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A                                        # noqa: E402

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

d = tempfile.mkdtemp()
gave = Path(d) / "gave.json"; gave.write_text(json.dumps({"flags": ["EVENT_GAVE_GOLD_TEETH", "EVENT_GOT_HM04"]}))
none = Path(d) / "none.json"; none.write_text(json.dumps({"flags": ["EVENT_GOT_HM04"]}))
ck("a GAVE event naming the item says it was handed over", A._handed_over("GOLD_TEETH", str(gave)))
ck("...a GOT event alone does not", not A._handed_over("GOLD_TEETH", str(none)))
ck("...nor another item's", not A._handed_over("SECRET_KEY", str(gave)))
ck("no record, no hand-over", not A._handed_over("GOLD_TEETH", str(Path(d) / "missing.json")))
src = (ROOT / "planner/author.py").read_text()
ck("_item_not_held asks it before refusing", "if _handed_over(it):" in src)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

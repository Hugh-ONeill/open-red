#!/usr/bin/env python3
"""A failed buy names the shelf's items, and not the list's CANCEL row as "nil".

Run 54, CELADON_MART_5F (2026-10-12): "FRESH_WATER is not on
CELADONMART5F_CLERK2's shelf, which holds: HP_UP, PROTEIN, IRON, CARBOS,
CALCIUM, nil" — the CANCEL row carries no item and tostring(nil) went on the
page. Source check (harness/shim.lua).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sh = (ROOT / "harness/shim.lua").read_text()
b = sh[sh.index("function OPS.buy(G, c)"):]
b = b[:b.index("\nfunction OPS.", 10)]
ok = ("if row.value ~= nil then sold[#sold + 1] = tostring(row.value) end" in b
      and "sold[#sold + 1] = tostring(row.value)\n" not in b)
print(("ok   " if ok else "FAIL ") + "the shelf list skips rows with no item")
sys.exit(0 if ok else 1)

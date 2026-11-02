"""The long-chain go refusal says go did not set off and the chain starts here.

Run 70, 2026-11-02, leg 45 v3 travel_to_pallet_town r2-r7: each round go
refused "NOT WALKED — the only chain of exits you have walked from
ROUTE_15|14,8 to PALLET_TOWN|10,0 is 35 leg(s) long ... send
{...,"long":true}". The model read NOT WALKED as "not on the walked chain
yet" and crossed one border a round "to initiate the chain of walked exits",
sending the bare go again every time. Source-shape pin on the refusal.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
i = src.index("A ROUND-THE-WORLD CHAIN IS SAID BEFORE IT IS WALKED")
blk = src[i:i + 3500]
checks = [
    ("the refusal no longer heads itself NOT WALKED", '"go: NOT WALKED' not in blk),
    ("it says go did not set off", "NOT SET OFF" in blk),
    ("it says the chain starts where the party stands", "(it starts here, with" in blk),
    ("it says to send long:true from right here", "from right here, send" in blk),
    ("the long:true op is still printed", '","long":true}' in blk),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""Past the last leg with no Hall of Fame, the chain goes back to the
earliest passed-over leg with returns left, whatever waits on it.

Run 57 (2026-10-16): "Defeat the Elite Four" was passed over, nothing in
the inserts ledger recorded the final rival fight waiting on it, the last
leg was stepped over, and the chain ended on Victory Road with eight
badges. A stepped-over leg is now written down as passed over too.

Synthetic, plus source checks.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


RP = "Reach the Indigo Plateau"
E4 = "Defeat the Elite Four"
VR = "Exit Victory Road"
RV = "Defeat the rival after the Elite Four"
OUT = ["Pick a starter", RP, E4, VR, RV]


def ret(i, passed, returns=()):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        (d / "plans/outline.txt").write_text("\n".join(OUT) + "\n")
        (d / "run/outline_passed").write_text("".join(t + "\n" for t in passed))
        (d / "run/outline_inserts").write_text("")
        (d / "run/outline_returns").write_text("".join(t + "\n" for t in returns))
        r = subprocess.run([sys.executable, str(ROOT / "planner/return_leg.py"), str(i)],
                           cwd=d, capture_output=True, text=True)
        return (r.returncode, r.stdout.strip(),
                (d / "run/outline_passed").read_text().splitlines(),
                (d / "run/outline_returns").read_text().splitlines())


rc, out, _, _ = ret(5, [RP, E4], returns=[RP, RP])
ck("at the last leg, a passed leg nothing records waiting is still left", rc == 1, (rc, out))
rc, out, passed, rets = ret(6, [RP, E4, RV], returns=[RP, RP])
ck("past the end: the earliest passed-over leg with returns left",
   rc == 0 and out == f"3\t{E4}", (rc, out))
ck("...everything from it on comes off the passed list", passed == [RP], passed)
ck("...and the return is counted", rets == [RP, RP, E4], rets)
rc, out, _, _ = ret(6, [RP, E4], returns=[RP, RP, E4, E4])
ck("past the end with every return spent: nothing", rc == 1, (rc, out))
rc, out, _, _ = ret(7, [E4])
ck("further past the end than one: nothing", rc == 1, (rc, out))

sh = (ROOT / "fresh_discovery.sh").read_text()
end = sh[sh.index('if [ "$i" -gt "${#LEGS[@]}" ]; then'):]
end = end[:end.index("exit 0")]
ck("past the end asks return_leg before stopping",
   'return_leg.py "$i"' in end and end.index("return_leg.py") < end.index("OUTLINE CHAIN"))
ck("...only when the game is not finished", "! python planner/finished.py" in end)
ck("...rewinds, records a disposition and archives the old plans",
   'echo $((_rp - 1)) > "$PROGRESS"' in end and "DISPOSED" in end
   and "archive_plans_of" in end and "continue" in end)
skip = sh[sh.index('echo "!! could not push leg $i'):]
skip = skip[:skip.index("continue")]
ck("a stepped-over leg is written to the passed list", '"$leg" >> run/outline_passed' in skip)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
"""Before a leg that waits on a passed-over leg, and before the last leg,
the chain goes back to the earliest passed-over leg something ahead still
waits on.

Run 36, 2026-10-05: "Give the GOLD TEETH", "Obtain HM04 STRENGTH" and
"Clear Victory Road" were passed over one after another, and the chain
authored the final rival fight from the Safari Zone (user: "nope it went
straight back to 'Defeat rival in final showdown'").

Pinned: a leg waiting (transitively, PULL rows counting) on a passed-over
leg goes back to the earliest such leg; the last leg goes back to the
earliest passed-over leg with a dependent ahead; one with nothing waiting
on it is left; each leg is gone back to at most twice; the legs replayed
come off the passed list; nothing passed, nothing done; the chain wires
it in before the plan is looked up. Synthetic."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


GT = "Give the GOLD TEETH to the Warden in the Safari Zone"
HM = "Obtain HM04 STRENGTH from the Warden in the Safari Zone"
VR = "Clear Victory Road"
E4 = "Defeat the Elite Four"
RV = "Defeat the rival in the final showdown"
SK = "Retrieve the Secret Key from the Game Corner"
OUT = [SK, "every party member is at least level 50", GT, HM, VR, E4, RV]
INS = [f"LEG={HM}|{GT}", f"LEG={VR}|{HM}", f"LEG={E4}|{VR}"]


def ret(i, passed, inserts=INS, returns=(), rewordings=()):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        (d / "plans/outline.txt").write_text("\n".join(OUT) + "\n")
        (d / "run/outline_passed").write_text("".join(t + "\n" for t in passed))
        (d / "run/outline_inserts").write_text("\n".join(inserts) + "\n")
        (d / "run/outline_returns").write_text("".join(t + "\n" for t in returns))
        (d / "run/outline_rewordings").write_text(
            "".join(f"0\t{a}\t{b}\n" for a, b in rewordings))
        r = subprocess.run([sys.executable, str(ROOT / "planner/return_leg.py"), str(i)],
                           cwd=d, capture_output=True, text=True)
        return (r.returncode, r.stdout.strip(),
                (d / "run/outline_passed").read_text().splitlines(),
                (d / "run/outline_returns").read_text().splitlines())


rc, out, passed, rets = ret(5, [SK, GT, HM])
ck("a leg waiting on passed-over legs goes back to the earliest of them",
   rc == 0 and out == f"3\t{GT}", (rc, out))
ck("...the legs replayed come off the passed list, others stay",
   passed == [SK], passed)
ck("...and the return is counted", rets == [GT], rets)
rc, out, _, _ = ret(7, [SK, GT, HM, VR])
ck("the last leg goes back to the earliest passed-over leg with a dependent ahead",
   rc == 0 and out == f"3\t{GT}", (rc, out))
CH = "Defeat the Pokemon League Champion"
OUT.insert(6, CH)
rc, out, _, _ = ret(7, [SK, GT, HM, VR], inserts=INS + [f"LEG={RV}|{CH}"])
ck("a leg the last leg waits on goes back as the last leg would",
   rc == 0 and out == f"3\t{GT}", (rc, out))
rc, out, _, _ = ret(7, [SK, GT, HM, VR])
ck("...but not a leg nothing records the last leg waiting on", rc == 1, (rc, out))
rc, out, _, _ = ret(7, [SK, GT, HM, VR],
                    inserts=INS + [f"LEG={RV}|Defeat the Elite Four Champion"],
                    rewordings=[("Defeat the Elite Four Champion", CH)])
ck("...and the ledger is read under today's wordings (run 36's case)",
   rc == 0 and out == f"3\t{GT}", (rc, out))
OUT.pop(6)
rc, out, _, _ = ret(7, [SK])
ck("a passed-over leg nothing waits on is left", rc == 1, (rc, out))
rc, out, _, _ = ret(5, [SK, GT, HM], returns=[GT, GT])
ck("a leg gone back to twice is not gone back to again; the next one is",
   rc == 0 and out == f"4\t{HM}", (rc, out))
rc, out, _, _ = ret(5, [SK, GT, HM], returns=[GT, GT, HM, HM])
ck("with every return spent, the leg is played as it stands", rc == 1, (rc, out))
rc, out, _, _ = ret(5, [GT], inserts=[f"LEG={HM}|PULL {GT}", f"LEG={VR}|{HM}"])
ck("a PULL row counts as waiting", rc == 0 and out == f"3\t{GT}", (rc, out))
rc, out, _, _ = ret(6, [])
ck("nothing passed over, nothing to go back to", rc == 1, (rc, out))

src = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain asks before looking up the leg's plan",
   src.index('if _ret=$(python planner/return_leg.py "$i"')
   < src.index('plan=$(python planner/find_plan.py "$leg"'))
ck("...goes back by rewinding progress", 'echo $((_rp - 1)) > "$PROGRESS"' in src)
ck("...as a disposition, so its runs are counted afresh",
   '"gone back to from leg $i, which waits on it" >> run/attempt_yield' in src)
ck("...and the count is a chain's, cleared with the rest",
   "run/outline_passed run/outline_returns" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

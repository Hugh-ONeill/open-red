#!/usr/bin/env python3
"""A pull cannot jump a prerequisite the ladder later reworded.

Run 67, 2026-10-27: "Give the GOLD TEETH to the Warden in the Safari Zone
Gate" was inserted before "Retrieve the HM04 from the Safari Zone", reworded
to "...at the Safari Zone Gate", and the blocker rung then pulled the HM04
leg ahead of it -- the inserts ledger's words no longer matched the list's,
and the two legs handed the run back and forth.

Pinned: through a rewording (run/outline_rewordings) the pull is refused,
exit 4; with no rewording the old match still refuses; an unrelated jump
still goes through. Synthetic.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

OLD = "Give the GOLD TEETH to the Warden in the Safari Zone Gate"
NEW = "Give the GOLD TEETH to the Warden at the Safari Zone Gate"
HM = "Retrieve the HM04 from the Safari Zone"


def pull(to, frm, out, inserts, rewordings=()):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "plans").mkdir(); (d / "run").mkdir()
        for f in ("outline.authored", "outline.txt"):
            (d / "plans" / f).write_text("\n".join(out) + "\n")
        (d / "plans/outline.upkeep").write_text("")
        (d / "run/outline_leg").write_text("1")
        (d / "run/outline_inserts").write_text("\n".join(inserts) + "\n")
        (d / "run/outline_rewordings").write_text("\n".join(rewordings) + "\n")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "planner"))
        r = subprocess.run([sys.executable, str(ROOT / "planner/pull_leg.py"),
                            "pull", str(to), str(frm)], cwd=d, env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr, \
            (d / "plans/outline.txt").read_text().splitlines()


OUT = ["Defeat Koga for the Soul Badge", NEW, HM, "Reach Cinnabar Island"]
rc, o, lines = pull(2, 3, OUT, [f"LEG={HM}|{OLD}"], [f"47\t{OLD}\t{NEW}"])
ck("the HM04 leg is not pulled over its reworded prerequisite",
   rc == 4 and lines == OUT, (rc, o))
OUT2 = ["Defeat Koga for the Soul Badge", OLD, HM, "Reach Cinnabar Island"]
rc, o, lines = pull(2, 3, OUT2, [f"LEG={HM}|{OLD}"])
ck("...and with no rewording the old match still refuses", rc == 4, (rc, o))
rc, o, lines = pull(1, 3, ["Reach Cinnabar Island", "Defeat Koga for the Soul Badge", HM],
                    [f"LEG={HM}|{OLD}"], [f"47\t{OLD}\t{NEW}"])
ck("an unrelated jump still goes through", rc == 0 and lines[0] == HM, (rc, o))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

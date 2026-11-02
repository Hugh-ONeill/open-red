#!/usr/bin/env python3
"""author.py's run/ paths follow RED_BRIDGE_DIR when ./run is the live run.

Code-health pass, 2026-11-02 (run 70 stop): every run/ path in author.py was a
CWD-relative literal, so a test importing author from the repo root read and
wrote the LIVE run (outline_void, outline_push_with, leg_witness.json, the
journal) whatever RED_BRIDGE_DIR said; the tests-never-touch-the-live-run
rule was not true for the ~195 tests that import author.

Pinned without touching the live run: from the repo root with RED_BRIDGE_DIR
set to a scratch dir, author's run paths resolve into the scratch dir; in a
scratch tree with its own run/ (the chdir tests), they stay ./run.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

scratch = Path(tempfile.mkdtemp(prefix="bridge_"))
os.environ["RED_BRIDGE_DIR"] = str(scratch)
os.chdir(ROOT)                      # ./run here IS the live run
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

live = (ROOT / "run").resolve()
for name, p in (("OUTLINE_INSERTS", A.OUTLINE_INSERTS),
                ("WITNESS_FILE", A.WITNESS_FILE)):
    got = Path(p).resolve()
    ck(f"{name} resolves into the bridge dir, not the live run",
       str(got).startswith(str(scratch.resolve())) and not str(got).startswith(str(live)), got)
ck("the default run dir argument resolves into the bridge dir",
   Path(getattr(A, "RUN", Path("run"))).resolve() == scratch.resolve(), Path(getattr(A, "RUN", Path("run"))).resolve())
ck("joining under it lands in the bridge dir",
   (Path(getattr(A, "RUN", Path("run"))) / "executor_log.jsonl").resolve().parent == scratch.resolve())

tree = Path(tempfile.mkdtemp(prefix="tree_"))
(tree / "run").mkdir()
os.chdir(tree)
ck("a scratch tree with its own run/ keeps ./run",
   Path(A.WITNESS_FILE).resolve() == (tree / "run/leg_witness.json").resolve(),
   Path(A.WITNESS_FILE).resolve())

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""A ride the game refused is kept in the walked record, not only in memory.

Run 69, 2026-10-31, Seafoam B4F: explore rode for the water frontier at
(3,12), SURF was refused ("The current is much too fast!"), and the refusal
was kept in a set on the executor. Every attempt is a new process, so the
next attempt's explore rode for the same frontier again.

Pinned: the refusal is saved with explored.json, read back on load, and
saved the moment it is kept.
"""
import json, os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
key = ["SEAFOAM_ISLANDS_B4F|15,0", "[5, 'aaaaaaaa', 'bbbbbbbb']"]
d = tempfile.mkdtemp()
mem = Path(d) / "explored.json"
mem.write_text(json.dumps({"ride_refused": [key, ["bad"]]}))
ex = object.__new__(E.Executor)
ex.MEMORY, ex._harness_rev = mem, "x"
for _ in range(120):
    try:
        ex._load_memory()
        break
    except AttributeError as e:
        n = str(e).split("attribute '")[1].rstrip("'")
        setattr(ex, n, {} if not n.startswith("_mark") else None)
rr = getattr(ex, "_ride_refused", set())
ck("a refusal read back is the same key explore asks with", tuple(key) in rr, rr)
ck("...a malformed row is dropped", len(rr) == 1, rr)

src = (ROOT / "planner" / "executor.py").read_text()
ck("it is written with the record",
   '"ride_refused": sorted([list(x) for x in' in src)
i = src.index('self.log("ride_refused_kept", where=_ride_key[0])')
ck("...and saved the moment it is kept", "self._save_memory()" in src[i:i + 120])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
sys.exit(1 if bad else 0)

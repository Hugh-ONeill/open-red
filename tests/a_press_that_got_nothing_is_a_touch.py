"""A press made beside a thing that brought up nothing counts as touched.

Run 70, Celadon Game Corner (2026-11-02): SLOT_MACHINE_12, 13, 24 and 36
answer only from sides other machines stand on; pressed from the free side
they bring up nothing. The op failed, nothing was marked, and the page kept
offering them as untouched for ~6 rounds. User at the stop: pressed-nothing
counts as touched. The shim's words decide it (next354 slots, next359
interact): "... and nothing came up", "... brought up nothing ...".

Pinned: _record_touch keeps such a press and still drops an ordinary
failure; the op-landing site marks it for interact and slots; the failed
interact retraction leaves it standing.
"""
import sys
from pathlib import Path
sys.path.insert(0, "planner")
import executor as E

checks = []
def ck(name, cond, d=""): checks.append((name, bool(cond), d))


def ex_with(det, ok=False):
    ex = E.Executor.__new__(E.Executor)
    ex._tried_objs, ex._shelves, ex._shelf_machine = {}, {}, set()
    ex._save_memory = lambda: None
    ex.log = lambda *a, **k: None
    ex._stamp_touch = lambda r: None
    ex._mark_touch = lambda *a: None
    res = ex._record_touch("GAME_CORNER|1,6", "SLOT_MACHINE_12",
                           {"result": {"ok": ok, "detail": det}})
    return ex, res


ex, res = ex_with("pressed it from (13,16) facing up and nothing came up; its "
                  "other sides are taken: SLOT_MACHINE_11 at (13,14)")
ck("a press beside it that got nothing is a touch",
   res is True and "SLOT_MACHINE_12" in ex._tried_objs.get("GAME_CORNER|1,6", ()))
ex, res = ex_with("no reachable tile adjacent to target")
ck("...an ordinary failure still is not", res is False and not ex._tried_objs)

src = Path("planner/executor.py").read_text()
i = src.index("# ...AND SO DOES A PRESS THAT STOOD BESIDE IT AND GOT NOTHING.")
blk = src[i:i + 1800]
ck("the landing site marks interact and slots on the shim's words",
   'op in ("interact", "slots")' in blk and '"and nothing came up"' in blk
   and '"brought up nothing"' in blk and "_tried_objs.setdefault(_hr, set()).add" in blk)
j = src.index("An interact that never happened leaves the thing UNTOUCHED.")
ck("the failed-interact retraction leaves it standing",
   '"and nothing came up" not in str(r.get("detail") or "")' in src[j:j + 900])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

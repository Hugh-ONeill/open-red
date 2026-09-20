#!/usr/bin/env python3
"""A cross step that names which cell of the edge to use does not crash the
attempt.

The pocket check binds `_pocket` only when the step carries no `skip` of its
own, and the line after the cross reads it unconditionally. So every cross
built from a seam key like "west#skip2" — which explore's own _exit_op
writes through _cross_step_for, and which the model may write itself —
raised UnboundLocalError and killed the whole attempt. Run 28 lost an
attempt of leg 13 to it in Cerulean (2026-09-19); live since 913c9f8,
2026-08-27.

Pinned: both names are bound before the branch that fills them; the skipped
-cell key still becomes a cross with that skip; and the attempt survives a
cross step carrying one. Synthetic."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
ck("a plain seam key crosses without naming a cell",
   ex._cross_step_for("west") == {"op": "cross", "dir": "west"})
ck("a skipped-cell key carries the skip",
   ex._cross_step_for("west#skip2")
   == {"op": "cross", "dir": "west", "skip": 2})

# the two names are bound before the branch that fills them, so the read
# after the cross can never be unbound
src = (ROOT / "planner/executor.py").read_text()
tree = ast.parse(src)


def find(node, want):
    for n in ast.walk(node):
        if isinstance(n, ast.FunctionDef) and n.name == want:
            return n
    return None


fn = find(tree, "_run_traced")
ck("the function is there", fn is not None)
assigns = [n for n in ast.walk(fn)
           if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "_pocket"
                   for t in n.targets)]
reads = [n for n in ast.walk(fn)
         if isinstance(n, ast.Name) and n.id == "_pocket"
         and isinstance(n.ctx, ast.Load)]
ck("_pocket is bound before it is ever read",
   assigns and reads and min(a.lineno for a in assigns)
   < min(r.lineno for r in reads),
   (sorted(a.lineno for a in assigns), sorted(r.lineno for r in reads)))
ck("...outside the branch that only runs without a skip",
   "                _skipped_why = \"\"\n                _pocket = None\n"
   "                if step.get(\"skip\") is None:" in src)
first = min(assigns, key=lambda a: a.lineno)
ck("...its first binding is the outer one, and it is None",
   first.col_offset == 16 and isinstance(first.value, ast.Constant)
   and first.value.value is None,
   (first.lineno, first.col_offset, ast.dump(first.value)[:60]))
ck("the branch that finds a pocket still sets it",
   any(a.col_offset > 16 for a in assigns))

# the whole path: an executor whose cross is refused still returns
crossed = []


class Ex(E.Executor):
    def __init__(self):
        self.explored = {"CERULEAN_CITY|0,0": {}}

    def _where(self, obs):
        return "CERULEAN_CITY|0,0"

    def _send_safe(self, op, **kw):
        crossed.append((op, kw))
        return {"result": {"ok": False, "detail": "no gap there"}}


ck("a cross that names a cell reaches the bridge with that skip",
   (Ex()._cross_step_for("west#skip2") or {}).get("skip") == 2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

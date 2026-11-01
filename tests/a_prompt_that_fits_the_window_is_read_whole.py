#!/usr/bin/env python3
"""Ollama reads a prompt whole as long as it fits num_ctx; only one LONGER
than num_ctx is cut, to half, from the front.

Measured 2026-10-27 on the loaded gemma4:31b at num_ctx 32768, a word
planted at the top and one at the bottom: 10,650 / 17,699 / 24,751 /
31,240-token prompts came back with both words; a ~34k one was cut to
16,387 (= num_ctx/2 + 3) and only the bottom word came back. For two months
the code said the prompt got HALF of num_ctx: author.prompt_guard capped at
NUM_CTX // 2 and printed 1,872 false "IT WILL BE TRUNCATED" / "close to the
cliff" lines into run 69's log, and EVIDENCE_BUDGET was sized to a cliff
that was not there.

Pinned: the guard's cap is the window less the reply's room; a prompt well
under it is not warned about; the overflow signature detector is unchanged
(it was right); the half-of-num_ctx claim is gone from both files."""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import brock_probe as B  # noqa: E402
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


def guard_says(chars):
    buf = io.StringIO()
    with redirect_stdout(buf):
        A.prompt_guard("probe", body="x" * chars)
    return buf.getvalue()


cap = B.NUM_CTX - B.NUM_PREDICT
ck("a prompt at 60% of the window draws no warning (it would have at 24576 // 2)",
   guard_says(int(B.NUM_CTX * 0.6) * 4) == "")
ck("one near the window less the reply's room is warned about",
   "close to the cliff" in guard_says(int(cap * 0.95) * 4))
ck("...and one over it is said to be cut from the front",
   "TRUNCATED FROM THE FRONT" in guard_says((cap + 100) * 4))
ck("the warning names the cap as the window less the reply", f"against a {cap} cap" in guard_says((cap + 100) * 4))
bp = (ROOT / "planner/brock_probe.py").read_text()
au = (ROOT / "planner/author.py").read_text()
ck("the overflow signature detector is unchanged",
   "if (NUM_CTX // 2) <= n <= (NUM_CTX // 2) + 8:" in bp)
ck("the half-of-num_ctx claim is gone from brock_probe",
   "Ollama gives the PROMPT only HALF of num_ctx" not in bp)
ck("...and from the author's guard and budget",
   "cap = brock_probe.NUM_CTX // 2" not in au
   and "Ollama evaluates a prompt at HALF of num_ctx" not in au)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""A long system prompt is sent alone before the round that carries it.

Gemma's sliding window makes the server keep its restore points at the END
of each prompt, and consecutive rounds share only the system prompt, so
every round was read from token 0. A system-prompt-only call (one token of
reply) leaves a restore point where the shared part ends; measured
2026-09-27, rounds 1-2 went from 33.2 s to 28.6 s of wall.

Pinned: a long system prompt is warmed first, with the same model, window
and think setting and a one-token reply; a short one is not; a warm-up that
fails never costs the round; RED_WARM=0 turns it off. Synthetic: no server.
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import brock_probe as B  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


SENT = []
FAIL_WARM = {"on": False}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(req, timeout=None):
    body = json.loads(req.data)
    SENT.append(body)
    if FAIL_WARM["on"] and body["options"]["num_predict"] == 1:
        raise ConnectionRefusedError("server reloading")
    return _Resp(json.dumps({"message": {"content": "{}"},
                             "prompt_eval_count": 100,
                             "eval_count": 1}).encode())


B.urllib.request.urlopen = fake_urlopen
LONG = "rules " * 3000
SHORT = "be brief"
USER = {"role": "user", "content": "where now?"}

SENT.clear()
B._chat_once([{"role": "system", "content": LONG}, USER], "m", think=True,
             temp=0.7)
ck("a long system prompt is sent alone first",
   len(SENT) == 2 and SENT[0]["messages"] == [{"role": "system",
                                                "content": LONG}], SENT[:1])
w, r = (SENT + [{}, {}])[:2]
ck("...with the round's model, window and think setting",
   w.get("model") == r.get("model") == "m"
   and w["options"]["num_ctx"] == r["options"]["num_ctx"] == B.NUM_CTX
   and w.get("think") is True and r.get("think") is True
   and w["options"]["temperature"] == r["options"]["temperature"] == 0.7)
ck("...and a one-token reply", w["options"]["num_predict"] == 1)
ck("the round itself is unchanged",
   r["messages"][-1] == USER and r["options"]["num_predict"] != 1)

SENT.clear()
B._chat_once([{"role": "system", "content": SHORT}, USER], "m")
ck("a short system prompt is not warmed", len(SENT) == 1)

SENT.clear()
FAIL_WARM["on"] = True
out = B._chat_once([{"role": "system", "content": LONG}, USER], "m")
FAIL_WARM["on"] = False
ck("a warm-up that fails never costs the round", out == "{}" and len(SENT) == 2)

SENT.clear()
os.environ["RED_WARM"] = "0"
B._chat_once([{"role": "system", "content": LONG}, USER], "m")
os.environ.pop("RED_WARM")
ck("RED_WARM=0 turns it off", len(SENT) == 1)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

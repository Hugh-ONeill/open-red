#!/usr/bin/env python3
"""A thinking call streams, and its trace is written as it arrives.

A thinking call runs two to three minutes and its trace only existed once it
ended, so a watcher had nothing to show meanwhile (user, 2026-09-28). A
thinking call now streams: its words go to run/thinking_live.txt as they come,
and the streamed lines are put back together as the one reply a non-streamed
call returns.

Pinned: only a thinking call streams; the reassembled reply carries the same
content, trace and accounting the caller always read; the live file is reset
at the start and says "# done" at the end; a live file that cannot be written
never costs the round; a server that ignores stream and sends one object is
read the same. Synthetic: no server.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
TMP = tempfile.mkdtemp()
os.environ["RED_RUN_DIR"] = TMP
os.environ["RED_WARM"] = "0"
import brock_probe as B  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


SENT = []
MODE = {"stream": True}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(req, timeout=None):
    body = json.loads(req.data)
    SENT.append(body)
    if body.get("stream") and MODE["stream"]:
        lines = [{"message": {"role": "assistant", "thinking": "The tree "}, "done": False},
                 {"message": {"role": "assistant", "thinking": "blocks south."}, "done": False},
                 {"message": {"role": "assistant", "content": '{"op": '}, "done": False},
                 {"message": {"role": "assistant", "content": '"go north"}'}, "done": False},
                 {"message": {"role": "assistant", "content": ""}, "done": True,
                  "prompt_eval_count": 62, "eval_count": 9,
                  "prompt_eval_duration": 2e8, "eval_duration": 1e9, "total_duration": 1.3e9}]
        return _Resp(("\n".join(json.dumps(x) for x in lines) + "\n").encode())
    return _Resp(json.dumps({"message": {"content": '{"op": "wait"}',
                                         "thinking": "one piece" if body.get("think") else ""},
                             "prompt_eval_count": 10, "eval_count": 3}).encode())


B.urllib.request.urlopen = fake_urlopen
MSGS = [{"role": "user", "content": "where now?"}]
LIVE = Path(TMP) / B.LIVE_NAME

SENT.clear()
out = B._chat_once(MSGS, "m", think=True)
ck("a thinking call asks the server to stream", SENT and SENT[-1].get("stream") is True)
ck("...and gets back the content a caller always got", out == '{"op": "go north"}', out)
ck("...with the trace and the accounting in LAST",
   B.LAST.get("thinking") == "The tree blocks south." and B.LAST.get("gtok") == 9
   and B.LAST.get("ptok") == 62 and B.LAST.get("tot_s") == 1.3, B.LAST)
live = LIVE.read_text() if LIVE.exists() else ""
ck("the live file holds the trace as it came", "The tree blocks south." in live, live)
ck("...opens with a header and closes with # done",
   live.startswith("# thinking since") and "# done" in live.splitlines()[-1], live)

SENT.clear()
LIVE.write_text("old trace\n")
out = B._chat_once(MSGS, "m")
ck("a call that does not think does not stream", SENT and SENT[-1].get("stream") is False)
ck("...and leaves the live file alone", LIVE.read_text() == "old trace\n")

SENT.clear()
MODE["stream"] = False
out = B._chat_once(MSGS, "m", think=True)
MODE["stream"] = True
ck("a server that sends one object anyway is read the same",
   out == '{"op": "wait"}' and B.LAST.get("thinking") == "one piece", (out, B.LAST))

LIVE.unlink()
os.environ["RED_RUN_DIR"] = "/proc/nope"          # cannot be written
out = B._chat_once(MSGS, "m", think=True)
os.environ["RED_RUN_DIR"] = TMP
ck("a live file that cannot be written never costs the round", out == '{"op": "go north"}', out)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

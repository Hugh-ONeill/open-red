#!/usr/bin/env python3
"""A retry notice from the model client goes to stderr, never stdout.

Callers capture stdout as data: the ladder's already-done sweep reads leg
numbers from author.py's stdout. During an ollama restart the retry line
was printed to stdout, reached the sweep as a "leg number", and
skip_legs.py died on int("[ollama]") (run 36, 2026-10-04). Behavioural:
a chat against a dead port prints nothing to stdout.
"""
import contextlib, io, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import brock_probe as B  # noqa: E402

B.time.sleep = lambda s: None          # no real waits between retries
_url = getattr(B, "OLLAMA", None) or getattr(B, "URL", None)
for name in ("OLLAMA", "OLLAMA_URL", "URL", "BASE"):
    if isinstance(getattr(B, name, None), str) and "http" in getattr(B, name):
        setattr(B, name, "http://127.0.0.1:9/api/chat" if "chat" in getattr(B, name)
                else "http://127.0.0.1:9")
out, err = io.StringIO(), io.StringIO()
raised = False
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    try:
        B.chat([{"role": "user", "content": "hi"}], "nope", retries=1)
    except Exception:
        raised = True
checks = [
    ("the call fails against a dead port", raised),
    ("nothing reaches stdout", "[ollama]" not in out.getvalue()),
    ("the retry notice reaches stderr", "[ollama]" in err.getvalue()),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)

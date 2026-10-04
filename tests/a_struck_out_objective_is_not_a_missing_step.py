#!/usr/bin/env python3
"""An objective the run struck out is not offered back as a missing step.

Run 36, 2026-10-04: "Obtain the Coin Case from the old man in Celadon
City" was voided by the model's own account, then the missing rung
inserted the same line before the Secret Key leg; it ran dry twice and
the chain stopped on it. Behavioural, with the model stood in for: the
same proposal against the same void record is turned down with the
model's own reason, and the rung asks again.
"""
import json, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

COIN = "Obtain the Coin Case from the old man in Celadon City"
WHY = ("The run has already visited the roof house in Celadon Mansion "
       "(EVENT_GOT_EEVEE) and interacted with the old man there, but the "
       "Coin Case is not given by an old man")
d = tempfile.mkdtemp()
(Path(d) / "run").mkdir()
(Path(d) / "run/outline_void").write_text(COIN + "\t" + WHY + "\n")
os.chdir(d)

asked = []
def fake(msgs, model, *a, **k):
    asked.append(msgs[-1]["content"])
    if len(asked) == 1:
        return json.dumps({"insert": COIN, "why": "the key is bought with coins"})
    return json.dumps({"insert": "none", "why": "nothing else"})
A.chat_json = fake

got = A.check_missing("Retrieve the Secret Key from the Game Corner",
                      [(31, "Retrieve the Secret Key from the Game Corner"),
                       (32, "Reach Saffron City")],
                      "CELADON_CITY", "stand-in", tries=2)
checks = [
    ("the struck-out objective is not inserted", got == ""),
    ("the rung asked again", len(asked) == 2),
    ("...and told the model it had struck it out, in its own words",
     len(asked) == 2 and "you struck this objective out earlier" in asked[1]
     and "roof house" in asked[1]),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)

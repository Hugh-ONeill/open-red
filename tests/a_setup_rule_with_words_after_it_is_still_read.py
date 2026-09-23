#!/usr/bin/env python3
"""A setup-rule answer that says one more thing after its object is still
an answer.

Run 34, 2026-09-23: the reply for KADABRA's RECOVER carried its rule and
then a second line, and the greedy brace match — from the first "{" to
the last "}" — handed json.loads both ("Extra data: line 2 column 1 (char
369)"). The error row was written, the move was skipped, and the party's
one healing move played the whole run under no rule at all.

The first complete object in the reply is the answer; what follows it is
not, and does not spoil it. The same greedy match read the reply of every
other question the executor asks — the buy, the teach, the stone, the
name, the yes/no, the offer, the playback — twelve sites, one reader now.

Pinned: the first object is read whatever follows it — a sentence, a
second object, a stray brace, words before it; no object is no answer;
the setup question keeps a rule so answered and writes no error; no
greedy match on a reply is left anywhere in the executor. Synthetic."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


F = E.Executor._first_object
ck("an object followed by a sentence is read",
   F('{"rule": null, "why": "x"}\nI hope this helps.') == {"rule": None, "why": "x"})
ck("...and one followed by a second object is the first",
   F('{"a": 1} {"b": 2}') == {"a": 1})
ck("...and one followed by a stray brace", F('{"a": 1}\n}') == {"a": 1})
ck("...and one preceded by words", F('Sure: {"a": 1}') == {"a": 1})
ck("...and one whose sentence after it has braces of its own",
   F('{"a": 1} (the {b} is a placeholder)') == {"a": 1})
ck("a broken brace before the real object is skipped",
   F('{not json} {"a": 1}') == {"a": 1})
ck("no object is no answer", F("nothing here") is None and F("") is None)
ck("an array is not an object", F("[1, 2]") is None)


def mv(i, power, mtype="NORMAL", pp=20):
    return {"id": i, "power": power, "type": mtype, "max_pp": pp, "pp": pp}


PARTY = [{"species": "KADABRA", "level": 31, "hp": 70, "max_hp": 70,
          "types": ["PSYCHIC"],
          "moves": [mv("CONFUSION", 50, "PSYCHIC"), mv("RECOVER", 0, "PSYCHIC")]}]
tmp = Path(tempfile.mkdtemp(prefix="setup_"))
E.RUN = tmp
E.set_active_spec(dict(B.DEFAULT_SPEC))
REPLY = ('{"why": "it heals a third", "rule": {"move": "RECOVER", '
         '"max_uses": 3, "min_hp_frac": 0.5}, "before": null}\n\n'
         'I have kept the rule simple. {"note": "revise later"}')
E.brock_probe.chat = lambda msgs, m, **kw: REPLY
ex = E.Executor.__new__(E.Executor)
ex.logf = io.StringIO()
ex.t0 = time.time()
ex.model = "m"
ex._ask_setup_rules({"party": PARTY})
rows = [json.loads(l) for l in ex.logf.getvalue().splitlines()]
book = json.loads((tmp / "setup_rules.json").read_text()) \
    if (tmp / "setup_rules.json").exists() else {}
ck("the rule so answered is kept",
   isinstance((book.get("RECOVER") or {}).get("rule"), dict)
   and book["RECOVER"]["rule"].get("max_uses") == 3, book)
ck("...and no error is written",
   not any(r["kind"] in ("setup_rule_error", "setup_rule_unparsed") for r in rows),
   [r["kind"] for r in rows])

SRC = (ROOT / "planner/executor.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
i = _code.index("def _ask_setup_rules(")
j = _code.index("\n    def ", i + 10)
ck("the question reads the first object, not a greedy brace match",
   "Executor._first_object(reply" in _code[i:j]
   and 'r"\\{.*\\}"' not in _code[i:j])
ck("...and no greedy match on a reply is left anywhere in the executor",
   '_re.search(r"\\{.*\\}", reply' not in _code
   and _code.count("_first_object(reply") >= 12, _code.count("_first_object(reply"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

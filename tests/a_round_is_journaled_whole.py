#!/usr/bin/env python3
"""Every escalation prompt is journaled whole, and tools/page_ablation.py can
take it apart and put it back.

The journal kept the page capped and the echo, never the observation, atlas,
feedback or sketch, so no round could be asked again as it was; measuring
which page section changes a decision needs exactly that (TODO, 2026-09-30).

Runs in a throwaway bridge dir; no model is called.
"""
from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["RED_BRIDGE_DIR"] = tempfile.mkdtemp()
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tools"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import executor as E  # noqa: E402
import page_ablation as P  # noqa: E402

ck("the journal goes to the bridge dir, not the live run",
   str(E.RUN).startswith(os.environ["RED_BRIDGE_DIR"]), E.RUN)
x = object.__new__(E.Executor)
x.model = "m"
x._logged = []
x.log = lambda kind, **kw: x._logged.append((kind, kw))
USER = ("SUBGOAL: Get the Card Key\nDONE_WHEN: {\"has_item\": {\"CARD_KEY\": 1}}\n"
        "WHERE YOU STAND: SILPH_CO_5F|20,0 — indoors\n 1. explore — walk\n"
        " 2. door (5,0)\nWHAT YOU ARE CARRYING: BICYCLE x1, CARD_KEY x0\n"
        "THE PRINTED MAP OF KANTO (every road)\n  ROUTE_9 -> ROUTE_10\n"
        "ATLAS (map edges and doors you have observed so far): a->b\n"
        "FEEDBACK FROM YOUR LAST MACRO:\ninteract(x): FAILED\n"
        "CURRENT_OBSERVATION: {\"map\":{\"id\":\"SILPH_CO_5F\"}}\n"
        "Author the op-list macro to achieve DONE_WHEN from here.")
sg = {"id": "get_card_key", "done_when": {"has_item": {"CARD_KEY": 1}}}
obs = {"map": {"id": "SILPH_CO_5F", "region": "20,0"}}
x._journal_prompt(sg, 3, obs, "SYSTEM TEXT", USER,
                  '{"plan":"p","ops":[{"op":"interact","name":"ITEM_SILPH_CO_5F_21_16"}]}', False)
x._journal_prompt(sg, 4, obs, "SYSTEM TEXT", USER + " ", '{"ops":[{"op":"explore"}]}', True)
pf = E.RUN / "prompts.jsonl.gz"
recs = P.load(pf) if pf.exists() else []
ck("each round is one record, appended", len(recs) == 2, len(recs))
ck("...the user prompt whole, the reply, the round and where",
   recs and recs[0]["user"] == USER and recs[0]["round"] == 3
   and recs[0]["at"] == "SILPH_CO_5F|20,0" and recs[1]["think"] is True)
ck("...and the system prompt once, by its hash",
   recs and (E.RUN / "prompt_sys" / f"{recs[0]['sys']}.txt").read_text() == "SYSTEM TEXT"
   and len(list((E.RUN / "prompt_sys").iterdir())) == 1)
ck("no journal error", not x._logged, x._logged)

secs = P.split_sections(USER)
ck("the page splits and joins back to the same bytes", "".join(t for _l, t in secs) == USER)
labs = [l for l, _t in secs]
ck("the prompt's frame is its own sections",
   labs == ["SUBGOAL", "DONE_WHEN", "WHERE YOU STAND", "WHAT YOU ARE CARRYING",
            "THE PRINTED MAP OF KANTO", "ATLAS", "FEEDBACK FROM YOUR LAST MACRO",
            "CURRENT_OBSERVATION", "AUTHOR THE OP-LIST"], labs)
vs = P.variants(USER)
ck("the question and the observation are never taken out",
   not any(l in ("SUBGOAL", "DONE_WHEN", "CURRENT_OBSERVATION", "AUTHOR THE OP-LIST")
            for l, _k, _t in vs))
rm = {l: t for l, k, t in vs if k == "remove"}
ck("taking a section out leaves the rest as it was",
   rm["WHAT YOU ARE CARRYING"] == USER.replace("WHAT YOU ARE CARRYING: BICYCLE x1, CARD_KEY x0\n", ""))
top = {l: t for l, k, t in vs if k == "top"}
ck("moving one up puts it right after the question",
   top["THE PRINTED MAP OF KANTO"].split("\n")[2].startswith("THE PRINTED MAP OF KANTO"))
ck("a section already first after the question is not 'moved'", "WHERE YOU STAND" not in top)
ck("a decision is its first ops, by kind and aim",
   P.signature(recs[0]["reply"]) == ("interact:ITEM_SILPH_CO_5F_21_16",)
   and P.signature("no json") == ("unparsed",))

with tempfile.TemporaryDirectory() as td:
    out = Path(td)
    rows = [{"rec": 0, "why": "pivot", "label": "(unchanged)", "kind": "base", "k": k,
             "sig": ["explore:"]} for k in range(3)]
    rows += [{"rec": 0, "why": "pivot", "label": "WHERE YOU STAND", "kind": "remove", "k": k,
              "sig": ["interact:X"]} for k in range(3)]
    rows += [{"rec": 0, "why": "pivot", "label": "ATLAS", "kind": "remove", "k": k,
              "sig": ["explore:"]} for k in range(3)]
    (out / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    rep = P.report(out)
lines = rep.splitlines()
ck("the report ranks a section that moved the decision first",
   lines[3].startswith("WHERE YOU STAND") and "+1.00" in lines[3], rep)
ck("...and one that moved nothing at zero", any(l.startswith("ATLAS") and "+0.00" in l for l in lines), rep)

r = subprocess.run([sys.executable, str(ROOT / "tools/page_ablation.py"), "--prompts", str(pf),
                    "--sys-dir", str(E.RUN / "prompt_sys"), "--rounds", "0",
                    "--out", str(ROOT / "run/ablation_test")], capture_output=True, text=True)
ck("it will not write under run/", r.returncode != 0 and "must not be under" in (r.stdout + r.stderr)
   and not (ROOT / "run/ablation_test").exists(), r.stdout[-300:] + r.stderr[-300:])
fd = (ROOT / "fresh_discovery.sh").read_text()
ck("a fresh chain archives the last chain's prompts", 'mv run/prompts.jsonl.gz' in fd)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

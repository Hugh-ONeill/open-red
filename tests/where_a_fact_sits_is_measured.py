#!/usr/bin/env python3
"""Every block of the page is measured: where it sits, how big it is, and
how often the thing the run went on to do was named in it.

This project measured position once, in 2026-08-17: the first-listed
option is taken 54% of the time against a chance rate near 8%, and the
median position of whatever the run acted on is 14% of the way through the
prompt. It has never measured the blocks themselves, and the page has been
assembled by addition ever since (user, 2026-09-21: "it was something we
added in pretty early on so being kinda scattered by the additional gruft
over the course of the project makes sense ... we should try to see if we
can measure where we put information more").

Run 27 lost to BROCK ten times, five of them inside ninety seconds, and the
page said so at 95-99% while BROCK's own name was at 4%.

Pinned: a block starts at a shouted header at a line start; a header with
no body is reported with its size so a lead-in cannot read as a dead block;
what a macro acted on is the things it points AT, never the op name; a
block is credited when it names one of those, and credited separately when
it is the ONLY block that names it; positions and sizes are medians; the
goal shapes group the predicates the outline actually writes; and nothing
here reads or writes a prompt. Synthetic."""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import blocks as BK  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


PAGE = ("WHERE YOU STAND: PALLET_TOWN|10,0, an edge on its north side.\n"
        "WAYS OUT OF HERE — one of these:\n"
        "ROOMS WHERE SOMEBODY IS WORTH ANOTHER WORD\n"
        "  OAKS_LAB|4,1: OAKSLAB_OAK1 has not been spoken to.\n"
        "MACHINES YOU CARRY THAT NOBODY IN YOUR PARTY KNOWS: TM_DIG.\n")
b = BK.split_blocks(PAGE)
ck("a block starts at a shouted header on its own line",
   [h for h, _s, _e in b] == ["WHERE YOU STAND", "WAYS OUT OF HERE",
                              "ROOMS WHERE SOMEBODY IS WORTH ANOTHER WORD",
                              "MACHINES YOU CARRY THAT NOBODY IN YOUR PARTY KNOWS"],
   [h for h, _, _ in b])
ck("...and runs to the next header",
   PAGE[b[2][1]:b[2][2]].strip().endswith("has not been spoken to."))
ck("a lead-in with no body is short, which is how it is told apart",
   b[1][2] - b[1][1] < 40 and b[2][2] - b[2][1] > 60)
ck("a shout inside a sentence is not a header",
   [h for h, _, _ in BK.split_blocks("you have no CUT and no SURF here\n")] == [])

ck("what a macro acted on is what it points at",
   sorted(BK.acted_on([{"op": "go", "to": "ROUTE_4"},
                       {"op": "interact", "name": "OAKSLAB_OAK1"}]))
   == ["OAKSLAB_OAK1", "ROUTE_4"])
ck("...a cell counts, written the way a page writes one",
   BK.acted_on([{"op": "walk_to", "x": 10, "y": 8}]) == ["10,8"])
ck("...and the op name never does",
   BK.acted_on([{"op": "explore", "until": "warp"}]) == [])

ck("the goal shapes group what the outline actually writes",
   BK.goal_shape("map:PEWTER_CITY") == "place"
   and BK.goal_shape("party_min_level:12") == "party"
   and BK.goal_shape("has_species:ABRA") == "party"
   and BK.goal_shape("item:POKE_BALL") == "thing"
   and BK.goal_shape("") == "other")

# ---- a journal of three decisions, worked end to end -------------------
def row(kind, **kw):
    return json.dumps(dict(kind=kind, **kw))


tmp = Path(tempfile.mkdtemp(prefix="blocks_")) / "j.jsonl"
tmp.write_text("\n".join([
    row("escalate_context", target="map:ROUTE_4", memory=PAGE),
    row("escalate_proposal", macro=[{"op": "go", "to": "OAKS_LAB"}]),
    row("escalate_context", target="party_min_level:12", memory=PAGE),
    row("escalate_proposal", macro=[{"op": "interact", "name": "OAKSLAB_OAK1"}]),
    row("escalate_context", target="map:ROUTE_4", memory=PAGE),
    row("escalate_proposal", macro=[{"op": "use_item", "item": "TM_DIG"}]),
]) + "\n")
ck("a context is paired with the proposal that answered it",
   len(BK.pairs([tmp])) == 3)

buf = io.StringIO()
with redirect_stdout(buf):
    BK.main([str(tmp), "--min", "1"])
out = buf.getvalue()
line = {l.split("  ")[-1].strip(): l for l in out.splitlines() if "%" in l}
ck("the table counts every decision", "3 paired decisions" in out)
ck("a block that names what was done is credited",
   "67%" in line.get("ROOMS WHERE SOMEBODY IS WORTH ANOTHER WORD", ""),
   line.get("ROOMS WHERE SOMEBODY IS WORTH ANOTHER WORD"))
ck("...and a block that is the only place it appears is credited apart",
   line.get("MACHINES YOU CARRY THAT NOBODY IN YOUR PARTY KNOWS", "").count("33%") == 2,
   line.get("MACHINES YOU CARRY THAT NOBODY IN YOUR PARTY KNOWS"))
ck("a block nothing is ever done with reads zero",
   "    0%" in line.get("WAYS OUT OF HERE", "x"),
   line.get("WAYS OUT OF HERE"))
ck("the blocks are listed where they sit, earliest first",
   out.index("WHERE YOU STAND") < out.index("MACHINES YOU CARRY"))
ck("each block's size is printed beside it",
   "chars" in out)

buf = io.StringIO()
with redirect_stdout(buf):
    BK.main([str(tmp), "--min", "1", "--by-goal"])
g = buf.getvalue()
ck("the arrangement can be read against what the step wants",
   "WHERE EACH BLOCK SITS, BY WHAT THE STEP WANTS" in g
   and "place" in g and "party" in g)

buf = io.StringIO()
with redirect_stdout(buf):
    BK.main([str(tmp), "--block", "ROOMS WHERE SOMEBODY"])
one = buf.getvalue()
ck("one block can be read round by round",
   "3 of 3 pages carried it" in one and "map:ROUTE_4" in one)

SRC = (ROOT / "planner/blocks.py").read_text()
ck("it never calls a model",
   "brock_probe" not in SRC and "chat(" not in SRC and "ollama" not in SRC)
ck("...and never writes to a run", "write_text" not in SRC and "open(" not in SRC.replace("Path(p).open(", ""))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

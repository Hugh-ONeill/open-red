#!/usr/bin/env python3
"""An outline's party legs can be asked again over its story legs, on
their own, and the result lands beside --out with its sidecars.

2026-09-24. The party question was fixed twice (no type as its example;
what each leg is for) after the outline the judge had picked was drawn.
Its story legs were sound; its party legs took Squirtle thirty of thirty
asks of the starter question. Redrawing the whole list rolls the story
dice again for a fault that sits in one pass, so `--outline-reupkeep`
reruns that pass alone: story kept in order, old party legs set aside,
new ones placed by the model's own answer, upkeep and notes written
beside the output, the stages sidecar carried over.

Pinned: the story legs are kept, in order; the old party legs are gone;
the new ones are where the answer put them; the upkeep sidecar names
them; a purpose rides in the notes; the stages sidecar is copied; the
live plans/outline.upkeep is not touched; the judge's verdict is printed;
the switch needs both paths. Synthetic."""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import brock_probe  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


d = Path(tempfile.mkdtemp())
src = d / "cand.txt"
src.write_text("\n".join([
    "Choose a starter Pokemon", "Reach Pewter City",
    "the party holds a WATER or GRASS type", "every party member is at least level 12",
    "Defeat Brock for the Boulder Badge", "Reach Cerulean City",
    "the party holds a PSYCHIC or WATER type", "Defeat Misty for the Cascade Badge"]) + "\n")
src.with_suffix(".stages").write_text("Early\tChoose a starter Pokemon\nEarly\tReach Pewter City\n")
REPLY = json.dumps([
    {"item": "the party holds a FIGHTING or GRASS type", "after": 2, "for": "3"},
    {"item": "every party member is at least level 12", "after": 2, "for": "Brock's Onix"}])
calls = []


def chat(msgs, model, **kw):
    calls.append(msgs[1]["content"])
    return REPLY if len(calls) == 1 else "[]"


brock_probe.chat = chat
live = ROOT / "plans/outline.upkeep"
before = live.read_text() if live.exists() else None
out = d / "reup.txt"
buf = io.StringIO()
with redirect_stdout(buf):
    legs = A.outline_reupkeep(src, out, "Become the Champion", "m")
text = buf.getvalue()
got = [l for l in out.read_text().splitlines() if l.strip()]
ck("the story legs are kept, in order",
   [l for l in got if not A._UPKEEP_SHAPE.match(l)]
   == ["Choose a starter Pokemon", "Reach Pewter City", "Defeat Brock for the Boulder Badge",
       "Reach Cerulean City", "Defeat Misty for the Cascade Badge"], got)
ck("the old party legs are gone",
   "the party holds a WATER or GRASS type" not in got
   and "the party holds a PSYCHIC or WATER type" not in got, got)
ck("...and the question was asked over the story alone",
   "WATER or GRASS" not in calls[0] and "Reach Pewter City" in calls[0], calls[0][:300])
ck("the new ones are where the answer put them, both after leg 2",
   {got.index("the party holds a FIGHTING or GRASS type"),
    got.index("every party member is at least level 12")} == {2, 3}, got)
ck("the upkeep sidecar names them, beside the output",
   set((out.with_suffix(".upkeep")).read_text().splitlines())
   == {"the party holds a FIGHTING or GRASS type", "every party member is at least level 12"})
ck("a purpose rides in the notes", "for: 3" in out.with_suffix(".notes").read_text())
ck("the stages sidecar is carried over",
   out.with_suffix(".stages").read_text().startswith("Early\tChoose a starter Pokemon"))
ck("the live upkeep list is not touched",
   (live.read_text() if live.exists() else None) == before)
ck("the judge's verdict is printed", "[reupkeep] judge:" in text, text)
ck("...and what was set aside is said: the level leg is a party leg too",
   "3 party leg(s) set aside" in text, text)

SRC = (ROOT / "planner/author.py").read_text()
ck("the switch needs both paths",
   '"--outline-reupkeep"' in SRC and "needs --outline-path and --out" in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

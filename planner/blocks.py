#!/usr/bin/env python3
"""WHERE A FACT SITS, AND WHETHER ANYTHING IS EVER DONE WITH IT.

Measured 2026-08-17 over 3,535 decisions: the first-listed option is taken
54% of the time against a chance rate near 8%, and the median position of
whatever the run acted on is 14% of the way through the prompt. So a fact
at 60% depth is close to not having been said at all.

That was measured once, about one block. This measures EVERY block, over
any journal: where it sits, how often it is there, and how often the thing
the run went on to do was named in it. A block nothing is ever acted on is
either in the dead zone or not worth its tokens, and the two look the same
from inside the loop — which is the firehose question made answerable
(user, 2026-08-17: "we're shooting info at it with a firehose, but i dont
know a princibled way to do it otherwise").

WHAT SET IT OFF. Run 27 lost to BROCK ten times, five of them inside ninety
seconds, walking back and pressing him again with nothing healed, nothing
trained and no level gained. The page said so: "THIS STEP HAS BLACKED OUT 5
TIME(S)", "WHAT BEAT YOU", "something about the plan has to change". It
said so at 95-99% of the prompt, while BROCK's own name was at 4% (user,
2026-09-21: "it was something we added in pretty early on so being kinda
scattered by the additional gruft over the course of the project makes
sense ... we should try to see if we can measure where we put information").

NO MODEL CALLS. Every decision is already paired in the journal: an
`escalate_context` carries the exact page, and the `escalate_proposal`
after it carries the macro the model wrote.

  blocks.py run/executor_log.jsonl            # one run
  blocks.py run/executor_log*.jsonl --by-goal # split by what the step wants
  blocks.py ... --block "HAS BLACKED OUT"     # one block, with its rounds
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

# A BLOCK STARTS AT A SHOUTED HEADER. The page is assembled from prose
# written over months, and the one thing every piece has in common is that
# it announces itself in capitals. Anything shorter than eight characters
# is a word in a sentence (HP, CUT, YES), not a heading.
HEAD = re.compile(r"^([A-Z][A-Z0-9 ,'’\-/()\.]{7,}?)(?::| —|\.|,|$)", re.M)

# What a macro ACTED ON: the values worth looking for in the page. An op
# name alone is not it — every page names `explore` — so this reads the
# things a step points at, which is what a block can offer.
def acted_on(macro) -> list:
    out = []
    for step in (macro if isinstance(macro, list) else []):
        if not isinstance(step, dict):
            continue
        for k in ("to", "name", "item", "map", "dir", "species", "clerk"):
            v = step.get(k)
            if isinstance(v, str) and len(v) > 2:
                out.append(v)
        if step.get("x") is not None and step.get("y") is not None:
            out.append(f"{step['x']},{step['y']}")
    return out


def split_blocks(mem: str) -> list:
    """[(header, start, end)] over the page, in order."""
    hits = [(m.group(1).strip(), m.start()) for m in HEAD.finditer(mem)]
    out = []
    for i, (h, s) in enumerate(hits):
        e = hits[i + 1][1] if i + 1 < len(hits) else len(mem)
        out.append((h, s, e))
    return out


def pairs(paths) -> list:
    """[(context row, the proposal that answered it)] across journals."""
    out = []
    for p in paths:
        rows = []
        for line in Path(p).open(errors="ignore"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
        pending = None
        for r in rows:
            k = r.get("kind")
            if k == "escalate_context":
                pending = r
            elif k == "escalate_proposal" and pending is not None:
                out.append((pending, r))
                pending = None
    return out


def goal_shape(target: str) -> str:
    """The KIND of thing a step wants, which is what an arrangement would
    have to key on if one arrangement does not fit them all."""
    t = str(target or "")
    head = t.split(":", 1)[0]
    return {"map": "place", "area": "place",
            "item": "thing", "has_item": "thing",
            "party_size": "party", "party_min_level": "party",
            "slot_level": "party", "party_type": "party",
            "has_species": "party", "party_healthy": "party",
            "dex_owned": "party",
            "flag": "deed", "event": "deed"}.get(head, head or "other")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--by-goal", action="store_true",
                    help="split the table by what the step wants")
    ap.add_argument("--block", default="",
                    help="report one block's rounds instead of the table")
    ap.add_argument("--min", type=int, default=8,
                    help="drop blocks seen fewer than this many times")
    a = ap.parse_args(argv)

    data = pairs(a.logs)
    if not data:
        print("no paired decisions in those journals")
        return 1

    if a.block:
        n = 0
        for ctx, prop in data:
            mem = ctx.get("memory") or ""
            i = mem.find(a.block)
            if i < 0:
                continue
            n += 1
            if n <= 20:
                print(f"{i / max(1, len(mem)):5.0%} of {len(mem):6d}  "
                      f"{str(ctx.get('target'))[:26]:28s} "
                      f"{json.dumps(prop.get('macro'))[:70]}")
        print(f"\n{n} of {len(data)} pages carried it")
        return 0

    # header -> {shape: [positions]}, and how often it named what was done
    seen: dict = {}
    hit: dict = {}
    sole: dict = {}
    size: dict = {}
    for ctx, prop in data:
        mem = ctx.get("memory") or ""
        if not mem:
            continue
        shape = goal_shape(ctx.get("target"))
        blocks = split_blocks(mem)
        want = acted_on(prop.get("macro"))
        # WHICH BLOCK GETS THE CREDIT. Two readings, because they answer
        # different questions. `names` is every block the acted-on thing
        # appears in — is this block ever ABOUT what gets done. `only` is
        # the blocks that are the sole place it appears — without this
        # block, would the run have had to find that thing somewhere else.
        # Crediting the first block alone made the table measure nothing
        # but what happens to be printed at the top.
        names, where = set(), {}
        for w in want:
            for h, s, e in blocks:
                if w in mem[s:e]:
                    names.add(h)
                    where.setdefault(w, set()).add(h)
        only = {next(iter(hs)) for hs in where.values() if len(hs) == 1}
        for h, s, e in blocks:
            seen.setdefault(h, {}).setdefault(shape, []).append(
                s / max(1, len(mem)))
            size.setdefault(h, []).append(e - s)
            if h in names:
                hit[h] = hit.get(h, 0) + 1
            if h in only:
                sole[h] = sole.get(h, 0) + 1

    rows = []
    for h, byshape in seen.items():
        pos = [p for v in byshape.values() for p in v]
        if len(pos) < a.min:
            continue
        rows.append((statistics.median(pos), h, len(pos),
                     hit.get(h, 0) / len(pos),
                     sole.get(h, 0) / len(pos),
                     statistics.median(size.get(h, [0])), byshape))
    rows.sort()

    print(f"{len(data)} paired decisions from {len(a.logs)} journal(s)\n")
    # A HEADER WITH NO BODY IS A SENTENCE, NOT A BLOCK: "WAYS OUT OF
    # HERE — ... through one of these:" is a lead-in, and everything it
    # leads into is filed under the header on the next line. The size says
    # which is which, and a one-line intro reading 0% means nothing.
    print(f"{'where':>6}  {'seen':>5}  {'chars':>6}  {'names it':>8}  "
          f"{'only':>5}  block")
    for med, h, n, rate, srate, sz, byshape in rows:
        print(f"{med:6.0%}  {n:5d}  {sz:6.0f}  {rate:8.0%}  {srate:5.0%}  "
              f"{h[:52]}")

    if a.by_goal:
        shapes = sorted({s for _m, _h, _n, _r, _o, _z, b in rows for s in b})
        print(f"\nWHERE EACH BLOCK SITS, BY WHAT THE STEP WANTS\n")
        print(f"{'block':44s} " + " ".join(f"{s[:9]:>9}" for s in shapes))
        for med, h, n, rate, srate, sz, byshape in rows:
            cells = []
            for s in shapes:
                v = byshape.get(s)
                cells.append(f"{statistics.median(v):9.0%}" if v else " " * 9)
            print(f"{h[:44]:44s} " + " ".join(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())

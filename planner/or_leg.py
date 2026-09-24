#!/usr/bin/env python3
"""AN "OR" HELD ON ARRIVAL STILL GETS ONE TRY AT ITS OTHER HALF.

"the party holds a WATER or GRASS type" is done the moment either is held,
so with a Bulbasaur in the party it was crossed off at the boundary and
nothing was caught; with a Squirtle, every "X or WATER" leg on the list
went the same way, which is half the type legs the outline author writes
(2026-09-24, user: "it satisfies all those catch goals by picking squirt at
the start which would prevent any of the non-water types from being
caught ... kinda have to do it if we have half the list already fulfilled
by squirtle").

So when the chain finds such a leg already accomplished, it reads which
half the party holds and which it does not, and runs ONE non-fatal attempt
at the other half — "the party holds a GRASS type", the model's own words
minus the half it has — before crossing the leg off, which it does either
way. A scheduling rule about party building, nothing told to the model:
what to catch, and whether, stays the plan's.

  or_leg.py "the party holds a WATER or GRASS type"            # prints the other half, or nothing
  or_leg.py --record LEG BONUS                                  # journal row for the attempt

ASKED FIRST (user, 2026-09-24: "half budget and ask first"). The try at
the other half ran unasked: run of record 3 beat Brock inside it, the gym
its "FIGHTING or GRASS" leg was for, and then hunted a Mankey on Route 2
for the rest of a full attempt. So before the plan is written, ask() puts
the leg, the half held, the half missing and what the model wrote the leg
was for in front of it, with where the run stands and what is ahead, and
the model says whether the try is still worth making. Its call, its
words; a reply that cannot be read keeps the try. author.py asks when the
plan it is writing is a bonus plan (leg_NN_bonus_*.json), and the
executor gives that plan half a budget.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

OBS = Path("run/obs.json")
JOURNAL = Path("run/executor_log.jsonl")
NOTES = Path("plans/outline.notes")
AUTHORED = Path("plans/outline.authored")
UPKEEP = Path("plans/outline.upkeep")
OUTLINE = Path("plans/outline.txt")
PROGRESS = Path("run/outline_leg")
LEG = re.compile(r"^the party holds an? ([A-Z]+(?: or [A-Z]+)+) type$")


def held_types(obs: dict | None) -> set:
    out = set()
    for mon in ((obs or {}).get("party") or []):
        for t in (mon.get("types") or []):
            out.add(str(t).upper())
    return out


def missing_branch(leg: str, held: set) -> str:
    """The leg with the held half removed, or "" when the leg is not an
    "or" type leg, holds none of its types yet (not accomplished, so not
    this rule's), or holds every one of them."""
    m = LEG.match(str(leg or "").strip())
    if not m:
        return ""
    types = m.group(1).split(" or ")
    have = [t for t in types if t in held]
    want = [t for t in types if t not in held]
    if not have or not want:
        return ""
    art = "an" if want[0][0] in "AEIOU" else "a"
    return f"the party holds {art} {' or '.join(want)} type"


def _lines(path: Path) -> list:
    try:
        return [l.strip() for l in path.read_text().splitlines() if l.strip()]
    except OSError:
        return []


def purpose(leg: str) -> str:
    """What the outline pass said this leg was for, in its words.

    The pass numbered the STORY legs it was shown (the banked outline minus
    its party legs) and answers "for: 5"; that number is stale the moment
    the live outline gains or loses a leg (run of record 3 lost "Reach
    Viridian City" before leg 5), so it is read against the banked list it
    was written against. A number that list does not have is left as said."""
    note = ""
    for l in _lines(NOTES):
        k, _, v = l.partition("\t")
        if k.strip() == leg.strip():
            note = v.strip()
            break
    m = re.fullmatch(r"for:\s*(?:leg\s*)?(\d+)\.?", note, re.I)
    if not m:
        return note[4:].strip() if note.lower().startswith("for:") else note
    up = set(_lines(UPKEEP))
    story = [l for l in _lines(AUTHORED) if l not in up]
    n = int(m.group(1))
    return story[n - 1] if 1 <= n <= len(story) else note


ASK_SYS = """You are playing Pokemon Red, working down an outline you wrote.

One objective on it is already true: the party holds one of the types it \
names. That objective counts as done either way. Before moving on there is \
room for ONE optional attempt, on a shorter budget than a normal step, at \
the type it names that the party does not hold. It is optional: it is \
worth making only if it still serves something ahead of you.

Decide whether to make that attempt now. Reply with JSON only:
{"why": "one or two sentences", "try": true or false}"""


def ask(leg: str, bonus: str, start: str, model: str) -> tuple:
    """(try it?, why) — the model's call. An unreadable reply keeps the try."""
    import brock_probe
    held = sorted(held_types(_obs()))
    _w = re.match(r"^the party holds an? ([A-Z]+(?: or [A-Z]+)*) type$",
                  missing_branch(leg, set(held)) or bonus)
    wants = _w.group(1) if _w else bonus
    lines = _lines(OUTLINE)
    try:
        at = int(PROGRESS.read_text().strip() or 0)
    except (OSError, ValueError):
        at = 0
    ahead = lines[at:at + 8]
    why_leg = purpose(leg)
    body = (f"THE OBJECTIVE: {leg}\n"
            f"ALREADY TRUE: the party holds {' and '.join(t for t in held if t in leg.split()) or 'one of them'}.\n"
            f"THE OPTIONAL ATTEMPT: catch {'an' if wants[:1] in 'AEIOU' else 'a'} {wants} type.\n"
            + (f"WHEN YOU WROTE THE OUTLINE YOU SAID THIS OBJECTIVE WAS FOR: {why_leg}\n"
               if why_leg else "")
            + f"\nWHERE THE RUN STANDS: {start}\n"
            + ("\nTHE NEXT OBJECTIVES ON YOUR OUTLINE:\n"
               + "\n".join(f"  {at + 1 + i}. {l}" for i, l in enumerate(ahead))
               if ahead else ""))
    try:
        reply = brock_probe.chat([{"role": "system", "content": ASK_SYS},
                                  {"role": "user", "content": body}], model)
    except Exception as e:          # noqa: BLE001 — a failed ask keeps the try
        return True, f"(the question could not be asked: {e})"
    ans = _first_object(reply or "")
    if not isinstance(ans, dict) or not isinstance(ans.get("try"), bool):
        return True, f"(no readable answer: {str(reply)[:160]!r})"
    return ans["try"], " ".join(str(ans.get("why") or "").split())[:300]


def _first_object(text: str):
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                return dec.raw_decode(text, i)[0]
            except ValueError:
                continue
    return None


def _obs() -> dict:
    try:
        return json.loads(OBS.read_text() or "{}")
    except (OSError, ValueError):
        return {}


def last_bonus_leg(bonus: str) -> str:
    """The leg the chain just recorded this bonus for (--record's row)."""
    leg = ""
    try:
        for l in JOURNAL.read_text().splitlines()[-400:]:
            if '"or_leg_bonus"' in l:
                r = json.loads(l)
                if r.get("bonus") == bonus:
                    leg = r.get("leg") or leg
    except (OSError, ValueError):
        pass
    return leg


def record_ask(leg: str, bonus: str, go: bool, why: str) -> None:
    try:
        with JOURNAL.open("a") as f:
            f.write(json.dumps({"t": time.time(), "kind": "or_leg_ask",
                                "leg": leg, "bonus": bonus, "try": go,
                                "why": why}) + "\n")
    except OSError:
        pass


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--record":
        leg, bonus = argv[1], argv[2]
        try:
            obs = json.loads(OBS.read_text() or "{}")
        except (OSError, ValueError):
            obs = {}
        with JOURNAL.open("a") as f:
            f.write(json.dumps({"t": time.time(), "kind": "or_leg_bonus",
                                "leg": leg, "bonus": bonus,
                                "held": sorted(held_types(obs))}) + "\n")
        return 0
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    obs_path = Path(argv[1]) if len(argv) > 1 else OBS
    try:
        obs = json.loads(obs_path.read_text() or "{}")
    except (OSError, ValueError):
        return 1
    out = missing_branch(argv[0], held_types(obs))
    if not out:
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

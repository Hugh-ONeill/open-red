#!/usr/bin/env python3
"""A PARTY LEG WHOSE PURPOSE IS DONE IS ASKED ABOUT BEFORE IT IS PLAYED.

The party pass writes each leg with what it is for ("a party Pokemon knows
FLASH", for: "Retrieve the Pokemon Flute from Mr. Fuji"). Run of record 4
(2026-09-26) got the flute and then went into its fifth authoring of the
FLASH leg, plan v16, hunting HM05 on Route 9, with nothing ahead that the
leg was for (user: "add the ask for upkeep legs whose purpose is done").

So before a party leg is planned, when the leg it was written for is done
— that leg at or behind the run's progress, or a finished leg sharing a
name with it (the flute was finished under other words) — the model is
shown the leg, what it was for, the finished leg, where the run stands and
what is ahead, and says whether the leg is still worth an attempt. Its
call. A no skips the leg the way a party leg that ran out is skipped
(run/outline_upkeep_missed), and says so; a yes, or an unreadable answer,
plays it. Asked once per leg per chain (run/upkeep_purpose_asked).
Called from author.check_done, which the chain asks before every leg."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import or_leg

UPKEEP = Path("plans/outline.upkeep")
OUTLINE = Path("plans/outline.txt")
PROGRESS = Path("run/outline_leg")
ASKED = Path("run/upkeep_purpose_asked")
MISSED = Path("run/outline_upkeep_missed")
JOURNAL = Path("run/executor_log.jsonl")
_NOTE = re.compile(r"\s*\(a doubt you recorded when outlining:.*$")

ASK_SYS = """You are playing Pokemon Red, working down an outline you wrote.

The next objective on it is one you added to prepare your party, and when
you added it you said what it was for. That purpose has been met already.
Decide whether this objective is still worth an attempt now, given where
the run stands and what is ahead of you; if not, it is skipped and you go
on with the next one.

Reply with JSON only:
{"why": "one or two sentences", "try": true or false}"""


def _lines(p: Path) -> list:
    try:
        return [l.strip() for l in p.read_text().splitlines() if l.strip()]
    except OSError:
        return []


def purpose_done(leg: str) -> tuple:
    """(what the leg was for, the finished leg that meets it) or ("", "")."""
    why = or_leg.purpose(leg)
    if not why:
        return "", ""
    lines = _lines(OUTLINE)
    try:
        done = int(PROGRESS.read_text().strip() or 0)
    except (OSError, ValueError):
        done = 0
    behind = lines[:done]
    if why in behind:
        return why, why
    try:
        from author import _names
    except Exception:
        return why, ""
    want = _names(why)
    hit = next((l for l in reversed(behind) if want & _names(l)), "")
    return why, hit


def maybe_skip(goal: str, start: str, model: str) -> str:
    """The model's reason for skipping this leg, or "" to play it."""
    leg = _NOTE.sub("", str(goal or "")).strip()
    if leg not in set(_lines(UPKEEP)) or leg in set(_lines(ASKED)):
        return ""
    why_for, met = purpose_done(leg)
    if not met:
        return ""
    with ASKED.open("a") as f:
        f.write(leg + "\n")
    lines = _lines(OUTLINE)
    try:
        at = int(PROGRESS.read_text().strip() or 0)
    except (OSError, ValueError):
        at = 0
    ahead = [l for l in lines[at:at + 9] if l != leg][:8]
    body = (f"THE OBJECTIVE: {leg}\n"
            f"WHEN YOU ADDED IT YOU SAID IT WAS FOR: {why_for}\n"
            f"ALREADY DONE: {met}\n"
            f"\nWHERE THE RUN STANDS: {start}\n"
            + ("\nTHE NEXT OBJECTIVES ON YOUR OUTLINE:\n"
               + "\n".join(f"  - {l}" for l in ahead) if ahead else ""))
    try:
        import brock_probe
        reply = brock_probe.chat([{"role": "system", "content": ASK_SYS},
                                  {"role": "user", "content": body}], model)
    except Exception as e:          # noqa: BLE001 — a failed ask plays the leg
        print(f"[upkeep-ask] could not ask ({e}); playing it")
        return ""
    ans = or_leg._first_object(reply or "")
    if not isinstance(ans, dict) or not isinstance(ans.get("try"), bool):
        print(f"[upkeep-ask] no readable answer; playing it")
        return ""
    why = " ".join(str(ans.get("why") or "").split())[:300]
    try:
        with JOURNAL.open("a") as f:
            f.write(json.dumps({"t": time.time(), "kind": "upkeep_purpose_ask",
                                "leg": leg, "for": why_for, "met": met,
                                "try": ans["try"], "why": why}) + "\n")
    except OSError:
        pass
    if ans["try"]:
        print(f"[upkeep-ask] still worth it: {why}")
        return ""
    with MISSED.open("a") as f:
        f.write(leg + "\n")
    return why


if __name__ == "__main__":
    print(purpose_done(sys.argv[1]))

#!/usr/bin/env python3
"""Go back to a passed-over leg before playing what waits on it.

A leg the ladder could not move, change or strike out is PASSED OVER and
the chain plays on (fresh_discovery.sh). But what waits on it cannot
succeed either: run 36 passed over "Obtain HM04 STRENGTH", then "Clear
Victory Road" (the inserts ledger says it waits on HM04), then "Defeat
the Elite Four" (waits on Victory Road), and went on to author the final
rival fight from the Safari Zone (2026-10-05, user: "nope it went straight
back to 'Defeat rival in final showdown'"). So before a leg that waits on
a passed-over leg, and before the outline's last leg, the chain goes back
to the earliest passed-over leg that still has something waiting on it
ahead, and tries it again with everything learned since.

Waiting is the inserts ledger's own record (run/outline_inserts,
"LEG=<needs>|<needed>", followed transitively, a PULL row counting); the
last leg waits on everything, since nothing comes after the end of the
game. Each leg is gone back to at most RETURNS times a chain
(run/outline_returns), so the chain cannot circle for ever.

Usage: return_leg.py <i>    prints "<p>\\t<text>" and exits 0 to go back
                            to leg p; exits 1 to play leg i as it stands.
"""
import os
import sys
from pathlib import Path

OUT = Path("plans/outline.txt")
PASSED = Path("run/outline_passed")
INSERTS = Path("run/outline_inserts")
RETURNS_LOG = Path("run/outline_returns")
RETURNS = int(os.environ.get("RED_LEG_RETURNS", "2"))


def _lines(p: Path) -> list:
    try:
        return [l.strip() for l in p.read_text().splitlines() if l.strip()]
    except OSError:
        return []


def _needs() -> dict:
    """needs -> set of what it waits on, directly."""
    out: dict = {}
    for row in _lines(INSERTS):
        if not row.startswith("LEG=") or "|" not in row:
            continue
        dep, pre = row[4:].split("|", 1)
        if pre.startswith("PULL "):
            pre = pre[5:]
        dep, pre = dep.strip(), pre.strip()
        if dep and pre and dep != pre:
            out.setdefault(dep, set()).add(pre)
    return out


def waits_on(text: str, needs: dict) -> set:
    out, todo = set(), [text]
    while todo:
        for pre in needs.get(todo.pop(), ()):
            if pre not in out:
                out.add(pre)
                todo.append(pre)
    return out


def pick(i: int):
    lines = _lines(OUT)
    if not 1 <= i <= len(lines):
        return None
    passed = set(_lines(PASSED))
    if not passed:
        return None
    used: dict = {}
    for t in _lines(RETURNS_LOG):
        used[t] = used.get(t, 0) + 1
    needs = _needs()
    here = lines[i - 1]
    behind = {t: k + 1 for k, t in enumerate(lines[:i - 1])}
    cands = []
    for t, p in behind.items():
        if t not in passed or used.get(t, 0) >= RETURNS:
            continue
        if t in waits_on(here, needs):
            cands.append(p)
        elif i == len(lines):
            # the last leg: anything still waiting on t ahead of here
            ahead = lines[p:i]
            if any(t in waits_on(a, needs) for a in ahead):
                cands.append(p)
    if not cands:
        return None
    p = min(cands)
    return p, lines[p - 1]


def main(argv):
    if len(argv) != 1:
        sys.exit("usage: return_leg.py <i>")
    got = pick(int(argv[0]))
    if not got:
        sys.exit(1)
    p, text = got
    lines = _lines(OUT)
    i = int(argv[0])
    # the legs from p up to here are played again: none of them is passed
    # over any more until the ladder passes it over again
    replay = set(lines[p - 1:i - 1])
    PASSED.write_text("".join(l + "\n" for l in _lines(PASSED)
                              if l not in replay))
    with RETURNS_LOG.open("a") as fh:
        fh.write(text + "\n")
    print(f"{p}\t{text}")


if __name__ == "__main__":
    main(sys.argv[1:])

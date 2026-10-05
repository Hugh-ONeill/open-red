#!/usr/bin/env python3
"""Move an outline leg forward, and put it back when that was wrong.

Its own file rather than an inline heredoc: the chain script already
nests one, and a second sharing the terminator silently truncated the
block it was written into.

A pull is recorded by TEXT as well as by position (run/outline_pulls,
"to<TAB>from<TAB>text"). Positions shift — the sweep crosses finished
objectives off, the insert rung adds one — so the number that named a leg
when it moved may name a different leg by the time the move turns out to
have been a mistake. The text is what survives.

Usage: pull_leg.py pull <to> <from>
       pull_leg.py undo <at>
"""
import sys
from pathlib import Path

OUT = Path("plans/outline.txt")
PULLS = Path("run/outline_pulls")
FAILED = Path("run/outline_pulls_failed")
AUTHORED = Path("plans/outline.authored")
UPKEEP = Path("plans/outline.upkeep")
PROGRESS = Path("run/outline_leg")


def _lines(p: Path) -> list:
    try:
        return [l.strip() for l in p.read_text().splitlines() if l.strip()]
    except OSError:
        return []


def anchor_of(text: str) -> str:
    """The story leg a party leg was placed after, in the model's own
    outline, or "".

    The party pass places each leg it adds directly after a story leg it
    names ("a party Pokemon knows CUT" after "Retrieve the HM01 from the
    S.S. Anne"), and the banked outline keeps that placement: the nearest
    story leg above it there is the one it was placed after. It counts as
    what the leg waits on only when the two share a name, read as the
    author's guards read them (HM01 is CUT, by the game's own machine
    table): "a party Pokemon knows CUT" after "Retrieve the HM01 from the
    S.S. Anne" waits on it; "the party holds a FLYING type", placed after
    the same leg, does not."""
    up = set(_lines(UPKEEP))
    if text not in up:
        return ""
    banked = _lines(AUTHORED)
    if text not in banked:
        return ""
    for leg in reversed(banked[:banked.index(text)]):
        if leg not in up:
            try:
                from author import _names
            except Exception:
                return ""
            return leg if (_names(text) & _names(leg)) else ""
    return ""


def before_its_anchor(lines: list, to: int, text: str) -> str:
    """The anchor this pull would put the leg ahead of, or "": the leg's
    anchor is still on the list, not yet done, and at or after `to`."""
    a = anchor_of(text)
    if not a or a not in lines:
        return ""
    try:
        done = int(PROGRESS.read_text().strip() or 0)
    except (OSError, ValueError):
        done = 0
    pos = lines.index(a) + 1
    return a if pos > done and pos >= to else ""


def read_outline() -> list:
    return [l for l in OUT.read_text().splitlines() if l.strip()]


def write_outline(lines: list):
    OUT.write_text("\n".join(lines) + "\n")


def records() -> list:
    try:
        return [l.split("\t") for l in PULLS.read_text().splitlines()
                if l.strip()]
    except OSError:
        return []


INSERTS = Path("run/outline_inserts")


def prerequisites_of(text: str) -> set:
    """Every leg the ladder put before `text` as needed first
    (run/outline_inserts "LEG=<needs>|<needed>"), and what those need in
    turn. A rewording row names the leg itself under new words, so a row
    whose two sides are the leg's own wordings is no prerequisite."""
    rows = []
    for row in _lines(INSERTS):
        if row.startswith("LEG=") and "|" in row:
            dep, pre = row[4:].split("|", 1)
            if pre.startswith("PULL "):
                pre = pre[5:]
            rows.append((dep.strip(), pre.strip()))
    out, todo = set(), [text.strip()]
    while todo:
        cur = todo.pop()
        for dep, pre in rows:
            if dep == cur and pre and pre != text.strip() and pre not in out:
                out.add(pre)
                todo.append(pre)
    return out


def do_pull(to: int, frm: int):
    lines = read_outline()
    if not (1 <= to <= len(lines)) or not (1 <= frm <= len(lines)):
        sys.exit(f"pull_leg: {to} or {frm} is off the list of {len(lines)}")
    # A LEG IS NOT PULLED AHEAD OF WHAT IT WAS PLACED AFTER. Run of
    # record 4 (2026-09-25): stuck on "Retrieve the S.S. Ticket", the
    # blocker rung pulled "a party Pokemon knows CUT" five legs forward on
    # the model's "the path ... is blocked by a CUT_TREE" — ahead of
    # "Retrieve the HM01 from the S.S. Anne", the leg the party pass had
    # placed it after, which needs the ticket. The run then had to teach
    # CUT before it could reach the HM, decided Bill gives it, and went
    # back to him for a quarter of an hour (user: "fix the pull so it
    # can't jump ahead of its prerequisite"). The prerequisite is the
    # model's own placement (anchor_of), not a table; refused, the chain
    # goes on to its next rung.
    _a = before_its_anchor(lines, to, lines[frm - 1])
    if _a:
        print(f"pull refused: {lines[frm - 1]!r} was placed after {_a!r}, "
              f"which is still ahead at leg {lines.index(_a) + 1}; pulled to "
              f"{to} it would come before what it waits on")
        sys.exit(4)
    # ...NOR AHEAD OF WHAT THE LADDER PUT BEFORE IT. The momentum rung
    # pulled "Defeat the Elite Four" to the front because the run had
    # wandered onto ROUTE_21, sliding "Clear Victory Road" behind it: the
    # leg the missing rung had inserted eleven minutes earlier because the
    # Elite Four needs it first (run 36, 2026-10-05). push_leg already
    # refuses the mirror image; the inserts ledger says what each insert
    # was for, and what that insert needs is needed too.
    _pre = prerequisites_of(lines[frm - 1])
    _over = [l for l in lines[to - 1:frm - 1] if l in _pre]
    if _over:
        print(f"pull refused: {_over[0]!r} was put before "
              f"{lines[frm - 1]!r} because it is needed first, and pulled "
              f"to {to} the leg would jump it")
        sys.exit(4)
    text = lines.pop(frm - 1)
    lines.insert(to - 1, text)
    write_outline(lines)
    with PULLS.open("a") as fh:
        fh.write(f"{to}\t{frm}\t{text}\n")
    print(f"pulled forward: {text}")


def do_undo(at: int):
    """Put back the leg pulled to this position, if one was.

    A pulled-forward leg that then exhausts its own attempts did not
    unstick anything, and leaving it where it is costs the run twice: the
    leg it displaced never comes up, and the reorder budget is spent
    defending the mistake. It goes home, and it is written down as a pull
    that failed so the blocker rung will not make the same move again.
    """
    lines = read_outline()
    recs = records()
    for k in range(len(recs) - 1, -1, -1):
        r = recs[k]
        if len(r) < 3 or int(r[0]) != at:
            continue
        text = r[2]
        if text not in lines:
            break
        frm = max(1, min(int(r[1]), len(lines)))
        lines.remove(text)
        lines.insert(frm - 1, text)
        write_outline(lines)
        del recs[k]
        PULLS.write_text("".join("\t".join(x) + "\n" for x in recs))
        with FAILED.open("a") as fh:
            fh.write(f"{at}\t{text}\n")
        print(f"put back at {frm}: {text}")
        return
    sys.exit(3)


if len(sys.argv) < 3:
    sys.exit(__doc__)
if sys.argv[1] == "pull":
    do_pull(int(sys.argv[2]), int(sys.argv[3]))
elif sys.argv[1] == "undo":
    do_undo(int(sys.argv[2]))
else:
    sys.exit(__doc__)

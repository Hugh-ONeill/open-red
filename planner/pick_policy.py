#!/usr/bin/env python3
"""Which battle policy plays: the one that SCORED best, not the newest file.

fresh_run.sh picked the active spec with `ls plans/policy_model_v*.json |
sort -V | tail -1` — the highest version number, which is a filename and
not a result. Run 16 therefore fought its entire game on v6, whose own
provenance records three gauntlet trials that cleared ZERO rooms and
blacked out three times out of three, while v1 (6/6 on the rival, three
badges, no blackouts) and v3 (eight Elite Four rooms, no blackouts) sat
beside it in the same directory (2026-09-12).

Every spec carries the trial that judged it in `provenance.eval`, written
by policy_author.py at the moment it was scored. That is the ranking, and
it was already there.

TWO ARENAS, NOT ONE SCALE. policy_author runs either the Brock arena (the
level-five rival, then the forest and Pewter Gym) or the Elite Four
gauntlet, and they measure different things: `rooms` only exists for the
gauntlet, `badge` and `rival_wins` only for Brock. Ranking them on one
tuple would mean any gauntlet spec beats any Brock spec by default. So
they are ranked SEPARATELY and the stage chooses between them — which is
also why the specs read the way they do: v1 heals with POTION and cures
with ANTIDOTE, things a Kanto mart stocks, and v6 reaches for HYPER_POTION
and MAX_REVIVE, which no early party has ever seen.

  pick_policy.py                 the best sound spec, any arena
  pick_policy.py --badges 3      the best for a run wearing three badges
  pick_policy.py --why           say what was rejected and why
  pick_policy.py --kind train    the best TRAIN rule (plans/train_model_v*)

A THIRD KIND, RANKED ON ITS OWN (2026-09-19). A train rule is the `train`
block alone, authored over a base policy and scored in the training rooms
(policy_author.py --train-block): how far a trainee got toward its goal
level inside a step budget. That number has nothing to do with rooms
cleared or badges won, so train artifacts never enter the fight ranking
and the fight policies never enter theirs. The executor lays the chosen
rule over whichever fight policy plays (--train-spec).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Where the stage line falls, FOR SPECS THAT WERE ONLY EVER SCORED IN ONE
# ARENA. The gauntlet arena is the last fight in the game and the Brock
# arena is the first; a run is on the endgame side of that once it holds
# the badges that open the league.
#
# A stage line is a workaround, not the design. It exists because every
# spec on disk was authored inside one arena and named that arena's items:
# v1 heals with POTION and cures with ANTIDOTE, which a Kanto mart stocks,
# and v6 reaches for HYPER_POTION and MAX_REVIVE, which no early party has
# seen. Switching specs at a badge count patches over that, and badly —
# the seam is exactly where the bag and the policy disagree, and run 17
# crossed no seam at all, playing v1's POTION rule into Erika with three
# SUPER_POTIONs in the bag (2026-09-15). The answer is ONE SPEC FIT TO THE
# WHOLE GAME (user, 2026-08-24: "not one per stage"), which the item
# classes make writable and the multi-arena run makes scorable. A spec
# that carries `arenas` was scored in more than one and needs no line
# drawn through the game; it wins outright, at any badge count.
E4_FROM_BADGES = 8


def _eval(p: Path) -> dict:
    try:
        d = json.loads(p.read_text())
    except (OSError, ValueError):
        return {}
    return (d.get("provenance") or {}).get("eval") or {}


def fit_across(ev: dict) -> dict:
    """The per-arena results of a spec scored in more than one arena, or
    {} for the single-arena specs that came before."""
    ar = ev.get("arenas")
    return ar if isinstance(ar, dict) and len(ar) > 1 else {}


def rooms_of(ev: dict) -> dict:
    """Every room an artifact was scored in, one or many (a train rule
    scored in a single room still has a score to rank)."""
    ar = ev.get("arenas")
    return ar if isinstance(ar, dict) else {}


def cross_score(ev: dict) -> tuple:
    """Higher is better, across arenas.

    A SUM IS NOT COMPARABLE BETWEEN SPECS SCORED IN DIFFERENT ROOMS, and
    this said it was. v7 was scored in four arenas for 3.60 and v8 in
    nine for 8.27, and the sum ranked v8 first for the arithmetic reason
    that nine fractions add up to more than four — it would have ranked a
    WORSE spec first just as happily (2026-09-15). What the sums are
    actually claiming is two different things, so both are said: how many
    rooms the spec was asked to hold up in, and how well it held up on
    average. More evidence first, because that is what "fit to the whole
    game" means; then the fraction, which IS comparable."""
    ar = fit_across(ev)
    try:
        total = float(ev.get("cross_total") or 0.0)
    except (TypeError, ValueError):
        total = 0.0
    mean = total / len(ar) if ar else 0.0
    return (len(ar), round(mean, 6),
            -sum(int((r or {}).get("blackouts") or 0) for r in ar.values()))


def arena_of(ev: dict) -> str:
    """Which arena judged this spec. Recorded by policy_author since
    2026-09-12; inferred from the shape of the score for older files —
    the Brock arena is the only one that fights the rival or wins badges."""
    a = str(ev.get("arena") or "")
    if a:
        return a
    if (ev.get("rival_trials") or 0) or (ev.get("badge") or 0):
        return "brock"
    return "e4"


def failed_its_own_trial(ev: dict) -> str:
    """Why this spec should never be chosen, or "" if it is sound.

    A spec that blacked out in EVERY trial it was given did not survive
    the only test it has, and no version number changes that."""
    if not ev:
        return "no recorded trial at all"
    trials = (ev.get("gauntlet_trials") or 0) + (ev.get("rival_trials") or 0)
    if trials and (ev.get("blackouts") or 0) >= trials:
        return f"blacked out in all {trials} of its own trials"
    if not trials:
        return "its trial ran no fights"
    return ""


def score(ev: dict) -> tuple:
    """Higher is better, within one arena. The same terms policy_author
    ranks its own candidates on, minus `rooms` for the Brock arena where
    it does not exist."""
    return (int(ev.get("rooms") or 0),
            int(ev.get("badge") or 0),
            int(ev.get("pewter") or 0),
            (ev.get("rival_wins") or 0) / max(1, ev.get("rival_trials") or 0),
            -int(ev.get("blackouts") or 0),
            -float(ev.get("dmg_gap") or 0.0))


def rank(paths, badges: int | None = None):
    """(winner, rows) — rows are (path, arena, sound?, why, score)."""
    rows = []
    for p in sorted(paths):
        ev = _eval(p)
        why = failed_its_own_trial(ev)
        rows.append((p, arena_of(ev), not why, why, score(ev)))
    sound = [r for r in rows if r[2]]
    if not sound:
        return None, rows
    # A SPEC FIT ACROSS THE GAME NEEDS NO STAGE LINE DRAWN THROUGH IT.
    whole = [r for r in sound if fit_across(_eval(r[0]))]
    # ...BUT ONLY SCORES FROM THE SAME ROOMS CAN BE COMPARED. Arenas get
    # rebuilt; a percentage from an older version of a room is a
    # measurement on a different instrument. Specs carrying arena stamps
    # are ranked among themselves, and an unstamped one — every spec
    # written before 2026-09-15 — is not trusted above them.
    _stamped = [r for r in whole if (_eval(r[0]).get("arena_stamps") or {})]
    if _stamped:
        whole = _stamped
    if whole:
        return max(whole, key=lambda r: cross_score(_eval(r[0])))[0], rows
    want = None
    if badges is not None:
        want = "e4" if badges >= E4_FROM_BADGES else "brock"
        tier = [r for r in sound if r[1] == want]
        if tier:
            return max(tier, key=lambda r: r[4])[0], rows
    # no stage asked, or no spec scored on that stage's arena: the best
    # sound one anywhere, which at least beat something
    return max(sound, key=lambda r: r[4])[0], rows


def train_rejected(p: Path) -> str:
    """Why this train artifact should not be chosen, or ""."""
    try:
        d = json.loads(p.read_text())
    except (OSError, ValueError):
        return "unreadable"
    if not isinstance(d.get("train"), dict):
        return "it carries no train rule"
    ev = (d.get("provenance") or {}).get("eval") or {}
    rooms = ev.get("arenas") or {}
    if not rooms:
        return "no recorded trial at all"
    trials = sum(int((r or {}).get("gauntlet_trials") or 0)
                 for r in rooms.values())
    if not trials:
        return "its trial ran no battles"
    if sum(int((r or {}).get("blackouts") or 0)
           for r in rooms.values()) >= trials:
        return f"blacked out in all {trials} of its own trials"
    # A RULE THAT LOST TO A CONSTANT IS NOT AN IMPROVEMENT ON ONE. Every
    # artifact records what the constant tactics scored in the same rooms
    # on the same day; a rule under the best of them would have the run
    # train worse than "always fight" or "always switch" would.
    refs = (d.get("provenance") or {}).get("references") or {}
    best_ref = max((float((v or {}).get("cross_total") or 0.0)
                    for v in refs.values()), default=0.0)
    if float(ev.get("cross_total") or 0.0) < best_ref:
        return (f"scored {float(ev.get('cross_total') or 0.0):.2f} across "
                f"its rooms, under a constant tactic's {best_ref:.2f}")
    return ""


def rank_train(paths):
    """(winner, rows) among train artifacts — rows are (path, why)."""
    rows = [(p, train_rejected(p)) for p in sorted(paths)]
    sound = [p for p, why in rows if not why]
    # only scores from the same rooms compare; more rooms first, then the
    # mean of them (cross_score), the same rule the fight policies follow
    if not sound:
        return None, rows
    def key(p):
        ev = _eval(p)
        ar = rooms_of(ev)
        try:
            total = float(ev.get("cross_total") or 0.0)
        except (TypeError, ValueError):
            total = 0.0
        return (len(ar), round(total / max(1, len(ar)), 6),
                -sum(int((r or {}).get("blackouts") or 0)
                     for r in ar.values()))
    return max(sound, key=key), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=REPO / "plans")
    ap.add_argument("--glob", default=None)
    ap.add_argument("--kind", choices=("fight", "train"), default="fight",
                    help="fight: the battle policy (policy_model_v*). "
                         "train: the train rule laid over it "
                         "(train_model_v*), ranked on the training rooms")
    ap.add_argument("--badges", type=int, default=None,
                    help="how many badges the run holds, to pick the tier")
    ap.add_argument("--why", action="store_true",
                    help="print every spec and why it did or did not win")
    a = ap.parse_args()
    if a.kind == "train":
        paths = list(Path(a.dir).glob(a.glob or "train_model_v*.json"))
        win, rows = rank_train(paths)
        if a.why:
            for p, why in rows:
                mark = "WINNER" if p == win else ("REJECT" if why else "  ok  ")
                _ev = _eval(p)
                _ac = rooms_of(_ev)
                _mean = float(_ev.get("cross_total") or 0.0) / max(1, len(_ac))
                print(f"{mark} {p.name:28s} "
                      + (why or f"across {len(_ac)} training room(s), "
                                f"{_mean:.0%} of each"),
                      file=sys.stderr)
        if not win:
            return 1
        print(win)
        return 0
    paths = list(Path(a.dir).glob(a.glob or "policy_model_v*.json"))
    if not paths:
        return 1
    win, rows = rank(paths, a.badges)
    if a.why:
        for p, arena, ok, why, sc in sorted(rows, key=lambda r: -r[4][0]):
            mark = "WINNER" if p == win else ("  ok  " if ok else "REJECT")
            _ac = fit_across(_eval(p))
            print(f"{mark} {p.name:28s} arena={arena:6s} "
                  + (why or (f"across {len(_ac)} arenas, "
                             f"{cross_score(_eval(p))[1]:.0%} of each"
                             if _ac
                             else f"score={sc}")), file=sys.stderr)
            # A SCORE IS UNREADABLE WITHOUT THE PARTY THAT PRODUCED IT.
            # v3's eight rooms with no healing rules at all look like a
            # finding about the spec until you see the L71 CHARIZARD that
            # swept them. Specs written before 2026-09-12 cannot say.
            lead = (_eval(p).get("arena_party") or [])
            if ok and lead:
                print(f"       scored on: {', '.join(lead[:6])}",
                      file=sys.stderr)
    if not win:
        return 1
    print(win)
    return 0


if __name__ == "__main__":
    sys.exit(main())

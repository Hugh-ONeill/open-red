#!/usr/bin/env python3
"""HOW OLD IS THE POLICY THAT IS ABOUT TO PLAY?

A battle policy is a frozen artifact authored once; the DSL keeps growing;
nothing connected the two. Add a word to the vocabulary and every run after
it quietly ignores that word until somebody remembers to author again. No
warning at launch, no staleness check, nothing in the journal.

plans/policy_model_v13.json was authored 2026-09-15 and pinned on the 16th.
`probe_hit` — the rule that lets a catch spend one weak hit so it can see
what its own move does, without which the weakener has no damage on record,
nothing counts as safe, and every turn falls through to a throw — was
committed on the 16th. The model could not have chosen it. Run 33 then
threw five balls at a full-HP KAKUNA without attacking once, and a whole
pocket went the same way (2026-09-22, user: "damn thats a stupid
oversight"). The status words landed on the 21st and are just as dormant.

So: say it at launch. Not a judgment, not a refusal — a count and a list,
so a policy that predates half its vocabulary cannot do it in silence.

  spec_age.py plans/policy_model_v13.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "planner"))


# The TRAIN block is described inside DSL_DOC as well as TRAIN_DOC, so the
# documents cannot tell them apart; these are its words, and they are
# supplied by the train artifact (plans/train_model_v*.json) rather than by
# the fight policy, so a fight policy is not stale for lacking them.
TRAIN_BLOCK_WORDS = {"fight_if", "else", "min_level_ratio", "min_matchup",
                     "max_foe_matchup", "seen_ko_hits",
                     "types_ignored_at_level_ratio", "wild_items"}


def dsl_words() -> set:
    """Every rule word the author is offered today, read from the document
    it is actually shown — not from a list kept by hand here, which would
    go stale in the same way the policy does."""
    import policy_author
    # THE TRAIN RULE IS ITS OWN ARTIFACT, laid over whichever policy plays
    # (plans/train_model_v*.json, picked by fresh_run.sh), so its words are
    # not missing from a fight policy that does not carry them.
    doc = policy_author.DSL_DOC
    # the doc names its words in quotes ("out_of_pp") or as `key:` at the
    # head of a line; both forms appear, so take both
    out = set(re.findall(r'"([a-z_]{3,})"\s*:', doc))
    out |= set(re.findall(r"^\s{2,6}([a-z_]{3,}):", doc, re.M))
    # words that are values or prose, not rule keys
    return out - {"trainer", "wild", "any", "true", "false", "null", "int",
                  "str", "bool", "resists", "healthiest", "first_alive",
                  "best_matchup", "heal", "cure", "revive", "ball", "last",
                  "free", "name", "move", "item", "slot", "kind", "why",
                  "read", "train"} - TRAIN_BLOCK_WORDS


def words_used(spec) -> set:
    """Every word this spec actually carries, at any depth."""
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                out.add(str(k))
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk({k: v for k, v in (spec or {}).items() if k != "provenance"})
    return out


def report(path) -> tuple:
    """(missing words, used words) for the spec at `path`."""
    try:
        spec = json.loads(Path(path).read_text() or "{}")
    except (OSError, ValueError):
        return set(), set()
    used = words_used(spec)
    return dsl_words() - used, used


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        print("usage: spec_age.py <spec.json>")
        return 2
    missing, used = report(argv[0])
    name = Path(argv[0]).name
    if not used:
        print(f"[policy] {name}: could not be read")
        return 1
    if not missing:
        print(f"[policy] {name} uses every word the DSL offers")
        return 0
    # A COUNT OF WORDS NOT USED, NOT A DATE. This tool cannot see when a
    # word was added or when the spec was written; it sees only what the
    # spec carries. "was authored before six words" was said of v16 on
    # 2026-09-23, a spec written after every one of them (it simply chose
    # not to use them), so the line now says what is measured.
    print(f"[policy] {name} does not use {len(missing)} word(s) the DSL "
          f"offers: {', '.join(sorted(missing))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

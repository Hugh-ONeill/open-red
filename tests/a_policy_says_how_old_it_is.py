#!/usr/bin/env python3
"""The launch says when the policy about to play predates words it could
be using.

A battle policy is frozen when it is authored; the DSL keeps growing;
nothing connected the two. plans/policy_model_v13.json was authored
2026-09-15 and pinned on the 16th. `probe_hit` was committed on the 16th —
the rule that lets a catch spend one weak hit so its own damage is on
record, without which the weakener has nothing it calls safe and every turn
falls through to a throw. The model could not have chosen it. Run 33 threw
five balls at a full-HP KAKUNA without attacking once and lost a whole
pocket the same way. The status words landed on the 21st and are just as
dormant (user, 2026-09-22: "damn thats a stupid oversight").

So the launch counts them. Not a judgment and not a refusal — the pin still
plays — just a line so a policy that predates half its vocabulary cannot do
it in silence.

Pinned: the words come from the document the author is actually shown, not
a hand-kept list that would go stale the same way; the TRAIN block's words
are excluded, because a separate artifact supplies them; v13's real gap is
reported; a spec using everything says so; an unreadable file does not
crash the launch; and the launch prints it after naming the policy.
Synthetic."""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import spec_age as S  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


words = S.dsl_words()
ck("the vocabulary is read from the author's own document",
   "probe_hit" in words and "only_if_foe_clear" in words
   and "out_of_pp" in words and "setup" in words, sorted(words)[:8])
ck("...not from a list kept by hand in this tool",
   "policy_author" in (ROOT / "planner/spec_age.py").read_text())
ck("the train block's words are left out, being another artifact's",
   not (words & S.TRAIN_BLOCK_WORDS) and "fight_if" in S.TRAIN_BLOCK_WORDS)
ck("...and values and prose are not counted as rule words",
   not ({"trainer", "wild", "healthiest", "true", "ball"} & words))

missing, used = S.report(ROOT / "plans/policy_model_v13.json")
ck("v13's real gap is the eight words of the 2026-09-22 audit, and field_revive (2026-09-30)",
   missing == {"field_revive", "first_ball", "max_share", "min_foe_level_ratio",
               "only_if_foe_clear", "only_if_leader", "per_foe",
               "probe_hit", "self_ko"}, sorted(missing))
ck("...and what it DOES carry is not reported as missing",
   {"out_of_pp", "reserve", "field_cure", "setup", "switch"} <= used)

tmp = Path(tempfile.mkdtemp())
full = tmp / "full.json"
full.write_text(json.dumps({k: 1 for k in words}))
ck("a spec using every word has no gap", S.report(full)[0] == set())
bad = tmp / "bad.json"
bad.write_text("{not json")
ck("an unreadable spec reports nothing rather than crashing",
   S.report(bad) == (set(), set()))

buf = io.StringIO()
with redirect_stdout(buf):
    rc = S.main([str(ROOT / "plans/policy_model_v13.json")])
out = buf.getvalue()
ck("the line names the spec, the count and the words",
   rc == 0 and "policy_model_v13.json" in out and "9 word(s)" in out
   and "probe_hit" in out, out.strip()[:120])
ck("...and never refuses or advises, only counts",
   not any(w in out.lower() for w in
           ("refus", "should", "must", "re-author", "stale", "error")), out)
buf = io.StringIO()
with redirect_stdout(buf):
    S.main([str(full)])
ck("a current spec says so plainly", "every word the DSL offers" in buf.getvalue())

SH = (ROOT / "fresh_run.sh").read_text()
ck("the launch runs it, after naming the policy",
   'python planner/spec_age.py "$POLICY"' in SH
   and SH.index('echo "[policy] $POLICY"') < SH.index("spec_age.py"))
ck("...and a failure there never stops a launch",
   'spec_age.py "$POLICY" 2>/dev/null || true' in SH)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

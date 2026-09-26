#!/usr/bin/env python3
"""A party leg gets one short attempt, and is asked about first when what
it was for is already done.

Run of record 4, 2026-09-26: "a party Pokemon knows FLASH", written for
"Retrieve the Pokemon Flute from Mr. Fuji", was authored five times after
the flute was in the bag, reached plan v18, and cost 3.5 hours and 275
rounds hunting HM05 on Route 9, while the ladder's pulls kept sending it
round again (user: "an unneccesary party leg shouldnt derail the entire
run for hours"; "stop it, apply the fixes, and restart clean").

Pinned: the purpose is read from the leg's note and met by that leg, or
by a finished leg sharing its name; the model is asked once and its no
skips the leg (filed with the party legs played on past) and makes the
check-done CLI exit 5, which the chain says in its own words; a yes, a
purpose not yet met, or a story leg plays as before; a party leg's one
attempt runs on half the round budget and, failed, plays on without the
ladder; the refused-pull line no longer names a judge. Synthetic."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import brock_probe  # noqa: E402
import upkeep_ask as U  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


FLASH = "a party Pokemon knows FLASH"
d = Path(tempfile.mkdtemp(prefix="upask_"))
(d / "plans").mkdir(); (d / "run").mkdir()
(d / "plans/outline.upkeep").write_text(f"{FLASH}\n")
(d / "plans/outline.authored").write_text("\n".join([
    "Reach Rock Tunnel", FLASH, "Retrieve the Pokemon Flute from Mr. Fuji",
    "Defeat Sabrina for the Marsh Badge"]) + "\n")
(d / "plans/outline.notes").write_text(f"{FLASH}\tfor: Retrieve the Pokemon Flute from Mr. Fuji\n")
(d / "plans/outline.txt").write_text("\n".join([
    "Reach Rock Tunnel", "Retrieve the Poké Flute", FLASH,
    "Retrieve the Pokemon Flute from Mr. Fuji", "Defeat Sabrina for the Marsh Badge"]) + "\n")
(d / "run/outline_leg").write_text("2")
os.chdir(d)

why, met = U.purpose_done(FLASH)
ck("the purpose is the leg's own note, met by a finished leg sharing its name",
   why == "Retrieve the Pokemon Flute from Mr. Fuji" and met == "Retrieve the Poké Flute",
   (why, met))
seen = {}


def stub(reply):
    def chat(msgs, model, **kw):
        seen["body"] = msgs[-1]["content"]
        return reply
    return chat


brock_probe.chat = stub('{"why": "the flute is already in the bag", "try": false}')
G = FLASH + " (a doubt you recorded when outlining: for: Retrieve the Pokemon Flute from Mr. Fuji)"
r = U.maybe_skip(G, "standing in LAVENDER_TOWN with POKE_FLUTE x1", "m")
ck("asked, the model's no skips it with its reason", r == "the flute is already in the bag", r)
ck("...shown the leg, what it was for and what met it",
   "WHEN YOU ADDED IT YOU SAID IT WAS FOR: Retrieve the Pokemon Flute from Mr. Fuji" in seen.get("body", "")
   and "ALREADY DONE: Retrieve the Poké Flute" in seen.get("body", ""), seen.get("body", "")[:400])
ck("...and filed with the party legs played on past",
   FLASH in (d / "run/outline_upkeep_missed").read_text().splitlines())
ck("asked once per leg per chain", U.maybe_skip(G, "s", "m") == "")
(d / "run/upkeep_purpose_asked").unlink()
brock_probe.chat = stub('{"why": "still useful", "try": true}')
ck("a yes plays it", U.maybe_skip(G, "s", "m") == "")
(d / "run/upkeep_purpose_asked").unlink()
(d / "run/outline_leg").write_text("0")
ck("a purpose not yet met is not asked", U.maybe_skip(G, "s", "m") == ""
   and not (d / "run/upkeep_purpose_asked").exists())
ck("a story leg is not asked", U.maybe_skip("Defeat Sabrina for the Marsh Badge", "s", "m") == "")

au = (ROOT / "planner/author.py").read_text()
ck("check_done asks it first and the CLI exits 5 on a skip",
   "_skip = upkeep_ask.maybe_skip(goal, start, model)" in au
   and "sys.exit(5 if (done and UPKEEP_SKIPPED) else 0 if done else 3)" in au)
sh = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain says a skip as a skip",
   'if [ "$_cd_rc" = 5 ]; then' in sh
   and "skipped on the model's own answer" in sh)
ck("a party leg's one attempt runs on half the budget",
   '[ "$_party" = 1 ] && _budget_scale=0.5' in sh
   and 'RED_BUDGET_SCALE="${_budget_scale:-1}"' in sh
   and 'if [ "$crc" = 1 ] && [ "$_party" = 1 ]; then\n    failed=1' in sh)
blk = sh[sh.index('if [ "$failed" = 1 ]; then'):]
blk = blk[:blk.index("A PULL THAT DID NOT UNSTICK ANYTHING GOES HOME")]
ck("...and, failed, plays on before any pull, insert or push",
   'if [ "$_party" = 1 ]; then' in blk and "a party leg — playing on" in blk
   and 'echo "$leg" >> run/outline_upkeep_missed' in blk)
ex = (ROOT / "planner/executor.py").read_text()
ck("the executor scales the rounds by RED_BUDGET_SCALE",
   'os.environ.get("RED_BUDGET_SCALE", "1")' in ex
   and "rounds = max(1, int(rounds * _bs + 0.5))" in ex)
ck("the refused-pull line names no judge", "refused by the judge" not in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

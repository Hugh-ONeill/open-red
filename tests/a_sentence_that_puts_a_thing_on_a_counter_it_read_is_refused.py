#!/usr/bin/env python3
"""A rung that writes a sentence may not put a thing on a counter this run
has read and seen it was not on.

Run 27, 2026-09-16: the wording rung rewrote "Obtain the FRESH WATER" into
"Obtain the FRESH WATER from the Cerulean City Mart" on a memory ("it is
sold at the Cerulean City Mart"), with Cerulean's counter on file from the
run's own reading and no FRESH_WATER on it. The plan validator already
refused five drafts of that leg on exactly that fact; the rung that wrote
the sentence never consulted it, and the blocker rung went on to reason
from the wrong mart.

Pinned: the fact is one function, asked of the wording rung (refused, the
wording stands) and the missing rung (turned down, re-asked); a counter
that has moved is exempt; a sentence naming no counter or no item, or a
thing the counter does sell, passes; both rungs' pages carry the counters
the run has read. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


A.walked_shelves = lambda: {
    "CERULEAN_MART": (["POKE_BALL", "POTION", "REPEL", "ANTIDOTE"], False),
    "VIRIDIAN_MART": (["POTION"], True),
    "VERMILION_MART": (["POKE_BALL", "SUPER_POTION"], False)}

got = A.names_a_counter_without("Obtain the FRESH WATER from the Cerulean City Mart")
ck("a sentence putting a thing on a counter read without it is named",
   got and got.startswith("names CERULEAN_MART, whose counter this run has read")
   and "FRESH_WATER is not on it" in got, got)
ck("...quoting what the counter sells", got and "POKE_BALL, POTION, REPEL, ANTIDOTE" in got, got)
for why, txt in (("no counter named", "Obtain the FRESH WATER"),
                 ("no item named", "Visit the Cerulean Mart"),
                 ("a thing the counter does sell", "Buy a POTION at the Cerulean Mart"),
                 ("a counter that has moved", "Buy a FRESH WATER at the Viridian Mart"),
                 ("a counter never read", "Buy a FRESH WATER at the Celadon Mart")):
    ck(f"...and passes {why}", A.names_a_counter_without(txt) is None, txt)
A.walked_shelves = lambda: {}
ck("no counters read, nothing to say",
   A.names_a_counter_without("Obtain the FRESH WATER from the Cerulean City Mart") is None
   and A.read_counters_text() == "")
A.walked_shelves = lambda: {"CERULEAN_MART": (["POTION"], False), "VIRIDIAN_MART": (["POTION"], True)}
page = A.read_counters_text()
ck("the page lists the counters read, and says which moved",
   "CERULEAN_MART: POTION" in page and "VIRIDIAN_MART: POTION — it has sold something different since" in page
   and "nothing is known of counters you have not stood at" in page, page)

src = (ROOT / "planner/author.py").read_text()
w = src[src.index("def check_wording("):]
w = w[:w.index("\nLATER_SYS")]
ck("the wording rung refuses on it and the wording stands",
   "_sh = names_a_counter_without(new)" in w and 'the "\n              f"wording stands"' in w)
ck("...before the rewrite is applied", w.index("names_a_counter_without(new)") < w.index("return new"))
ck("...and its page carries the counters", "recent_events() + done_ledger_text() + read_counters_text()" in w)
m = src[src.index("def check_missing("):]
m = m[:m.index("\ndef ", 10)]
ck("the missing rung turns it down and asks again",
   "_sh = names_a_counter_without(ins)" in m and "turned_down.append((ins, _sh +" in m)
ck("...and its page carries the counters", "done_ledger_text() + read_counters_text()" in m)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

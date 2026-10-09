#!/usr/bin/env python3
"""A done reason resting on the story's order or the game's lore is refused
even when it names a fact the record confirms; a plain hedge that names one
is still let through.

"Infiltrate Silph Co. and defeat the rival" was judged already done on "The
player has the SILPH_SCOPE, which is only obtainable after infiltrating Silph
Co. and defeating the rival/boss" — the Scope came from the Celadon hideout,
and no Silph rival or Giovanni event had fired (run 41, 2026-10-09). The
named-fact escape exists for "has the Poke Flute, indicating the tower is
cleared", where the fact is the deed's own product.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A                                        # noqa: E402

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

silph = ("The player has the SILPH_SCOPE, which is only obtainable after "
         "infiltrating Silph Co. and defeating the rival/boss.")
ck("'only obtainable after' is story order", A._order_lore(silph))
ck("...and so it is inferred", A._inferred(silph))
ck("'only possible after' still is", A._order_lore(
    "The player has entered Bill's house, which is only possible after rescuing Bill"))
ck("lore words still are", A._order_lore("Typically the gym opens after the event"))
ck("a plain hedge is not story order (the named-fact escape stays for it)",
   not A._order_lore("The player possesses the Silph Scope and Poke Flute, "
                     "indicating they have reached the end of the tower"))
ck("a plain account of a gift is not story order",
   not A._order_lore("TM28 was given by the Rocket thief and is in the bag"))

src = (ROOT / "planner/author.py").read_text()
ck("check-done skips the named-fact escape for story order",
   '_fact = "" if _order_lore(_why) else _record_fact_named(_why)' in src)
ck("...and so does the already-done rung",
   '_fact = ("" if _order_lore(ans.get("why"))' in src)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

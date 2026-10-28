"""A name off only by its underscores is answered with this map's spelling.

Run 67, 2026-10-28, leg 52 in GAME_CORNER_PRIZE_ROOM: the model pressed
TEXT_GAMECORNERPRIZE_ROOM_PRIZE_VENDOR_1 round after round and every press
came back "object ... not visible", while TEXT_GAMECORNERPRIZEROOM_PRIZE_
VENDOR_1 stood on the page. The answer was true but never said which
spelling this map uses.

Pinned: before the generic answer, a name equal to a person, fixture or
sign here once underscores are dropped is answered with that spelling.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
shim = (ROOT / "harness" / "shim.lua").read_text()

j = shim.find("A NAME OFF BY ITS UNDERSCORES IS SAID AS SPELLED HERE")
ck("the shim compares names with underscores dropped", j > 0)
blk = shim[j:j + 1800]
ck("...over people, fixtures and signs",
   "ow.npcs" in blk and "map_fixtures(G, mid)" in blk and "md.signs" in blk)
ck("...and says the spelling this map uses",
   "nothing on %s is spelled '%s'; '%s' is" in blk)
ck("...before the generic not-visible answer",
   j < shim.find('return false, "object \'" .. c.name .. "\' not visible"'))
squash = lambda n: n.replace("_", "")
ck("the run's misspelling matches the real name",
   squash("TEXT_GAMECORNERPRIZE_ROOM_PRIZE_VENDOR_1")
   == squash("TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_1"))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok  " if ok else "FAIL"), n)
    if not ok and d: print("      ", str(d)[:200])
sys.exit(1 if bad else 0)

"""The foe's PP was reported, and it was not even the foe's PP.

Gen 1 shows you your own PP on the FIGHT menu and never the enemy's. The
shim published both sides through one builder, and the enemy side has no
`curMoves`, so it fell through to `mon.moves` — the species table — and
printed every foe move at its BASE PP, a number that cannot change.
AGATHA's GENGAR read CONFUSE_RAY 10, NIGHT_SHADE 15, TOXIC 10,
DREAM_EATER 15 with NIGHT_SHADE named as its last move and nineteen
thousand turns behind it (2026-09-15).

A number that never moves and never was right is worse than no number. It
also reads as a promise the foe still has turns in it, which is exactly
the thing that was false: the Gengar had run dry, gen 1 enemies do not
Struggle, and it had stopped acting entirely.

Our own PP stays, because the FIGHT menu prints it.
"""
import sys, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / "harness" / "shim.lua").read_text()

checks = []


def ck(name, ok):
    checks.append((name, bool(ok)))
    print(("  ok   " if ok else "  FAIL ") + name)


i = src.find("local function battle_side(G, s")
blk = src[i:i + 1400] if i > 0 else ""
ck("the two sides are built by one function that knows which is which",
   "local function battle_side(G, s, mine)" in src)
ck("...and PP is published only for ours",
   "pp = mine and mv.pp or nil" in blk)
ck("our side asks for it", "battle_side(G, top.player, true)" in src)
ck("the foe's side does not", "battle_side(G, top.enemy, false)" in src)
ck("nothing else hands the foe a pp field",
   len(re.findall(r"pp\s*=\s*mv\.pp\b", src)) == 1)

ck("the reason is written down where the code is",
   "YOU CANNOT SEE THE ENEMY'S PP IN GEN 1" in src)
_why = src[src.find("YOU CANNOT SEE THE ENEMY'S PP"):][:900]
ck("...including that it was the species table, not live PP",
   "mon.moves" in _why and "BASE PP" in _why)

# our own probe still reports OUR pp, which the policy filters on
ck("the damage probe still carries our PP",
   "index = i, id = mv.id, pp = mv.pp," in src)

sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as BP
ck("...and the policy still refuses a move with none of it",
   "(m.get(\"pp\") or 0) > 0" in (ROOT / "planner" / "battle_policy.py").read_text())

bad = [n for n, ok in checks if not ok]
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

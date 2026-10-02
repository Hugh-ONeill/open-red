#!/usr/bin/env python3
"""NOTABLE: what more than one voice has mentioned, side by side.

Run 23 (2026-10-02) heard its rival in Cerulean ("I went to BILL's..."), a
Route 24 trainer ("You're going to see BILL?") and a Route 25 sign ("SEA
COTTAGE BILL lives here!"), each filed under its own room, and called Route 25
a dead end. User: "itd be neat if it could synthesize all the people
basically telling the player to go visit bill ... a notable ledger where
things that keep getting mentioned are grouped together like all the stuff
about the silph scope".
"""
import inspect
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


x = object.__new__(E.Executor)
x._hint_stands = lambda r, l: True
x.hints = {
    "CERULEAN_CITY|20,0": ["ZEKE: ZEKE: Hey, guess what? I went to BILL's and got him to show me his rare POKéMON!",
                           "CERULEANCITY_GUARD2: It's obvious that TEAM ROCKET is behind this!"],
    "ROUTE_25|10,2": ["ROUTE24_YOUNGSTER1: You're going to see BILL? First, let's fight!",
                      "SIGN_ROUTE_25_43_3: SEA COTTAGE BILL lives here!"],
    "POKEMON_TOWER_2F|9,2": ["POKEMONTOWER2F_CHANNELER: A SILPH SCOPE might be able to unmask them."],
    "POKEMON_TOWER_3F|9,1": ["POKEMONTOWER3F_CHANNELER1: The GHOSTs can be identified by the SILPH SCOPE."],
    "CELADON_CITY|2,1": ["SIGN_CELADON_CITY_27_21: ROCKET GAME CORNER The playground for grown-ups!",
                         "SIGN_CELADON_MANSION_2F_4_9: GAME FREAK Meeting Room"],
    "ROUTE_2|1,1": ["grind: ACE recovered by 20!", "grind: MOCHI recovered by 20!",
                    "OAKSLAB_GIRL: ACE, PROF.OAK is the authority!", "menu: MOCHI evolved!"],
}
obs = {"player_name": "ACE", "rival_name": "ZEKE", "party": [{"nickname": "MOCHI"}]}
t = x._notable_text(obs)
ck("BILL is one entry, from three voices", "BILL, from 3 different voices" in t, t)
ck("...the sign's longer phrase joined it", "SEA COTTAGE BILL lives here!" in t.split("BILL, from")[1].split("\n")[0])
ck("the Silph Scope lines are grouped", "SILPH SCOPE, from 2 different voices" in t, t)
ck("phrases that share no phrase stay apart (GAME FREAK is not the Game Corner)",
   "GAME FREAK" not in t, t)
ck("the run's own names are not things heard about", "ACE," not in t and "MOCHI" not in t, t)
ck("lines the harness filed under its own ops are not voices", "recovered by" not in t)
ck("a thing one voice said is not notable", "PROF.OAK" not in t)
# --- what happened since clears what was said before it ---
B = x.hints
x.hints_at = {r: {l: {"seq": 1} for l in ls} for r, ls in B.items()}
x._fired_at = {"EVENT_BEAT_ROUTE_24_TRAINER_0": 3}
ck("a trainer beaten does not clear anything", "BILL, from 3" in x._notable_text(obs))
x._fired_at["EVENT_MET_BILL"] = 4
ck("an event naming the thing, fired after its lines, clears them",
   "BILL, from" not in x._notable_text(obs), x._notable_text(obs))
x.hints_at["ROUTE_25|10,2"]["SIGN_ROUTE_25_43_3: SEA COTTAGE BILL lives here!"] = {"seq": 5}
x.hints_at["CERULEAN_CITY|20,0"]["ZEKE: ZEKE: Hey, guess what? I went to BILL's and got him to show me his rare POKéMON!"] = {"seq": 6}
ck("...but what is said after it keeps the thing alive", "BILL, from 2" in x._notable_text(obs))
ck("an item the bag holds leaves", "SILPH SCOPE" not in x._notable_text(dict(obs, bag={"SILPH_SCOPE": 1})))
ck("a line heard before firing order was kept is left as is",
   "SILPH SCOPE, from 2" in x._notable_text(obs))
src2 = (ROOT / "planner/executor.py").read_text()
ck("firing order is kept across attempts", '"fired_at":' in src2 and 'data.get("fired_at")' in src2
   and '"seq": int(getattr(self, "_fire_seq"' in src2)
x.hints = {"A|1,1": ["SOMEONE: just one BILL"]}
ck("nothing repeated, no section", x._notable_text(obs) == "")
src = inspect.getsource(E.Executor)
ck("it rides with what you were told elsewhere", "_nh = self._notable_text(obs)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

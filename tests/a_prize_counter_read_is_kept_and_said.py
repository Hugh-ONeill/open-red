#!/usr/bin/env python3
"""What a prize counter listed is kept, and said on the page and to every
rung, with the counters never opened named as such.

Run 53 (2026-10-12): the run opened the Game Corner's first prize counter
(ABRA, CLEFAIRY, NIDORINA, CANCEL) and said "the Secret Key is not listed";
the list was gone the next round, and the wording rung reworded the leg
"Purchase the Secret Key from the Game Corner" (user: "truly a troublesome
issue"). Mart shelves were kept; prize lists were not.

Synthetic: executor recorder on a stub, author text on a temp record.
"""
import json
import os
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


X = E.Executor
saved, logged = [], []
st = types.SimpleNamespace(_PRIZE_RE=X._PRIZE_RE, _prize_lists=None,
                           sightings={"GAME_CORNER_PRIZE_ROOM|0,3": [
                               "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_1",
                               "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_2",
                               "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_3",
                               "GAMECORNERPRIZEROOM_GAMBLER"]},
                           _save_memory=lambda: saved.append(1),
                           log=lambda k, **kw: logged.append((k, kw)))
V1 = "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_1"
det = (f"{V1} opened a prize list: 1=ABRA (180 coins), 2=CLEFAIRY (500 coins), "
       "3=NIDORINA (1200 coins), 4=CANCEL. Nothing was chosen and it is left OPEN.")
X._record_prize_list(st, "GAME_CORNER_PRIZE_ROOM|0,3", V1,
                     {"result": {"ok": True, "detail": det}})
ck("the op's words are kept by map and counter, CANCEL aside",
   st._prize_lists == {"GAME_CORNER_PRIZE_ROOM": {V1: [
       "ABRA (180 coins)", "CLEFAIRY (500 coins)", "NIDORINA (1200 coins)"]}},
   st._prize_lists)
ck("...logged and saved", logged and logged[-1][0] == "prize_list" and saved)
n0 = len(saved)
X._record_prize_list(st, "GAME_CORNER_PRIZE_ROOM|0,3", V1,
                     {"result": {"ok": True, "detail": det}})
ck("the same list read again writes nothing", len(saved) == n0)
V3 = "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_3"
X._record_prize_list(st, "GAME_CORNER_PRIZE_ROOM|0,3", V3,
                     {"result": {"ok": True, "detail": "ASKING ..."},
                      "ui": {"rows": ["1=TM23 (3300 coins)", "2=TM15 (5500 coins)",
                                      "3=CANCEL"]}})
ck("a list met only as the screen's rows is kept too",
   st._prize_lists["GAME_CORNER_PRIZE_ROOM"].get(V3) == ["TM_DRAGON_RAGE (TM23, 3300 coins)", "TM_HYPER_BEAM (TM15, 5500 coins)"],
   st._prize_lists)
X._record_prize_list(st, "CELADON_MART_1F|0,0", "CLERK",
                     {"result": {"ok": True, "detail": "opened a menu: 1=FLOOR 1F"},
                      "ui": {"rows": ["1=1F", "2=2F"]}})
ck("a menu with no coin rows is not a prize list", "CELADON_MART_1F" not in st._prize_lists)

line = X._prize_lists_line(st)
ck("the page line says each read counter's rows",
   "PRIZE COUNTERS YOU HAVE READ" in line and f"{V1} offered ABRA (180 coins)" in line, line)
ck("...and names the counter in that room never opened",
   "never read: TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_2" in line, line)

tmp = Path(tempfile.mkdtemp())
obs = tmp / "explored.json"
obs.write_text(json.dumps({"prize_lists": st._prize_lists, "sightings": st.sightings}))
t = A.prize_lists_text(obs)
ck("the author's text carries the same reads and the unopened counter",
   f"GAME_CORNER_PRIZE_ROOM, {V1}: ABRA (180 coins)" in t
   and "never opened: TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_2" in t, t)
ck("nothing recorded, nothing said", A.prize_lists_text(tmp / "none.json") == "")

src_a = (ROOT / "planner" / "author.py").read_text()
src_e = (ROOT / "planner" / "executor.py").read_text()
ck("the drafts' evidence, the counters text and the pull check all read it",
   "out += prize_lists_text(path)" in src_a
   and src_a.count("+ prize_lists_text())") == 1
   and "(prize_lists_text(observed) if observed else \"\")" in src_a)
ck("the record is kept across attempts",
   '"prize_lists": getattr(self, "_prize_lists", None) or {},' in src_e
   and 'for _m, _reads in (data.get("prize_lists") or {}).items()}' in src_e)
ck("the sweep's touch recorder and the model's own interact both call it",
   "self._record_prize_list(region, name, res_obs)" in src_e
   and 'self._record_prize_list(_hr, step["name"], obs)' in src_e)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

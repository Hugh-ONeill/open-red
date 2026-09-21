"""The starter question, asked the way the executor asks it, N times.
Uses the executor's own _road_ahead_text and _ask_offer_choice."""
import io, json, random, sys, time, collections
from pathlib import Path
sys.path.insert(0, "planner")
import executor as E
S = Path(sys.argv[1]); N = int(sys.argv[2])   # <scratch dir holding plans/outline.txt and run/outline_leg> <asks>
E.PLANS, E.RUN = S / "plans", S / "run"
ex = E.Executor.__new__(E.Executor)
ex.logf = io.StringIO(); ex.t0 = time.time()
ex.model = "gemma4:31b-it-q4_K_M"
ex._last_overworld_map = "OAKS_LAB"; ex._last_overworld_items = []
ASKED = [("ITEM_OAKS_LAB_6_3", "So! You want the fire POKéMON, CHARMANDER?"),
         ("ITEM_OAKS_LAB_7_3", "So! You want the water POKéMON, SQUIRTLE?"),
         ("ITEM_OAKS_LAB_8_3", "So! You want the plant POKéMON, BULBASAUR?")]
WHO = {"ITEM_OAKS_LAB_6_3": "CHARMANDER", "ITEM_OAKS_LAB_7_3": "SQUIRTLE",
       "ITEM_OAKS_LAB_8_3": "BULBASAUR", "none": "none"}
cur = {"party": [], "map": {"id": "OAKS_LAB"}}
said = ASKED[0][1]
goals = (ex._road_ahead_text(cur, said).replace(
    "Which of those the Pokemon this question names would answer is yours to judge",
    "Which of those each of these Pokemon would answer is yours to judge")
    .split("Also standing on this map:")[0].rstrip())
print("GOALS BLOCK AS ASKED:" + goals + "\n", flush=True)
picks, pos = collections.Counter(), collections.Counter()
rows = []
for i in range(N):
    order = list(ASKED); random.shuffle(order)
    r = ex._ask_offer_choice({"id": "pick_starter"}, cur, order, goals)
    if r is None:
        picks["unparsed"] += 1; print(i, "unparsed", flush=True); continue
    take, why = r
    p = [n for n, _ in order].index(take) + 1 if take != "none" else 0
    picks[WHO[take]] += 1; pos[p] += 1
    rows.append({"take": WHO[take], "pos": p, "order": [WHO[n] for n, _ in order], "why": why})
    print(i, WHO[take], f"listed #{p}", "|", why[:170], flush=True)
print("\nPICKS:", dict(picks)); print("LIST POSITION OF THE PICK:", dict(sorted(pos.items())))
json.dump(rows, open(S / "rows.json", "w"), indent=1)

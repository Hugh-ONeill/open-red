#!/usr/bin/env python3
"""The unreached-ground line says what no part reaches (run 18, 2026-09-28).

On Mt. Moon B2F each of two stood parts "reached" some of the other's seen
cells, which were simply the other part's own worked-out ground, and the
page sent the run from one to the other twenty times while Rocket 4 and the
(21,17) ladder sat in a third part neither reaches (user: "its just
pingponging between the other two areas of b2f"). Now a named part with no
unseen ground left says so, and the cells no stood part reaches are counted
and said to have no known way.

Synthetic: no game, no model."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                   # noqa: E402
import ledger as L                                     # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
HERE = "MT_MOON_B2F|27,5"
ex = E.Executor.__new__(E.Executor)
for _n, _v in dict(
        visits={HERE: 2}, explored={}, frontier={}, _no_cross={}, _no_cross_at={},
        _exit_tries={}, sightings={}, searched={}, dead_ends={}, _gone={}, seen_far={},
        blockers={}, _cut_bushes={}, map_forced={}, map_holes={}, door_dests={},
        _shelves={}, _shelf_machine=set(), _shelf_reads={}, _offered={}, _wild_lv={},
        _wild_seen={}, region_seen={}, frontier_here={}, touched={}, hints={}, hints_at={},
        _inert_objs={}, _outcomes={}, _touch_mark={}, _dead_ops={}, _dead_at={}, _dead_why={},
        _unreached_at={}, _region_mark={}, _plan_hist={}, _world_visits={}, _stuck_in={},
        _parts_by_map={}, region_anchors={}, _bad_seam=set(), _shut_settings={},
        _reach_settings={}, flag_sites={}, contested={}, _dry_walks={}, _ghost_said="",
        shut_doors={}, map_seen={}, _grind_exp={}, _retalked=set(), _cur_target="flag:EVENT_BEAT_MT_MOON_3_TRAINER_3",
        _mark_now=[5, 200, 20]).items():
    setattr(ex, _n, _v)
ex._where = lambda o: HERE
ex._route = lambda a, b: None
ex.log = lambda *a, **k: None

def page(n, frm):
    obs = {"mode": "overworld", "player": {"x": 27, "y": 5}, "bag": {},
           "map": {"id": "MT_MOON_B2F", "region": "27,5", "warps": [],
                   "connections": {}, "objects": [], "frontier": [],
                   "seen_unreached": {"n": n, "near": [{"x": 22, "y": 9}], "from": frm}}}
    return L.render(L.build(ex, obs, ex._cur_target), ex, obs, ex._cur_target)

t = page(311, [{"region": "MT_MOON_B2F|23,21", "n": 93}])
ck("the part that reaches some of it is still named",
   "MT_MOON_B2F|23,21 (reaches 93 of them" in t, t[:900])
ck("...and said to be all on screen when it has no unseen ground left",
   "; all of its ground has been on screen — that count is its own floor, "
   "already walked: going back finds nothing new)" in t, t[:900])
ck("...and the rest are said to be reached by no part",
   "the other 218 no part you have stood in reaches" in t, t[:900])
ex.region_seen = {"MT_MOON_B2F|23,21": 4}
t = page(311, [{"region": "MT_MOON_B2F|23,21", "n": 93}])
ck("a named part with unseen ground left is not called finished",
   "all of its ground has been on screen" not in t, t[:900])
# run 37, 2026-10-05: the kept count stays positive while the floor has
# unseen ground anywhere, but the reading taken INSIDE the part is 0
ex.frontier_here = {"MT_MOON_B2F|23,21": 0}
t = page(311, [{"region": "MT_MOON_B2F|23,21", "n": 93}])
ck("a part worked from within is called finished whatever its kept count",
   "all of its ground has been on screen — that count is its own floor" in t, t[:900])
ex.frontier_here = {"MT_MOON_B2F|23,21": 3}
t = page(311, [{"region": "MT_MOON_B2F|23,21", "n": 93}])
ck("...but not one with ground still to see from within",
   "all of its ground has been on screen" not in t, t[:900])
ex.frontier_here = {}
t = page(93, [{"region": "MT_MOON_B2F|23,21", "n": 93}])
ck("when a stood part reaches all of it, nothing is said of the rest",
   "no part you have stood in reaches" not in t, t[:900])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

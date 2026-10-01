#!/usr/bin/env python3
"""Ask the model, once, every learn-move question an arena room can raise,
and keep its answers in plans/arena_learn.json.

A savepoint room never asks the model anything (policy_author), so a level-up
offer to a member that already knows four moves fell back to keeping the old
moves in every trial. The offers are the same every time — the room starts
from a fixed party — so the model's answer to each is asked here, with the
live question (Executor.FORGET_SYS and _forget_user, the facts the summary
screen shows), and the room plays it (Executor.LEARN_TABLE). User,
2026-10-01: "we can do what the model pre-chooses as that table".

  tools/arena_learn_table.py                   # every room, offers within 5 levels
  tools/arena_learn_table.py --rooms e4_real --levels 3 --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
OUT = ROOT / "plans/arena_learn.json"
GEN = Path.home() / "Developer/gen1recomp/data/generated"

_DUMP = r'''
local P = dofile(arg[1] .. "/pokemon.lua")
local M = dofile(arg[1] .. "/moves.lua")
local function esc(s) return (tostring(s):gsub('"', '\\"')) end
io.write("{\"species\":{")
local first = true
for id, p in pairs(P) do
  if type(p) == "table" and p.learnset then
    if not first then io.write(",") end; first = false
    io.write(('"%s":{"types":['):format(esc(id)))
    for i, t in ipairs(p.types or {}) do io.write((i > 1 and "," or "") .. '"' .. esc(t) .. '"') end
    io.write('],"learnset":[')
    for i, e in ipairs(p.learnset) do
      io.write((i > 1 and "," or "") .. ('[%d,"%s"]'):format(e.level, esc(e.move)))
    end
    io.write("]}")
  end
end
io.write("},\"moves\":{")
first = true
for id, m in pairs(M) do
  if type(m) == "table" then
    if not first then io.write(",") end; first = false
    io.write(('"%s":{"type":"%s","power":%d,"pp":%d}'):format(
      esc(id), esc(m.type or ""), tonumber(m.power) or 0, tonumber(m.pp) or 0))
  end
end
io.write("}}")
'''


def game_data() -> dict:
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(_DUMP)
    r = subprocess.run(["lua", f.name, str(GEN)], capture_output=True, text=True)
    Path(f.name).unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit("could not read the game's data: " + r.stderr[-300:])
    return json.loads(r.stdout)


def shown(mid: str, moves: dict, cur_pp=None) -> str:
    """A move as the summary screen shows it (executor _maybe_forget._shown)."""
    m = moves.get(mid) or {}
    bits = [str(m.get("type")).upper()] if m.get("type") else []
    if m.get("power"):
        bits.append(f"power {m['power']}")
    if m.get("pp"):
        bits.append(f"PP {cur_pp}/{m['pp']}" if cur_pp is not None else f"PP {m['pp']}")
    return mid + (f" ({', '.join(bits)})" if bits else "")


def room_goal(name: str, kind: str, spec: dict) -> str:
    if kind == "catch":
        cfg = spec.get("catch") or {}
        named = " or ".join([f"{t} type" for t in cfg.get("want_types") or []]
                            + list(cfg.get("want_species") or []))
        return f"Catch a {named} Pokemon"          # the room's own subgoal text
    if kind == "e4":
        return "Defeat the Elite Four and the Champion"
    where = (spec.get("start") or {}).get("map") or name
    return f"Win the badge at {where}"


def offers(spec: dict, data: dict, levels: int) -> list:
    """(member, offered move, level) for every member, in level order: every
    move its learnset brings within `levels`, whether or not it will be a
    question (a free slot learns without one; see walk_member)."""
    out = []
    for m in spec.get("party") or []:
        sp = (data["species"].get(str(m.get("species"))) or {})
        known = [str(x if not isinstance(x, dict) else x.get("id")) for x in m.get("moves") or []]
        lv = int(m.get("level") or 0)
        for at, mv in sorted(sp.get("learnset") or [], key=lambda e: e[0]):
            if lv < at <= lv + levels and mv not in known:
                out.append((m, mv, at))
    return out


def walk_member(m: dict, its_offers: list, answer) -> list:
    """ONE MEMBER'S OFFERS, EACH ON THE MOVESET THE LAST ONE LEFT (user,
    2026-10-01: "so kadabra can learn psychic and then reflect having psychic
    known already"). A free slot takes the move without a question, as the
    game does; a full one is asked `answer(known, mv, at)` -> the move to
    forget or None, and the answer is applied before the next offer. The
    rooms play the table in the same order: a member reaches level 38
    before 42. Returns [(mv, at, forget or None, why, asked)]."""
    known = [str(x if not isinstance(x, dict) else x.get("id")) for x in m.get("moves") or []]
    out = []
    for _m, mv, at in its_offers:
        if mv in known:
            continue
        if len(known) < 4:
            known.append(mv)
            out.append((mv, at, None, "a free slot: learned without a question", False))
            continue
        forget, why = answer(list(known), mv, at)
        if forget in known:
            known[known.index(forget)] = mv
        else:
            forget = None
        out.append((mv, at, forget, why, True))
    return out


def ask(model: str, who: str, types: str, new: str, shown_known: list, goal: str):
    import brock_probe
    from executor import Executor
    user = Executor._forget_user(who, types, new, shown_known, goal)
    reply = brock_probe.chat([{"role": "system", "content": Executor.FORGET_SYS},
                              {"role": "user", "content": user}], model)
    d = Executor._first_object(reply or "") or {}
    return d, user


def main(argv=None):
    import policy_author as PA
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rooms", default="", help="comma-separated; default every room with a spec")
    ap.add_argument("--levels", type=int, default=5, help="offers within this many levels")
    ap.add_argument("--model", default="gemma4:31b-it-q4_K_M")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = game_data()
    rooms = [r for r in (a.rooms.split(",") if a.rooms else sorted(PA.ARENAS)) if r]
    table = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name in rooms:
        kind, _save, spec_path = PA.ARENAS.get(name, (None, None, None))
        if not spec_path or not Path(spec_path).exists():
            continue
        spec = json.loads(Path(spec_path).read_text())
        rows = {}                       # a room's rows are rebuilt, never merged
        allof = offers(spec, data, a.levels)
        for m in spec.get("party") or []:
            mine = [o for o in allof if o[0] is m]
            if not mine:
                continue
            sp = str(m.get("species"))
            types = "/".join((data["species"].get(sp) or {}).get("types") or [])

            def answer(known, mv, at, _m=m, _sp=sp, _types=types):
                line = f"{name}: {_sp} L{_m.get('level')} -> {mv} at L{at}, knowing {', '.join(known)}"
                if a.dry_run:
                    print(line)
                    return None, ""
                d, _user = ask(a.model, str(_m.get("nickname") or _sp), _types,
                               shown(mv, data["moves"]),
                               [shown(k, data["moves"], (data["moves"].get(k) or {}).get("pp"))
                                for k in known], room_goal(name, kind, spec))
                f = d.get("forget")
                f = str(f).upper().replace(" ", "_") if f is not None else None
                why = str(d.get("why") or "")[:200]
                print(f"{line}: forget {f if f in known else '(keep the old moves)'} — {why[:120]}",
                      flush=True)
                return (f if f in known else None), why

            for mv, at, forget, why, asked in walk_member(m, mine, answer):
                if asked:
                    rows[f"{sp}|{mv}"] = {"forget": forget, "why": why, "level": at}
        if rows:
            table[name] = rows
        else:
            table.pop(name, None)
    if not a.dry_run:
        OUT.write_text(json.dumps(table, indent=1, sort_keys=True) + "\n")
        print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

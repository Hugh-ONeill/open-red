#!/usr/bin/env python3
"""Ask the model, once, what types every species is, and keep its answers in
plans/arena_types.json.

A battle screen never shows a foe's types (planner/type_ledger.py). A live
run asks the model the first time it meets a species (Executor._ask_types);
a savepoint room asks nobody, so the same question is asked here, with the
live prompt, and the room plays on the model's word (policy_author). What
the model gets wrong stays wrong in the rooms too, as it would in a run.

  tools/arena_types_table.py                 # every species
  tools/arena_types_table.py --model qwen3:32b --only ONIX,GEODUDE
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
OUT = ROOT / "plans/arena_types.json"


def main(argv=None):
    import brock_probe
    import executor as E
    import type_ledger
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma4:31b-it-q4_K_M")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    names = sorted(E.Executor._species_names())
    if a.only:
        names = [n for n in a.only.split(",") if n]
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    for sp in names:
        if sp in have and not a.only:
            continue
        reply = brock_probe.chat(
            [{"role": "system", "content": E.Executor.TYPES_SYS},
             {"role": "user", "content": f"THE POKEMON: {sp}"}], a.model)
        d = E.Executor._first_object(reply or "") or {}
        got = d.get("types")
        got = [got] if isinstance(got, str) else (got or [])
        ts = [x for x in (type_ledger.norm_type(t) for t in got) if x][:2]
        print(f"{sp}: {ts or '(none)'}", flush=True)
        if ts:
            have[sp] = ts
            OUT.write_text(json.dumps(have, indent=1, sort_keys=True))
    print(f"{len(have)} species in {OUT}")


if __name__ == "__main__":
    main()

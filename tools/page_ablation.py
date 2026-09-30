#!/usr/bin/env python3
"""Which sections of the escalation page change the model's decision?

Usage counts are the wrong meter (user, 2026-09-29: a critical line may be
consulted "once in a blue moon", and where it sits changes how often it is
read). This asks recorded rounds AGAIN, exactly as they were asked, with one
section of the page taken out, and with it moved to the top, several times
each, and counts how often the decision changes beyond the round's own
spread when asked unchanged.

Reads run/prompts.jsonl.gz (the executor journals every escalation prompt,
whole, since 2026-09-30) and run/prompt_sys/. Writes only to --out, never
under run/ or plans/. Same model, same num_ctx as the run; do not run it
beside a live chain (it refuses unless --force).

  tools/page_ablation.py --dry-run                 # what it would ask, and the cost
  tools/page_ablation.py --out ~/ablation/r20      # ask (resumable)
  tools/page_ablation.py --out ~/ablation/r20 --report

Picking rounds: PIVOTS are rounds whose first op is a different kind from
the round before in the same step (the plan changed course); BEFORE adds the
round just ahead of each pivot; CONTROLS are a seeded random sample of the
rest. --rounds takes record indexes by hand instead.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

# the parts of the prompt that are the question itself, never measured
FIXED = ("SUBGOAL", "DONE_WHEN", "CURRENT_OBSERVATION", "AUTHOR THE OP")

_HEAD = re.compile(r"^[A-Z][A-Z0-9'’&/()_\-]*(?:[ ,][A-Z0-9'’&/()_\-|.,:]+){1,}")


def load(path: Path) -> list:
    out = []
    with gzip.open(path, "rt") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            r["_i"] = len(out)
            out.append(r)
    return out


# the prompt's own frame (executor escalate): each is a section of its own
# whatever follows it on the line (CURRENT_OBSERVATION: {json...})
KNOWN = ("SUBGOAL:", "DONE_WHEN:", "ATLAS", "FEEDBACK FROM YOUR LAST MACRO",
         "CURRENT_OBSERVATION:", "Author the op-list", "FLY GOES ONLY TO",
         "THIS PLACE, AS IT IS DRAWN", "(last_text is")


def label_of(line: str) -> str:
    """A section's name: the capitalised words its header starts with, up to
    a colon, with numbers dropped, so the same section is one name across
    rounds."""
    for k in KNOWN:
        if line.startswith(k):
            return {"Author the op-list": "AUTHOR THE OP-LIST",
                    "(last_text is": "LAST_TEXT NOTE"}.get(
                        k, k.rstrip(":").replace(",", ""))
    words = []
    for w in re.split(r"[ ,]+", line.strip()):
        if words and words[-1].endswith(":"):
            break
        w2 = w.strip(":.,—()")
        if not w2 or any(c.isdigit() for c in w2):
            if words:
                break
            continue
        if not (w2.isupper() and len(w2) >= 2) and w2 not in ("A", "I"):
            break
        words.append(w2 + (":" if w.endswith(":") else ""))
        if len(words) >= 5:
            break
    return " ".join(words).rstrip(":")


def split_sections(user: str) -> list:
    """[(label, text)] in order; a section starts at an unindented line that
    opens with capitalised words, and runs to the next one."""
    secs = []
    for line in user.split("\n"):
        if line and not line[0].isspace() and (
                line.startswith(KNOWN) or (_HEAD.match(line) and label_of(line))):
            secs.append([label_of(line), line + "\n"])
        elif secs:
            secs[-1][1] += line + "\n"
        else:
            secs.append(["(head)", line + "\n"])
    if secs:
        secs[-1][1] = secs[-1][1][:-1]      # the join added one newline too many
    return [(a, b) for a, b in secs]


def is_fixed(label: str) -> bool:
    return label == "(head)" or any(label.startswith(f) for f in FIXED)


def variants(user: str) -> list:
    """(label, kind, text) for every measurable section: taken out, and
    moved up to sit right after the question (SUBGOAL / DONE_WHEN)."""
    secs = split_sections(user)
    head_end = 0
    for j, (lab, _t) in enumerate(secs):
        if lab.startswith(("SUBGOAL", "DONE_WHEN")) or lab == "(head)":
            head_end = j + 1
        else:
            break
    out, seen = [], set()
    for j, (lab, _t) in enumerate(secs):
        if is_fixed(lab) or lab in seen:
            continue
        seen.add(lab)
        idx = [k for k, (l2, _x) in enumerate(secs) if l2 == lab]
        rest = [s for k, s in enumerate(secs) if k not in idx]
        out.append((lab, "remove", "".join(t for _l, t in rest)))
        if min(idx) > head_end:
            moved = [secs[k] for k in idx]
            top = rest[:head_end] + moved + rest[head_end:]
            out.append((lab, "top", "".join(t for _l, t in top)))
    return out


def signature(reply: str):
    """The decision, as the executor would read it: the first two ops, each
    by kind and what it is aimed at."""
    from executor import Executor
    try:
        ops, _plan = Executor._parse_macro(reply or "")
    except Exception:
        ops = None
    if not ops:
        return ("unparsed",)
    sig = []
    for o in ops[:2]:
        tgt = (o.get("name") or o.get("map") or o.get("item") or o.get("move")
               or o.get("dir") or o.get("until")
               or (f"{o.get('x')},{o.get('y')}" if o.get("x") is not None else ""))
        sig.append(f"{o.get('op')}:{tgt}")
    return tuple(sig)


def pick(recs: list, spec: str, seed: int) -> list:
    want = dict(p.split("=") for p in spec.split(",") if "=" in p)
    n_piv, n_ctl = int(want.get("pivots", 8)), int(want.get("controls", 4))
    before = int(want.get("before", 1))
    kinds = [((signature(r.get("reply"))[0]).split(":")[0]) for r in recs]
    piv = [i for i in range(1, len(recs))
           if recs[i].get("subgoal") == recs[i - 1].get("subgoal")
           and kinds[i] != kinds[i - 1] and not recs[i].get("think")]
    rng = random.Random(seed)
    piv = sorted(rng.sample(piv, min(n_piv, len(piv))))
    chosen = {i: "pivot" for i in piv}
    if before:
        for i in piv:
            if i - 1 not in chosen and not recs[i - 1].get("think"):
                chosen[i - 1] = "before"
    rest = [i for i in range(len(recs)) if i not in chosen and not recs[i].get("think")]
    for i in rng.sample(rest, min(n_ctl, len(rest))):
        chosen[i] = "control"
    return sorted(chosen.items())


WEIGHT = {"pivot": 2.0, "before": 1.5, "control": 1.0, "hand": 1.0}


def chain_running() -> bool:
    try:
        ps = subprocess.run(["ps", "-eo", "args"], capture_output=True,
                            text=True).stdout
    except OSError:
        return False
    return any(("fresh_discovery.sh" in l or "planner/executor.py" in l)
               and "grep" not in l for l in ps.splitlines())


def ask(sysp: str, user: str, model: str):
    import brock_probe
    t = time.time()
    reply = brock_probe.chat([{"role": "system", "content": sysp},
                              {"role": "user", "content": user}], model)
    return reply, round(time.time() - t, 1)


def report(out: Path) -> str:
    rows = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines() if l.strip()]
    base = {}
    for r in rows:
        if r["kind"] == "base":
            base.setdefault(r["rec"], []).append(tuple(r["sig"]))
    # the round's own spread: how often an unchanged ask lands outside the
    # other unchanged asks
    noise = {}
    for rec, sigs in base.items():
        miss = sum(1 for k, s in enumerate(sigs)
                   if s not in (sigs[:k] + sigs[k + 1:]))
        noise[rec] = miss / len(sigs) if len(sigs) > 1 else 0.0
    agg = {}
    for r in rows:
        if r["kind"] == "base" or r["rec"] not in base:
            continue
        key = (r["label"], r["kind"])
        a = agg.setdefault(key, {"w": 0.0, "wc": 0.0, "rounds": set(), "n": 0,
                                 "piv": 0})
        changed = tuple(r["sig"]) not in base[r["rec"]]
        w = WEIGHT.get(r["why"], 1.0)
        a["w"] += w
        a["wc"] += w * (float(changed) - noise[r["rec"]])
        a["rounds"].add(r["rec"])
        a["n"] += 1
        a["piv"] += int(changed and r["why"] in ("pivot", "before"))
    lines = [f"{len(base)} round(s); own spread (unchanged asks landing apart): "
             f"mean {sum(noise.values()) / max(1, len(noise)):.2f}",
             "", f"{'section':44} {'variant':7} {'rounds':>6} {'asks':>5} "
             f"{'changed-over-spread':>20} {'pivotal changes':>16}"]
    for (lab, kind), a in sorted(agg.items(), key=lambda kv: -(kv[1]["wc"] / max(kv[1]["w"], 1e-9))):
        lines.append(f"{lab[:44]:44} {kind:7} {len(a['rounds']):>6} {a['n']:>5} "
                     f"{a['wc'] / max(a['w'], 1e-9):>+20.2f} {a['piv']:>16}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--prompts", type=Path, default=ROOT / "run/prompts.jsonl.gz")
    ap.add_argument("--sys-dir", type=Path, default=ROOT / "run/prompt_sys")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--pick", default="pivots=8,before=1,controls=4")
    ap.add_argument("--rounds", default="", help="record indexes, comma-separated")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--variants", default="remove,top")
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.report:
        print(report(a.out))
        return
    recs = load(a.prompts)
    if a.rounds:
        chosen = [(int(x), "hand") for x in a.rounds.split(",") if x.strip()]
    else:
        chosen = pick(recs, a.pick, a.seed)
    kinds = set(a.variants.split(","))
    plan = []
    for i, why in chosen:
        vs = [v for v in variants(recs[i]["user"]) if v[1] in kinds]
        plan.append((i, why, vs))
    calls = sum(a.samples * (1 + len(vs)) for _i, _w, vs in plan)
    secs = sum(1 for _ in plan)
    print(f"{secs} round(s) of {len(recs)}, {calls} model call(s), "
          f"~{calls * 33 / 3600:.1f} h at the run's ~33 s a round")
    for i, why, vs in plan:
        r = recs[i]
        print(f"  #{i} {why:7} {r.get('subgoal')} r{r.get('round')} at {r.get('at')}: "
              f"{len({v[0] for v in vs})} section(s), first op {signature(r.get('reply'))}")
    if a.dry_run:
        return
    if not a.out:
        sys.exit("--out is required to ask")
    out = a.out.resolve()
    for forbidden in (ROOT / "run", ROOT / "plans"):
        if out == forbidden.resolve() or forbidden.resolve() in out.parents:
            sys.exit(f"--out must not be under {forbidden}")
    if chain_running() and not a.force:
        sys.exit("the chain (or an executor) is running; this shares its model "
                 "and GPU — stop it first, or pass --force")
    out.mkdir(parents=True, exist_ok=True)
    nc = next((r.get("num_ctx") for r in recs if r.get("num_ctx")), None)
    if nc:
        os.environ["RED_NUM_CTX"] = str(nc)
    resf = out / "results.jsonl"
    done = set()
    if resf.exists():
        for l in resf.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                done.add((d["rec"], d["label"], d["kind"], d["k"]))
    made = 0
    with resf.open("a") as f:
        for i, why, vs in plan:
            r = recs[i]
            sysp = (a.sys_dir / f"{r['sys']}.txt").read_text()
            jobs = [("(unchanged)", "base", r["user"])] + list(vs)
            for lab, kind, text in jobs:
                for k in range(a.samples):
                    if (i, lab, kind, k) in done:
                        continue
                    if a.max_calls and made >= a.max_calls:
                        print(f"stopped at --max-calls {a.max_calls}; run again to resume")
                        return
                    reply, dt = ask(sysp, text, r.get("model"))
                    sig = signature(reply)
                    f.write(json.dumps({"rec": i, "why": why, "label": lab,
                                        "kind": kind, "k": k, "sig": list(sig),
                                        "s": dt}) + "\n")
                    f.flush()
                    made += 1
                    print(f"  #{i} {kind:6} {lab[:40]:40} {k}: {sig} ({dt}s)", flush=True)
    print(report(out))


if __name__ == "__main__":
    main()

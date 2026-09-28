#!/usr/bin/env python3
"""Does thinking make the AUTHOR write better plans? An offline A/B.

The author thinks from a leg's third plan onward (campaign.sh,
RED_AUTHOR_THINK_FROM=3) at ~7.5x the cost (290.8 s vs 38.6 s, 2026-09-12),
and nothing has ever measured whether the plans it writes are better. This
freezes a real authoring moment and replays it both ways.

  author_ab.py snapshot CASE --goal "Reach Vermilion City"   # freeze now
  author_ab.py run CASE --n 3                                # think off/on
  author_ab.py report [CASE ...]

snapshot   copies what the author reads from run/ (obs, explored, seen,
           last_state, the journal, the outline_* / leg_* bookkeeping) and a
           private copy of plans/ into ~/.local/state/red-recomp/author_ab/CASE,
           symlinks the rest of the repo, then runs author.py's own main()
           there with campaign.sh's arguments and the model call swapped for a
           recorder: the first prompt it would send is saved as prompt.json and
           nothing is asked. --start defaults to planner/state_text.py, as in
           campaign.sh.
run        sends that exact prompt with think off and on, N times each, at the
           draft temperature (DRAW_TEMP, 0.8), and scores every reply with the
           author's own checks (validate + the four refusal checks it runs
           before accepting a plan). Refuses while the chain is up: the two
           would share one GPU and both measurements would be wrong.
report     per case and arm: valid first replies, time, tokens, and each
           plan's route (the maps its done_when conditions name), for a person
           to judge against what actually worked.

Writes nothing under the repo's run/ or plans/.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

# the chain's window: brock_probe defaults to 24576 when unset, and a different
# num_ctx both reloads the model and changes how the author sizes its prompt
os.environ.setdefault("RED_NUM_CTX", "32768")
REPO = Path(__file__).resolve().parents[1]
ROOT = Path(os.path.expanduser("~/.local/state/red-recomp/author_ab"))
MODEL = os.environ.get("RED_AUTHOR_MODEL") or os.environ.get("RED_MODEL") or "gemma4:31b-it-q4_K_M"

# what the author (and state_text / part_names / ledger) read out of run/
RUN_KEEP = re.compile(r"^(obs\.json|explored\.json|seen\.json|last_state\.json|executor_log\.jsonl|"
                      r"attempt_yield|self_ko\.json|leg_start\.(json|leg)|leg_unconfirmed|"
                      r"outline_(leg|void|pushes|push_with|pulls_failed|reorders|skips|inserts|"
                      r"rewordings|wordings_reverted|wording_asked))$")


class _Captured(Exception):
    pass


def chain_up():
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    return any(re.match(r"(python[0-9.]* .*planner/executor\.py|bash \./(fresh_discovery|campaign|fresh_run)\.sh)", l)
               for l in out.splitlines())


def case_dir(name):
    return ROOT / name


# ------- snapshot

def snapshot(name, goal, start=None, force=False):
    d = case_dir(name)
    if d.exists():
        if not force:
            sys.exit(f"{d} exists (use --force to replace)")
        shutil.rmtree(d)
    d.mkdir(parents=True)
    (d / "run").mkdir()
    n = 0
    for f in (REPO / "run").iterdir():
        if f.is_file() and RUN_KEEP.match(f.name):
            shutil.copy2(f, d / "run" / f.name)
            n += 1
    shutil.copytree(REPO / "plans", d / "plans", symlinks=True)
    for entry in REPO.iterdir():
        if entry.name not in ("run", "plans", ".git"):
            (d / entry.name).symlink_to(entry)
    if start is None:
        start = subprocess.run([sys.executable, "planner/state_text.py"], cwd=d,
                               capture_output=True, text=True, timeout=120).stdout.strip()
    prompt = capture_prompt(d, goal, start)
    meta = {"case": name, "goal": goal, "start": start, "model": MODEL, "created": time.time(),
            "run_files": n, "draw_temp": prompt.get("temp")}
    (d / "case.json").write_text(json.dumps(meta, indent=1))
    (d / "prompt.json").write_text(json.dumps(prompt))
    chars = sum(len(m["content"]) for m in prompt["messages"])
    print(f"{name}: {n} run files, prompt {chars} chars "
          f"({len(prompt['messages'])} messages), start: {start[:100]}...")


def capture_prompt(d, goal, start):
    """author.py's main(), exactly as campaign.sh calls it for a rewrite, with
    brock_probe.chat replaced by a recorder that keeps the first call and stops."""
    code = f"""
import json, sys, os
sys.path.insert(0, "planner")
import brock_probe
class _Captured(Exception): pass
def fake(msgs, model, retries=2, think=False, temp=None):
    json.dump({{"messages": msgs, "think": think, "temp": temp}}, open("prompt.captured.json", "w"))
    raise _Captured()
brock_probe.chat = fake
import author
sys.argv = ["author.py", "--goal", {goal!r}, "--start", {start!r}, "--out", "plan_out.json",
            "--model", {MODEL!r}, "--observed", "run/explored.json", "--journal", "run/executor_log.jsonl"]
try:
    author.main()
except _Captured:
    pass
except SystemExit:
    pass
"""
    r = subprocess.run([sys.executable, "-c", code], cwd=d, capture_output=True, text=True, timeout=600)
    cap = d / "prompt.captured.json"
    if not cap.exists():
        sys.exit("the author sent no model call; its output:\n" + (r.stdout + r.stderr)[-2000:])
    prompt = json.loads(cap.read_text())
    cap.unlink()
    return prompt


# ------- run

def score(d, reply):
    """The author's own acceptance test, run in the case's frozen world."""
    code = """
import json, re, sys
sys.path.insert(0, "planner")
import author
reply = sys.stdin.read()
m = re.search(r"\\{.*\\}", reply, re.S)
out = {"parsed": False, "problems": [], "route": [], "steps": 0}
if m:
    try:
        plan = json.loads(m.group(0))
        out["parsed"] = True
    except json.JSONDecodeError as e:
        out["problems"] = ["invalid JSON: %s" % e]
        plan = None
    if plan is not None:
        try:
            author.normalize_items(plan)
            probs = (author.validate(plan) or author.witness_already_true_problems(plan)
                     or author.held_step_problems(plan) or author.machine_slot_problems(plan)
                     or author.through_a_place_problems(plan))
            out["problems"] = list(probs or [])
        except Exception as e:
            out["problems"] = ["checker raised %s: %s" % (type(e).__name__, e)]
        subs = plan.get("subgoals") or []
        out["steps"] = len(subs)
        for s in subs:
            dw = s.get("done_when") or {}
            if isinstance(dw, dict) and dw.get("map"):
                out["route"].append(dw["map"])
else:
    out["problems"] = ["no JSON object in the reply"]
print(json.dumps(out))
"""
    r = subprocess.run([sys.executable, "-c", code], cwd=d, input=reply, capture_output=True,
                       text=True, timeout=300)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"parsed": False, "problems": ["scorer failed: " + (r.stderr or "")[-300:]],
                "route": [], "steps": 0}


def run(name, n, arms, force=False):
    if chain_up() and not force:
        sys.exit("the chain is running; this needs the GPU to itself (--force to override)")
    d = case_dir(name)
    prompt = json.loads((d / "prompt.json").read_text())
    sys.path.insert(0, str(REPO / "planner"))
    os.environ["RED_RUN_DIR"] = str(d / "run")      # a thinking call's live file stays in the case
    import brock_probe as B
    out = d / "results.jsonl"
    temp = prompt.get("temp")
    for i in range(n):
        for arm in arms:                              # interleaved, so drift hits both arms alike
            if chain_up() and not force:
                print("the chain came up; stopping here so it has the GPU", flush=True)
                return
            think = arm == "on"
            t = time.time()
            try:
                reply = B.chat(prompt["messages"], MODEL, think=think, temp=temp)
                err = None
            except Exception as e:
                reply, err = "", f"{type(e).__name__}: {e}"
            wall = time.time() - t
            last = dict(B.LAST or {})
            s = score(d, reply) if not err else {"parsed": False, "problems": [err], "route": [], "steps": 0}
            rec = {"t": t, "arm": arm, "i": i, "wall": round(wall, 1), "gtok": last.get("gtok"),
                   "ptok": last.get("ptok"), "think_chars": last.get("think_chars"),
                   "valid": s["parsed"] and not s["problems"], **s, "reply": reply,
                   "thinking": last.get("thinking", "")}
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{name} {arm:3s} #{i + 1}: {'VALID' if rec['valid'] else 'invalid'} "
                  f"{wall:6.1f}s {rec['gtok']} tok  route: {' > '.join(s['route'])[:90]}"
                  + ("" if rec["valid"] else f"  | {(s['problems'] or ['?'])[0][:110]}"), flush=True)


# ------- report

def report(names):
    names = names or sorted(p.name for p in ROOT.iterdir() if (p / "results.jsonl").exists())
    for name in names:
        d = case_dir(name)
        meta = json.loads((d / "case.json").read_text())
        rows = [json.loads(l) for l in open(d / "results.jsonl")] if (d / "results.jsonl").exists() else []
        print(f"\n== {name}: {meta['goal']}")
        for arm in ("off", "on"):
            r = [x for x in rows if x["arm"] == arm]
            if not r:
                continue
            v = sum(x["valid"] for x in r)
            print(f"  think {arm:3s}  n={len(r)}  valid first reply {v}/{len(r)}  "
                  f"median {statistics.median(x['wall'] for x in r):.0f}s  "
                  f"{statistics.median(x['gtok'] or 0 for x in r):.0f} tok")
            for x in r:
                print(f"     {'ok ' if x['valid'] else 'BAD'} {' > '.join(x['route'])[:100]}"
                      + ("" if x["valid"] else f"   [{(x['problems'] or ['?'])[0][:80]}]"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("case")
    s.add_argument("--goal", required=True)
    s.add_argument("--start")
    s.add_argument("--force", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("case")
    r.add_argument("--n", type=int, default=3)
    r.add_argument("--arms", default="off,on")
    r.add_argument("--force", action="store_true")
    p = sub.add_parser("report")
    p.add_argument("cases", nargs="*")
    a = ap.parse_args()
    if a.cmd == "snapshot":
        snapshot(a.case, a.goal, a.start, a.force)
    elif a.cmd == "run":
        run(a.case, a.n, a.arms.split(","), a.force)
    else:
        report(a.cases)


if __name__ == "__main__":
    main()

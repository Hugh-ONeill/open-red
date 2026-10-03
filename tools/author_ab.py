#!/usr/bin/env python3
"""Does thinking make the AUTHOR write better plans? An offline A/B.

The author thinks from a leg's third plan onward (campaign.sh,
RED_AUTHOR_THINK_FROM=3) at ~7.5x the cost (290.8 s vs 38.6 s, 2026-09-12),
and nothing has ever measured whether the plans it writes are better. This
freezes a real authoring moment and replays it both ways.

  author_ab.py snapshot CASE --goal "Reach Vermilion City"   # freeze now
  author_ab.py run CASE --n 3                                # think off/on
  author_ab.py report [CASE ...]
  author_ab.py snapshot CASE2 --from CASE --goal "..."       # same frozen world, new goal
  author_ab.py prompts CASE                                  # recapture with today's code
  author_ab.py run CASE --n 5 --arms nomap,map               # printed map without/with

THE PRINTED-MAP ARMS (2026-09-28, audit PT-17b). Every snapshot also saves
prompt.nomap.json, captured under RED_PRINTED_MAP=bag (the old TOWN_MAP item
gate); arms "map" and "nomap" send prompt.json / prompt.nomap.json with
think off and score each under its own setting, so the only difference is
whether the author was shown the printed map.

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
run --full the WHOLE authoring pass per sample, as campaign.sh runs it
           (author.py main(): drafts, picker, review, the retry rounds with the
           validator's feedback), each in a fresh copy of the frozen case so no
           run sees another's drafts; scored on the plan it finally writes.
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

def snapshot(name, goal, start=None, force=False, from_case=None):
    src = case_dir(from_case) if from_case else REPO
    if from_case and not (src / "run").is_dir():
        sys.exit(f"no case {from_case}")
    d = case_dir(name)
    if d.exists():
        if not force:
            sys.exit(f"{d} exists (use --force to replace)")
        shutil.rmtree(d)
    d.mkdir(parents=True)
    (d / "run").mkdir()
    n = 0
    for f in (src / "run").iterdir():
        if f.is_file() and RUN_KEEP.match(f.name):
            shutil.copy2(f, d / "run" / f.name)
            n += 1
    shutil.copytree(src / "plans", d / "plans", symlinks=True)
    for entry in REPO.iterdir():
        if entry.name not in ("run", "plans", ".git"):
            (d / entry.name).symlink_to(entry)
    if start is None:
        start = subprocess.run([sys.executable, "planner/state_text.py"], cwd=d,
                               capture_output=True, text=True, timeout=120).stdout.strip()
    prompt = capture_prompt(d, goal, start)
    meta = {"case": name, "goal": goal, "start": start, "model": MODEL, "created": time.time(),
            "run_files": n, "draw_temp": prompt.get("temp"), "from": from_case}
    (d / "case.json").write_text(json.dumps(meta, indent=1))
    (d / "prompt.json").write_text(json.dumps(prompt))
    (d / "prompt.nomap.json").write_text(json.dumps(capture_prompt(d, goal, start, nomap=True)))
    chars = sum(len(m["content"]) for m in prompt["messages"])
    print(f"{name}: {n} run files, prompt {chars} chars "
          f"({len(prompt['messages'])} messages), start: {start[:100]}...")


def prompts(name):
    """Recapture both prompts from a case's frozen world with today's code."""
    d = case_dir(name)
    meta = json.loads((d / "case.json").read_text())
    for fn, nm in (("prompt.json", False), ("prompt.nomap.json", True)):
        pr = capture_prompt(d, meta["goal"], meta["start"], nomap=nm)
        (d / fn).write_text(json.dumps(pr))
        print(f"{name} {fn}: {sum(len(m['content']) for m in pr['messages'])} chars")


def _env(nomap):
    env = dict(os.environ)
    if nomap:
        env["RED_PRINTED_MAP"] = "bag"
    else:
        env.pop("RED_PRINTED_MAP", None)
    return env


def capture_prompt(d, goal, start, nomap=False):
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
    r = subprocess.run([sys.executable, "-c", code], cwd=d, capture_output=True, text=True,
                       timeout=600, env=_env(nomap))
    cap = d / "prompt.captured.json"
    if not cap.exists():
        sys.exit("the author sent no model call; its output:\n" + (r.stdout + r.stderr)[-2000:])
    prompt = json.loads(cap.read_text())
    cap.unlink()
    return prompt


# ------- run

def score(d, reply, nomap=False):
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
                       text=True, timeout=300, env=_env(nomap))
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
    if {"map", "nomap"} & set(arms) and not (d / "prompt.nomap.json").exists():
        sys.exit(f"{name} has no prompt.nomap.json; run: author_ab.py prompts {name}")
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
            nomap = arm == "nomap"
            msgs = (json.loads((d / "prompt.nomap.json").read_text()) if nomap else prompt)["messages"]
            t = time.time()
            try:
                reply = B.chat(msgs, MODEL, think=think, temp=temp)
                err = None
            except Exception as e:
                reply, err = "", f"{type(e).__name__}: {e}"
            wall = time.time() - t
            last = dict(B.LAST or {})
            s = score(d, reply, nomap) if not err else {"parsed": False, "problems": [err], "route": [], "steps": 0}
            rec = {"t": t, "arm": arm, "i": i, "wall": round(wall, 1), "gtok": last.get("gtok"),
                   "ptok": last.get("ptok"), "think_chars": last.get("think_chars"),
                   "valid": s["parsed"] and not s["problems"], **s, "reply": reply,
                   "thinking": last.get("thinking", "")}
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{name} {arm:5s} #{i + 1}: {'VALID' if rec['valid'] else 'invalid'} "
                  f"{wall:6.1f}s {rec['gtok']} tok  route: {' > '.join(s['route'])[:90]}"
                  + ("" if rec["valid"] else f"  | {(s['problems'] or ['?'])[0][:110]}"), flush=True)


# ------- report

# ------- run --full: the whole authoring pass, as campaign.sh runs it

FULL_CODE = r"""
import json, sys, time
sys.path.insert(0, "planner")
import brock_probe
_chat = brock_probe.chat
stats = {"calls": 0, "think_calls": 0, "model_s": 0.0, "gtok": 0}
def counted(msgs, model, retries=2, think=False, temp=None):
    t = time.time()
    try:
        return _chat(msgs, model, retries=retries, think=think, temp=temp)
    finally:
        stats["calls"] += 1
        stats["think_calls"] += bool(think)
        stats["model_s"] += time.time() - t
        stats["gtok"] += (brock_probe.LAST or {}).get("gtok") or 0
brock_probe.chat = counted
import author
sys.argv = json.loads(sys.stdin.read())
try:
    author.main()
except SystemExit:
    pass
print("@@STATS " + json.dumps(stats))
"""


def fresh_work(d, tag):
    """A throwaway copy of the frozen case: the author keeps its drafts under
    plans/drafts and shows earlier ones to its review, so runs sharing one
    world would feed each other (and favour whichever arm went second)."""
    w = d / ("work_" + tag)
    if w.exists():
        shutil.rmtree(w)
    w.mkdir()
    shutil.copytree(d / "run", w / "run")
    shutil.copytree(d / "plans", w / "plans", symlinks=True)
    for entry in d.iterdir():
        if entry.is_symlink():
            (w / entry.name).symlink_to(os.readlink(entry))
    return w


def run_full(name, n, arms, force=False):
    """The WHOLE authoring pass per sample, exactly as campaign.sh runs it:
    author.py main() with its drafts, picker, review and the retry rounds that
    feed the validator's problems back. Arm on/off adds or drops --think; arm
    map/nomap sets the same environment as the single-reply arms. Scored on the
    plan it finally writes."""
    d = case_dir(name)
    meta = json.loads((d / "case.json").read_text())
    out = d / "results_full.jsonl"
    for i in range(n):
        for arm in arms:                              # interleaved, so drift hits both arms alike
            if chain_up() and not force:
                print("the chain came up; stopping here so it has the GPU", flush=True)
                return
            nomap = arm == "nomap"
            w = fresh_work(d, "%s_%d" % (arm, i))
            argv = ["author.py", "--goal", meta["goal"], "--start", meta["start"], "--out", "plan_out.json",
                    "--model", MODEL, "--observed", "run/explored.json", "--journal", "run/executor_log.jsonl"]
            if arm == "on":
                argv.append("--think")
            env = dict(_env(nomap), RED_RUN_DIR=str(w / "run"))
            t = time.time()
            r = subprocess.run([sys.executable, "-c", FULL_CODE], cwd=w, input=json.dumps(argv),
                               capture_output=True, text=True, timeout=3 * 3600, env=env)
            wall = time.time() - t
            stats = {}
            for line in r.stdout.splitlines():
                if line.startswith("@@STATS "):
                    stats = json.loads(line[8:])
            plan_txt = (w / "plan_out.json").read_text() if (w / "plan_out.json").exists() else ""
            s = score(d, plan_txt, nomap) if plan_txt else {"parsed": False, "problems": ["no plan written"],
                                                            "route": [], "steps": 0}
            log = [l for l in r.stdout.splitlines()
                   if l.startswith(("[author]", "[draws]", "[review]", "[think]", "wrote"))]
            rec = {"t": t, "arm": arm, "i": i, "mode": "full", "wall": round(wall, 1), **stats,
                   "valid": bool(plan_txt) and s["parsed"] and not s["problems"], **s,
                   "plan": plan_txt, "log": log[-40:], "stderr_tail": r.stderr[-1500:]}
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            shutil.rmtree(w, ignore_errors=True)
            print(f"{name} full {arm:5s} #{i + 1}: "
                  f"{'VALID' if rec['valid'] else 'no plan' if not plan_txt else 'invalid'} "
                  f"{wall:6.0f}s  calls {stats.get('calls')} (think {stats.get('think_calls')})  "
                  f"route: {' > '.join(s['route'])[:90]}", flush=True)


# ------- draws: do the drafts differ? three ways of asking for them

EXCLUDE_NOTE = ("\n\nYOU HAVE ALREADY DRAFTED THESE PLANS FOR THIS GOAL (the maps each one goes "
                "through):\n{routes}\nWrite a plan whose route is DIFFERENT from every one of "
                "them: a different first place to go, or a different way through. Everything "
                "else in the rules above still holds.")
IDEAS_NOTE = ("\n\nBEFORE YOU PLAN: name three DIFFERENT ideas for how this goal could be "
              "reached, each one sentence saying where you would go first and why. The ideas "
              "must not be rewordings of each other. Reply with JSON only: "
              "{{\"ideas\": [\"...\", \"...\", \"...\"]}}")
IDEA_NOTE = "\n\nPLAN THIS IDEA, and only this one: {idea}"


def target(name, maps):
    """The case's right answer for draws: a draft 'hits' when its route goes
    through any of these maps (set by hand from what finally worked)."""
    d = case_dir(name)
    meta = json.loads((d / "case.json").read_text())
    meta["hit_any"] = maps
    (d / "case.json").write_text(json.dumps(meta, indent=1))
    print(f"{name}: a draft hits when its route goes through any of {maps}")


def draws(name, n, methods, k=3, force=False):
    """N authoring passes per method, each of k drafts from the case's exact
    prompt at the draft temperature, interleaved by method:
      sample   k independent drafts, as author.py draws them today
      exclude  each draft is shown the routes already drafted and asked to differ
      hypo     one call for k different ideas, then one draft per idea
    The harness never says WHAT to do differently: every idea is the model's.
    Each draft is scored by the author's own checks, its route, and whether it
    goes through the case's hit_any maps (author_ab.py target)."""
    if chain_up() and not force:
        sys.exit("the chain is running; this needs the GPU to itself (--force to override)")
    d = case_dir(name)
    meta = json.loads((d / "case.json").read_text())
    hit_any = set(meta.get("hit_any") or [])
    prompt = json.loads((d / "prompt.json").read_text())
    sys.path.insert(0, str(REPO / "planner"))
    os.environ["RED_RUN_DIR"] = str(d / "run")
    import brock_probe as B
    temp = prompt.get("temp")
    sys_msg, user = prompt["messages"][0], prompt["messages"][-1]["content"]
    out = d / "results_draws.jsonl"

    def ask(text):
        t = time.time()
        reply = B.chat([sys_msg, {"role": "user", "content": text}], MODEL, temp=temp)
        return reply, time.time() - t
    for i in range(n):
        for method in methods:
            if chain_up() and not force:
                print("the chain came up; stopping here so it has the GPU", flush=True)
                return
            drafts, ideas, calls, wall = [], None, 0, 0.0
            try:
                if method == "hypo":
                    reply, w = ask(user + IDEAS_NOTE)
                    calls, wall = calls + 1, wall + w
                    m = re.search(r"\{.*\}", reply, re.S)
                    try:
                        ideas = [str(x) for x in json.loads(m.group(0)).get("ideas", [])][:k] if m else []
                    except ValueError:
                        ideas = []
                for j in range(k):
                    if method == "sample":
                        text = user
                    elif method == "exclude":
                        routes = "\n".join(f"{n_ + 1}. {' > '.join(x['route']) or '(no maps named)'}"
                                            for n_, x in enumerate(drafts))
                        text = user + (EXCLUDE_NOTE.format(routes=routes) if drafts else "")
                    else:
                        text = user + (IDEA_NOTE.format(idea=ideas[j]) if ideas and j < len(ideas) else "")
                    reply, w = ask(text)
                    calls, wall = calls + 1, wall + w
                    sc = score(d, reply)
                    drafts.append({"route": sc["route"], "valid": sc["parsed"] and not sc["problems"],
                                   "problem": (sc["problems"] or [""])[0][:200],
                                   "hit": bool(hit_any & set(sc["route"]))})
            except Exception as e:
                print(f"{name} {method} #{i + 1}: {type(e).__name__}: {e}", flush=True)
                continue
            routes = {tuple(x["route"]) for x in drafts}
            firsts = {x["route"][0] if x["route"] else None for x in drafts}
            rec = {"t": time.time(), "method": method, "i": i, "k": k, "calls": calls, "wall": round(wall, 1),
                   "ideas": ideas, "drafts": drafts, "distinct_routes": len(routes),
                   "distinct_first": len(firsts), "any_hit": any(x["hit"] for x in drafts),
                   "valid": sum(x["valid"] for x in drafts)}
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{name} {method:7s} #{i + 1}: {len(routes)} distinct routes, {len(firsts)} first maps, "
                  f"hit {'YES' if rec['any_hit'] else 'no '}, valid {rec['valid']}/{k}, {wall:5.0f}s", flush=True)
            for x in drafts:
                print(f"     {'*' if x['hit'] else ' '}{'ok ' if x['valid'] else 'BAD'} {' > '.join(x['route'])[:110]}")


def report_draws(names):
    names = names or sorted(p.name for p in ROOT.iterdir() if (p / "results_draws.jsonl").exists())
    for name in names:
        d = case_dir(name)
        if not (d / "results_draws.jsonl").exists():
            continue
        meta = json.loads((d / "case.json").read_text())
        rows = [json.loads(l) for l in open(d / "results_draws.jsonl")]
        print(f"\n== {name}: {meta['goal']}   (hit = through any of {meta.get('hit_any')})")
        for method in ("sample", "exclude", "hypo"):
            r = [x for x in rows if x["method"] == method]
            if not r:
                continue
            same = sum(1 for x in r if x["distinct_routes"] == 1)
            print(f"  {method:7s} passes={len(r)}  distinct routes/pass {statistics.mean(x['distinct_routes'] for x in r):.2f}"
                  f"  all-identical {same}/{len(r)}  any draft hits {sum(x['any_hit'] for x in r)}/{len(r)}"
                  f"  valid drafts {sum(x['valid'] for x in r)}/{sum(x['k'] for x in r)}"
                  f"  {statistics.median(x['wall'] for x in r):.0f}s/pass")


def report(names):
    names = names or sorted(p.name for p in ROOT.iterdir()
                            if (p / "results.jsonl").exists() or (p / "results_full.jsonl").exists())
    for name in names:
        d = case_dir(name)
        meta = json.loads((d / "case.json").read_text())
        print(f"\n== {name}: {meta['goal']}")
        for fname, kind in (("results.jsonl", "first reply"), ("results_full.jsonl", "full pass")):
            rows = [json.loads(l) for l in open(d / fname)] if (d / fname).exists() else []
            for arm in ("off", "on", "nomap", "map"):
                r = [x for x in rows if x["arm"] == arm]
                if not r:
                    continue
                v = sum(x["valid"] for x in r)
                label = f"think {arm:3s}" if arm in ("off", "on") else f"{arm:9s}"
                calls = ("  %.0f calls" % statistics.median(x.get("calls") or 0 for x in r)
                         if kind == "full pass" else "")
                print(f"  {kind:11s} {label}  n={len(r)}  valid {v}/{len(r)}  "
                      f"median {statistics.median(x['wall'] for x in r):.0f}s  "
                      f"{statistics.median(x['gtok'] or 0 for x in r):.0f} tok{calls}")
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
    s.add_argument("--from", dest="from_case")
    q = sub.add_parser("prompts")
    q.add_argument("case")
    r = sub.add_parser("run")
    r.add_argument("case")
    r.add_argument("--n", type=int, default=3)
    r.add_argument("--arms", default="off,on")
    r.add_argument("--force", action="store_true")
    r.add_argument("--full", action="store_true",
                   help="the whole authoring pass per sample (drafts, picker, review, retries)")
    dr = sub.add_parser("draws", help="do the drafts differ? sample / exclude / hypo")
    dr.add_argument("case")
    dr.add_argument("--n", type=int, default=3, help="authoring passes per method")
    dr.add_argument("--k", type=int, default=3, help="drafts per pass")
    dr.add_argument("--methods", default="sample,exclude,hypo")
    dr.add_argument("--force", action="store_true")
    tg = sub.add_parser("target", help="the case's right answer: maps a hitting draft goes through")
    tg.add_argument("case")
    tg.add_argument("maps", nargs="+")
    rd = sub.add_parser("report-draws")
    rd.add_argument("cases", nargs="*")
    p = sub.add_parser("report")
    p.add_argument("cases", nargs="*")
    a = ap.parse_args()
    if a.cmd == "snapshot":
        snapshot(a.case, a.goal, a.start, a.force, a.from_case)
    elif a.cmd == "prompts":
        prompts(a.case)
    elif a.cmd == "draws":
        draws(a.case, a.n, a.methods.split(","), a.k, a.force)
    elif a.cmd == "target":
        target(a.case, a.maps)
    elif a.cmd == "report-draws":
        report_draws(a.cases)
    elif a.cmd == "run" and a.full:
        run_full(a.case, a.n, a.arms.split(","), a.force)
    elif a.cmd == "run":
        run(a.case, a.n, a.arms.split(","), a.force)
    else:
        report(a.cases)


if __name__ == "__main__":
    main()

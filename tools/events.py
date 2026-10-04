#!/usr/bin/env python3
"""Run events: one short line per thing worth telling a viewer, derived from
the executor journal (run/executor_log.jsonl), the chain log (run/chain.log:
the plan authoring between attempts, when the game is closed) and the party
in run/obs.json,
appended to a feed that anything can follow: the HUD's EVENTS strip now, a
stream chat or the casters later.

  tools/events.py --follow     # run beside the chain; writes the feed
  tools/events.py --tail       # print the feed as it grows (a chat stand-in)
  tools/events.py --last 20    # the last 20 events

It only READS the run. The feed lives OUTSIDE it, at
~/.local/state/red-recomp/events.jsonl (RED_EVENTS overrides), so nothing here
can touch what the chain reads. Each record is
  {"t": ..., "kind": ..., "tone": "good|bad|info|think|round", "level": 1|2, "text": ...}
level 2 is worth showing anyone; level 1 is every round, for the casters.
and the text is plain ASCII-ish words, so any sink can add its own symbols.

Starting it does not replay history: it begins at the logs' current ends
and takes the party as it stands as the baseline. It also keeps
~/.local/state/red-recomp/phase.json (playing / authoring, with the goal, the
drafts and the pick) for the HUD.
"""
import argparse
import json
import subprocess
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(HERE, "..", "run")
JOURNAL = os.path.join(RUN, "executor_log.jsonl")
OBS = os.path.join(RUN, "obs.json")
STATUS = os.path.join(RUN, "status.txt")
FEED = os.environ.get("RED_EVENTS") or os.path.expanduser(
    "~/.local/state/red-recomp/events.jsonl")


def words(ident):
    """travel_to_vermilion -> travel to vermilion"""
    return str(ident or "").replace("_", " ").strip()


# a full stop inside these is not the end of a sentence (Mt. Moon, S.S. Anne)
ABBREV = re.compile(r"\b(Mt|St|Mr|Mrs|Dr|Prof|S\.S|vs|No)\.", re.I)


def first_sentence(text, limit=140):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    guarded = ABBREV.sub(lambda m: m.group(0).replace(".", "\x00"), text)
    m = re.match(r"(.+?[.!?])(\s|$)", guarded)
    s = (m.group(1) if m else guarded).replace("\x00", ".")
    if not m and s and s[-1].isalnum():
        s += "..."                   # the log itself cut the line mid-word
    return s if len(s) <= limit else s[:limit - 3].rstrip() + "..."


def ops_text(macro):
    """The first op of a proposed macro, read out: go to MT_MOON_B2F|27,5."""
    try:
        ops = json.loads(macro.replace("'", '"')) if isinstance(macro, str) else macro
    except ValueError:
        return ""
    if not ops:
        return ""
    op = ops[0]
    name = op.get("op", "?")
    args = " ".join(str(v) for k, v in op.items() if k != "op")
    more = " (+%d more)" % (len(ops) - 1) if len(ops) > 1 else ""
    return (words(name) + (" " + args if args else "") + more).strip()


def flag_text(flag):
    """EVENT_GOT_SS_TICKET -> got ss ticket; trainer flags are None (noise)."""
    if "TRAINER" in flag:
        return None
    return words(re.sub(r"^EVENT_", "", flag)).lower()


# ------- journal records -> events

def from_record(d, state):
    k = d.get("kind")
    if k == "plan_start":
        return "info", "new leg: %s" % d.get("goal", "?")
    if k == "plan_complete":
        n = d.get("escalations")
        return "good", "leg done: %s%s" % (d.get("goal", "?"),
                                           " (%s escalations)" % n if n else "")
    if k == "escalate_end" and str(d.get("success")) == "False":
        return "bad", "step failed: %s" % words(d.get("subgoal"))
    if k == "think_on":
        state["think_on"] = d.get("t")
        return "think", "stuck %s rounds on %s, thinking it over" % (
            d.get("stale", "?"), words(d.get("subgoal")))
    if k == "escalate_proposal" and str(d.get("think")) == "True":
        secs = d.get("tot_s")
        took = "%dm%02ds" % divmod(int(float(secs)), 60) if secs else "?"
        what = ops_text(d.get("macro"))
        why = first_sentence(d.get("plan"))
        return "think", "thought %s (%s tokens) -> %s%s" % (
            took, d.get("gtok", "?"), what or "a new plan", ": " + why if why else "")
    if k == "escalate_proposal":
        # an ordinary round: what it chose and why, in its own first sentence.
        # Level 1 = caster fodder, too frequent for chat or the HUD strip.
        what = ops_text(d.get("macro"))
        why = first_sentence(d.get("plan"))
        return "round", "r%s %s: %s%s" % (d.get("round", "?"), words(d.get("subgoal")),
                                           what or "a plan", " - " + why if why else "")
    if k == "fight_recap":
        who = words(d.get("who"))
        lost = str(d.get("lost")) == "True"
        return ("bad" if lost else "good",
                "%s %s at %s" % ("lost to" if lost else "beat", who, words(d.get("where"))))
    if k == "flag_fired":
        t = flag_text(d.get("flag", ""))
        if t and not t.startswith("beat "):         # fights come from fight_recap
            return "info", t
        return None
    if k == "named":
        # the "joined the team" line carries the name (see from_party)
        return None
    if k == "new_species_asked" and str(d.get("catch")) == "True":
        return "info", "going for a catch: %s" % d.get("foe", "?")
    if k == "buy_done" and str(d.get("ok")) == "True":
        return "info", "bought %s x%s" % (words(d.get("item")), d.get("count", "?"))
    if k == "backtrack" and d.get("redoing"):
        return "bad", "backtracking to redo %s" % words(d.get("redoing"))
    return None


# ------- party diffs -> events

def party_of(obs):
    out = []
    for p in (obs or {}).get("party") or []:
        out.append({"key": (p.get("otId"), p.get("nickname")), "nick": p.get("nickname"),
                    "species": p.get("species"), "level": p.get("level"), "hp": p.get("hp")})
    return out


# A NEW MEMBER IS SAID ONCE, BY THE NAME IT ENDS UP WITH. It arrives under
# its species name, is renamed a moment later, and the feed said "PIDGEY the
# PIDGEY joined", "named it X" and "X the PIDGEY joined" (user, 2026-10-03:
# "only the last one is a necessary line"). One still wearing its species
# name waits here until it is renamed, or until NAME_WAIT seconds say the
# name was declined.
PENDING = {}          # (otId, species) -> {"t": first seen, "m": member}
NAME_WAIT = 90


def _default_name(m):
    norm = lambda x: re.sub(r"[^A-Z0-9]", "", str(x or "").upper())
    return not m["nick"] or norm(m["nick"]) == norm(m["species"])


def _joined(m):
    return ("good", "%s the %s joined the team"
            % (m["nick"] or m["species"], m["species"]))


def flush_pending(now=None):
    """Members whose naming window has passed, said under the name they kept."""
    now = now or time.time()
    out = []
    for k, p in list(PENDING.items()):
        if now - p["t"] >= NAME_WAIT:
            out.append(_joined(p["m"]))
            del PENDING[k]
    return out


def from_party(before, after, badges_before, badges_after):
    evs = []
    old = {m["key"]: m for m in before}
    keys_after = {m["key"] for m in after}
    gone = [o for o in before if o["key"] not in keys_after]
    for m in after:
        o = old.get(m["key"])
        name = m["nick"] or m["species"]
        if o is None:
            sk = (m["key"][0], m["species"])
            renamed = next((g for g in gone if (g["key"][0], g["species"]) == sk), None)
            if renamed is not None:
                gone.remove(renamed)
                if sk in PENDING:        # renamed in its naming window: say it now
                    del PENDING[sk]
                    evs.append(_joined(m))
                continue                 # a rename of someone already said
            if not before:               # the first read is the baseline, not news
                continue
            if _default_name(m):
                PENDING[sk] = {"t": time.time(), "m": m}
            else:
                evs.append(_joined(m))
            continue
        if m["species"] != o["species"]:
            evs.append(("good", "%s evolved into %s" % (name, m["species"])))
        if (m["level"] or 0) > (o["level"] or 0):
            evs.append(("good", "%s grew to L%s" % (name, m["level"])))
        if (o["hp"] or 0) > 0 and m["hp"] == 0:
            evs.append(("bad", "%s fainted" % name))
    for b in badges_after:
        if b not in badges_before:
            evs.append(("good", "earned the %s" % words(b).upper()))
    return evs


# ------- chain.log (the authoring between attempts) -> events + phase

CHAIN = os.path.join(RUN, "chain.log")
LIVE = os.path.join(RUN, "thinking_live.txt")     # brock_probe writes it while a call thinks
MODEL_LIVE = os.path.join(RUN, "model_live.txt")  # ...and this for EVERY call (stream-all patch)
PHASE = os.path.join(os.path.dirname(FEED), "phase.json")
TRAIL = os.path.join(os.path.dirname(FEED), "trail.jsonl")   # breadcrumbs: the player's cell as it changes

LEG_AUTHOR = re.compile(r"^=== leg (\d+)/(\d+): authoring \S+ (.+)$")
REWRITE = re.compile(r"^--- rewriting (\S+) from evidence ---")
GOAL = re.compile(r"^\s+goal:\s+(.+)$")
START = re.compile(r"^\s+start:\s+(.+)$")
AUTHOR_THINKS = re.compile(r"^--- plan (\d+) for this leg: the author thinks ---")
AB_CAPTURE = os.environ.get("RED_AB_CAPTURE", "1") != "0"
DRAFT = re.compile(r"^\[draws\] draft (\d+): (\d+) subgoals: (.+)$")
PICKED = re.compile(r"^\[draws\] picked draft (\d+) of (\d+): (.+)$")
ATTEMPT = re.compile(r"^=== attempt (\d+)/(\d+): (\S+) ===")
PULLED = re.compile(r"^=== leg (\d+) stuck behind leg (\d+): pulling it forward ===")
WORDING = re.compile(r"^\[wording\] (VOID, by the model's own account|the wording stands)(.*)$")


def route(chain):
    """'? -> ROUTE_24 -> CERULEAN_CITY' -> 'route 24 -> cerulean city'"""
    stops = [words(x).lower() for x in chain.split(" -> ") if x.strip() not in ("?", "")]
    return " -> ".join(stops)


def write_phase(phase):
    os.makedirs(os.path.dirname(PHASE), exist_ok=True)
    tmp = PHASE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(phase, f)
    os.replace(tmp, PHASE)
    hist_append("phase", {"phase": phase})


# WHAT THE HUD SHOWED AT A GIVEN TIME. On stream the game on screen is the 1x
# copy, minutes behind the run; the status and the authoring phase the HUD
# prints must be the ones from the moment the copy is showing, or it reads
# out what is about to happen. Every change to either is kept here with its
# time; status_at / phase_at read the latest one at or before a moment.
HISTORY = os.path.join(os.path.dirname(FEED), "history.jsonl")
HISTORY_MAX = 30_000_000


def hist_append(kind, rec, t=None):
    try:
        os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
        with open(HISTORY, "a") as f:
            f.write(json.dumps(dict(rec, kind=kind, t=t or time.time())) + "\n")
        if os.path.getsize(HISTORY) > HISTORY_MAX:          # keep the newest third
            with open(HISTORY, "rb") as f:
                f.seek(-HISTORY_MAX // 3, 2)
                tail = f.read().split(b"\n", 1)[-1]
            with open(HISTORY + ".tmp", "wb") as f:
                f.write(tail)
            os.replace(HISTORY + ".tmp", HISTORY)
    except OSError:
        pass


def _hist_at(kind, t, tail=6_000_000):
    best = None
    try:
        with open(HISTORY, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - tail))
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return None
    for line in lines:
        if f'"kind": "{kind}"' not in line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("t", 0) <= t:
            best = r
        else:
            break
    return best


def status_at(t):
    r = _hist_at("status", t)
    return r.get("text") if r else None


def phase_at(t):
    r = _hist_at("phase", t)
    return r.get("phase") if r else None


AUTHOR_LOG_MAX = 40


def author_log(line, phase):
    """The authoring's own narration in chain.log, kept as a rolling log on
    the phase for the HUD: what was rejected and why, what the review
    changed, what the picker was shown. Returns True when the line was one."""
    if phase.get("phase") != "authoring":
        return False
    text, tone = None, "info"
    if phase.pop("want_problem", False) and line.startswith("- "):
        text, tone = "  " + line[2:].strip(), "bad"
    elif re.match(r"^\[author\] round \d+ invalid", line):
        text, tone = line[9:].rstrip(":").strip() + ":", "bad"
        phase["want_problem"] = True
    elif line.startswith("[author] valid plan"):
        text, tone = line[9:].strip(), "good"
    elif line.startswith("[review]"):
        text = "review " + line[8:].strip()
        tone = "bad" if "invalid" in line else "info"
    elif line.startswith("[drafts]"):
        text = line[9:].strip()
    elif line.startswith("[check-done] refused"):
        text, tone = "check refused: " + line.split("refused:", 1)[1].strip(), "bad"
    elif line.startswith("[draws] one shape"):
        text = line[8:].strip()
    elif line.startswith("[wording]"):
        text = "wording: " + line[10:].strip()
    elif line.startswith("--- plan ") and "author thinks" in line:
        text, tone = line.strip("- ").strip(), "think"
    if text is None:
        return False
    log = phase.setdefault("log", [])
    log.append({"t": time.time(), "tone": tone, "text": text[:300]})
    del log[:-AUTHOR_LOG_MAX]
    return True


def from_chain_line(line, phase):
    """One chain.log line -> (tone, text) or None; updates `phase` in place
    (the HUD reads it to know the game is gone because the model is writing)."""
    m = LEG_AUTHOR.match(line)
    if m:
        phase.update(phase="authoring", since=time.time(), what="new leg",
                     leg="%s/%s" % (m.group(1), m.group(2)), goal=m.group(3).strip(),
                     drafts=[], picked=None, log=[])
        return "think", "writing a plan for leg %s: %s" % (m.group(1), m.group(3).strip())
    m = REWRITE.match(line)
    if m:
        phase.update(phase="authoring", since=time.time(), what="rewrite",
                     goal=None, drafts=[], picked=None, log=[])
        phase["want_goal"] = True
        return None                      # announced with the goal on the next line
    m = GOAL.match(line)
    if m and phase.pop("want_goal", False):
        phase["goal"] = m.group(1).strip()
        return "think", "rewriting the plan from what it walked: %s" % phase["goal"]
    m = START.match(line)
    if m and phase.get("what") == "rewrite":
        phase["start"] = m.group(1).strip()
        return None
    m = AUTHOR_THINKS.match(line)
    if m:
        # A THINKING AUTHOR PASS IS AN A/B CASE. Freeze this moment (what the
        # author is about to read, and the goal and start campaign.sh gave
        # it) so tools/author_ab.py can later replay it with thinking off and
        # on. Snapshot only: reading and copying, in the background, no GPU.
        goal, start = phase.get("goal"), phase.get("start")
        if AB_CAPTURE and goal and start and phase.get("live", True):
            slug = re.sub(r"[^a-z0-9]+", "_", goal.lower()).strip("_")[:40]
            case = "%s_%s_p%s" % (time.strftime("%m%d_%H%M"), slug, m.group(1))
            try:
                subprocess.Popen([sys.executable, os.path.join(HERE, "author_ab.py"), "snapshot", case,
                                  "--goal", goal, "--start", start],
                                 cwd=os.path.join(HERE, ".."), stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
            except OSError:
                pass
        return "think", "plan %s for this leg: the author will think it over" % m.group(1)
    m = DRAFT.match(line)
    if m:
        r = route(m.group(3))
        phase.setdefault("drafts", []).append(
            {"n": int(m.group(1)), "steps": int(m.group(2)), "route": r})
        phase["phase"] = "authoring"
        return "info", "draft %s (%s steps): %s" % (m.group(1), m.group(2), r)
    m = PICKED.match(line)
    if m:
        phase["picked"] = {"n": int(m.group(1)), "of": int(m.group(2)),
                           "why": first_sentence(m.group(3), 200)}
        return "think", "picked draft %s of %s: %s" % (
            m.group(1), m.group(2), first_sentence(m.group(3)))
    m = PULLED.match(line)
    if m:
        return "info", "leg %s is stuck behind leg %s, pulling that one forward" % (
            m.group(1), m.group(2))
    m = WORDING.match(line)
    if m:
        if m.group(1).startswith("VOID"):
            return "bad", "the model voided this leg"
        return None
    if "terminated by signal" in line or line.startswith("=== chain stopped"):
        was = phase.get("phase")
        phase.update(phase="stopped", since=time.time())
        return ("bad", "the chain stopped") if was != "stopped" else None
    if line.startswith("[chain] model="):
        phase.update(phase="playing", since=time.time())
        return "info", "the chain is starting up"
    m = ATTEMPT.match(line)
    if m:
        was = phase.get("phase")
        phase.update(phase="playing", since=time.time(), attempt="%s/%s" % (m.group(1), m.group(2)))
        return ("info", "back to playing (attempt %s of %s)" % (m.group(1), m.group(2))) \
            if was == "authoring" else None
    return None


# ------- the follower

def append(kind, tone, text):
    """level 2 = worth showing anyone (HUD strip, chat); level 1 = every round,
    for the casters, who need something to say between milestones."""
    os.makedirs(os.path.dirname(FEED), exist_ok=True)
    level = 1 if tone == "round" else 2
    rec = {"t": time.time(), "kind": kind, "tone": tone, "level": level, "text": text}
    with open(FEED, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(time.strftime("%H:%M:%S"), tone.ljust(5), text, flush=True)


def read_obs():
    try:
        with open(OBS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


class Tail:
    """New complete lines of a file that may be replaced (a restart archives
    the journal and starts a new one) or truncated. Starts at the END: a
    follower begins with what happens next, not with history."""

    def __init__(self, path):
        self.path, self.ino, self.pos, self.rest = path, None, None, b""

    def lines(self):
        try:
            st = os.stat(self.path)
        except OSError:
            return []
        if self.ino is None:                       # first sight: skip history
            self.ino, self.pos = st.st_ino, st.st_size
            return []
        if st.st_ino != self.ino or st.st_size < self.pos:
            self.ino, self.pos, self.rest = st.st_ino, 0, b""   # replaced: read it all
        if st.st_size == self.pos:
            return []
        with open(self.path, "rb") as f:
            f.seek(self.pos)
            data = f.read()
        self.pos += len(data)
        data = self.rest + data
        *done, self.rest = data.split(b"\n")
        return [l.decode("utf-8", "replace") for l in done]


def follow(poll=0.5):
    state, phase = {}, {"phase": "playing", "since": time.time()}
    # where the chain stands right now (mid-authoring or playing), read off the
    # log's recent tail WITHOUT posting any of it: history is not news
    try:
        with open(CHAIN, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            phase["live"] = False           # replaying history: no captures
            for line in f.read().decode("utf-8", "replace").splitlines()[1:]:
                author_log(line, phase)
                from_chain_line(line, phase)
            phase.pop("live", None)
    except OSError:
        pass
    journal, chain = Tail(JOURNAL), Tail(CHAIN)
    obs = read_obs()
    party, badges = party_of(obs), list((obs or {}).get("badges") or [])
    obs_stamp = None
    write_phase(phase)
    while True:
        for line in journal.lines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            ev = from_record(d, state)
            if ev:
                append(d.get("kind"), *ev)
        changed = False
        for line in chain.lines():
            before = json.dumps(phase, sort_keys=True)
            author_log(line, phase)
            ev = from_chain_line(line, phase)
            if ev:
                append("chain", *ev)
            changed |= json.dumps(phase, sort_keys=True) != before
        if changed:
            write_phase(phase)
        # a thinking call in flight: a line from it every ~30 s, for the casters
        lt = live_thought()
        if lt and not lt[2] and time.time() - state.get("live_at", 0) > 30:
            line = latest_line(lt[0])
            if line and line != state.get("live_last"):
                append("thinking", "round", "thinking (%ds in): %s" % (time.time() - lt[1], line))
                state["live_last"], state["live_at"] = line, time.time()
        # the status column, every change, for status_at
        try:
            st = os.stat(STATUS).st_mtime
        except OSError:
            st = None
        if st and st != state.get("status_t"):
            state["status_t"] = st
            try:
                with open(STATUS) as f:
                    hist_append("status", {"text": f.read()}, t=st)
            except OSError:
                pass
        # the party
        try:
            s = os.stat(OBS).st_mtime_ns
        except OSError:
            s = None
        if s and s != obs_stamp:
            obs_stamp = s
            fresh = read_obs()
            if fresh is not None:
                # a breadcrumb whenever the player's map or cell changes, for
                # the world map's trail of the actual path
                pl = fresh.get("player") or {}
                here = ((fresh.get("map") or {}).get("id"), pl.get("x"), pl.get("y"))
                if here[0] and isinstance(here[1], int) and isinstance(here[2], int) \
                        and here != state.get("crumb"):
                    state["crumb"] = here
                    try:
                        with open(TRAIL, "a") as f:
                            f.write(json.dumps({"t": time.time(), "map": here[0],
                                                "x": here[1], "y": here[2]}) + "\n")
                    except OSError:
                        pass
                new_party = party_of(fresh)
                new_badges = list(fresh.get("badges") or [])
                for tone, text in from_party(party, new_party, badges, new_badges):
                    append("party", tone, text)
                # keep a pending member's latest read, so a declined name is
                # said with what it is now
                for _m in new_party:
                    _pk = (_m["key"][0], _m["species"])
                    if _pk in PENDING:
                        PENDING[_pk]["m"] = _m
                if new_party:        # a blank read mid-write is not a lost team
                    party, badges = new_party, new_badges
        for tone, text in flush_pending():
            append("party", tone, text)
        time.sleep(poll)


def live_thought():
    """(text, started, done) of run/thinking_live.txt, or None when there is
    none. A file untouched for 20 s without its '# done' is a call that died."""
    try:
        st = os.stat(LIVE)
        with open(LIVE, errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    if not lines or not lines[0].startswith("# thinking since"):
        return None
    try:
        started = float(lines[0].split()[3])
    except (IndexError, ValueError):
        started = st.st_mtime
    done = bool(lines[-1].startswith("# ")) and len(lines) > 1
    stale = time.time() - st.st_mtime > 20
    body = "\n".join(l for l in lines[1:] if not l.startswith("# "))
    return body, started, done or stale


def live_call():
    """The model call in flight, from run/model_live.txt (every call, once the
    stream-all patch is in) or else run/thinking_live.txt (thinking calls):
    {text, started, done, think, who, answer} or None. `answer` is the reply
    part (after '# answer'), `text` everything."""
    try:
        st = os.stat(MODEL_LIVE)
        fresh = time.time() - st.st_mtime < 20
    except OSError:
        fresh = False
    if fresh:
        try:
            with open(MODEL_LIVE, errors="replace") as f:
                lines = f.read().splitlines()
        except OSError:
            lines = []
        if lines and lines[0].startswith("# call since"):
            head = lines[0]
            m = re.search(r"since ([\d.]+)", head)
            who = head.split(" who=", 1)[1] if " who=" in head else ""
            body, answer, seen_answer = [], [], False
            for l in lines[1:]:
                if l == "# answer":
                    seen_answer = True
                    continue
                if l.startswith("# done") or l.startswith("# broken off"):
                    continue
                (answer if seen_answer else body).append(l)
            think = " think=1" in head
            done = lines[-1].startswith(("# done", "# broken off"))
            text = "\n".join(body + answer)
            return {"text": text, "answer": "\n".join(answer if think else body),
                    "started": float(m.group(1)) if m else st.st_mtime,
                    "done": done, "think": think, "who": who}
    lt = live_thought()
    if lt:
        return {"text": lt[0], "answer": "", "started": lt[1], "done": lt[2], "think": True, "who": ""}
    return None


def latest_line(text):
    """The last finished line of a trace worth quoting (bullets and markup off)."""
    for line in reversed(text.splitlines()[:-1] or text.splitlines()):
        line = re.sub(r"^[\s*\-0-9.)]+", "", line).replace("**", "").strip()
        if len(line) > 12:
            return line if len(line) <= 160 else line[:157] + "..."
    return None


def read_phase():
    try:
        with open(PHASE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_feed():
    try:
        with open(FEED) as f:
            return [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        return []


def last_events(n, min_level=1, until=None):
    """The last n events at or above min_level, newest last (the HUD asks for
    level 2; a record from before levels existed counts as 2)."""
    # the last 40 KB, and further back while the moment asked for is older
    # than all of it (the copy behind the run: an empty strip otherwise)
    out = []
    span = 40000
    while True:
        try:
            with open(FEED, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - span))
                lines = f.read().decode("utf-8", "replace").splitlines()
        except OSError:
            return []
        if until is None or span >= size or span >= 64_000_000:
            break
        try:
            first = json.loads(lines[1] if len(lines) > 1 else lines[0])
        except (ValueError, IndexError):
            break
        if (first.get("t") or 0) <= until:
            break
        span *= 8
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("level", 2) >= min_level and (until is None or (e.get("t") or 0) <= until):
            out.append(e)
    return out[-n:]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--follow", action="store_true", help="derive events and append to the feed")
    ap.add_argument("--tail", action="store_true", help="print the feed as it grows")
    ap.add_argument("--last", type=int, help="print the last N events and exit")
    args = ap.parse_args()
    if args.follow:
        print("feed:", FEED, flush=True)
        try:
            follow()
        except KeyboardInterrupt:
            pass
    elif args.tail or args.last:
        for e in last_events(args.last or 10):
            print(time.strftime("%H:%M:%S", time.localtime(e["t"])), e["tone"].ljust(5), e["text"])
        if args.tail:
            try:
                with open(FEED) as f:
                    f.seek(0, 2)
                    while True:
                        line = f.readline()
                        if not line:
                            time.sleep(0.5)
                            continue
                        e = json.loads(line)
                        print(time.strftime("%H:%M:%S", time.localtime(e["t"])),
                              e["tone"].ljust(5), e["text"], flush=True)
            except (KeyboardInterrupt, OSError):
                pass
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

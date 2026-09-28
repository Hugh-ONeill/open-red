#!/usr/bin/env python3
"""Run events: one short line per thing worth telling a viewer, derived from
the executor journal (run/executor_log.jsonl) and the party in run/obs.json,
appended to a feed that anything can follow: the HUD's EVENTS strip now, a
stream chat or the casters later.

  tools/events.py --follow     # run beside the chain; writes the feed
  tools/events.py --tail       # print the feed as it grows (a chat stand-in)
  tools/events.py --last 20    # the last 20 events

It only READS the run. The feed lives OUTSIDE it, at
~/.local/state/red-recomp/events.jsonl (RED_EVENTS overrides), so nothing here
can touch what the chain reads. Each record is
  {"t": ..., "kind": ..., "tone": "good|bad|info|think", "text": ...}
and the text is plain ASCII-ish words, so any sink can add its own symbols.

Starting it does not replay history: it begins at the journal's current end
and takes the party as it stands as the baseline.
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(HERE, "..", "run")
JOURNAL = os.path.join(RUN, "executor_log.jsonl")
OBS = os.path.join(RUN, "obs.json")
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
        if str(d.get("ok")) == "True":
            return "info", "named it %s" % d.get("name", "?")
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


def from_party(before, after, badges_before, badges_after):
    evs = []
    old = {m["key"]: m for m in before}
    for m in after:
        o = old.get(m["key"])
        name = m["nick"] or m["species"]
        if o is None:
            if before:               # the first read is the baseline, not news
                evs.append(("good", "%s the %s joined the team" % (name, m["species"])))
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


# ------- the follower

def append(kind, tone, text):
    os.makedirs(os.path.dirname(FEED), exist_ok=True)
    rec = {"t": time.time(), "kind": kind, "tone": tone, "text": text}
    with open(FEED, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(time.strftime("%H:%M:%S"), tone.ljust(5), text, flush=True)


def read_obs():
    try:
        with open(OBS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def follow(poll=0.5):
    state = {}
    fh, ino = None, None
    obs = read_obs()
    party, badges = party_of(obs), list((obs or {}).get("badges") or [])
    obs_stamp = None
    while True:
        # the journal: reopen when it is replaced (a restart archives it and
        # starts a new one); a fresh open of the SAME file seeks to its end
        try:
            st = os.stat(JOURNAL)
            if fh is None or st.st_ino != ino or st.st_size < fh.tell():
                if fh:
                    fh.close()
                replaced = fh is not None
                fh, ino = open(JOURNAL), st.st_ino
                if not replaced:
                    fh.seek(0, 2)
            buf = fh.read()
            if buf:
                done, _, rest = buf.rpartition("\n")
                fh.seek(fh.tell() - len(rest.encode()))    # keep a half line for later
                for line in done.splitlines():
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    ev = from_record(d, state)
                    if ev:
                        append(d.get("kind"), *ev)
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
                new_party = party_of(fresh)
                new_badges = list(fresh.get("badges") or [])
                for tone, text in from_party(party, new_party, badges, new_badges):
                    append("party", tone, text)
                if new_party:        # a blank read mid-write is not a lost team
                    party, badges = new_party, new_badges
        time.sleep(poll)


def load_feed():
    try:
        with open(FEED) as f:
            return [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        return []


def last_events(n):
    """The last n events, newest last (used by the HUD)."""
    out = []
    try:
        with open(FEED, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 40000))
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


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

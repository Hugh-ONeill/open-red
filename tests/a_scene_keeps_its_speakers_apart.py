#!/usr/bin/env python3
"""A scene with more than one speaker reaches the page box by box, and a
crossing that rides a cutscene says what the scene said.

Two faults, one scene (user, 2026-09-16: "when theres scripted events where
more than one character is talking, typically just oak and the rival, are
we seperating the dialog properly?"; then "build both, it happens later
when getting the dex too"):

  * Run 21's page read "OAK: It's unsafe! Wild POKéMON live in tall grass!
    You need ... have one! Choose! JERK: Hey! Gramps! What about me? OAK: Be
    patient!" — every box run into one sentence, and the trace's length cap
    cut through the middle. A box the game prints with no name on it
    ("WHAT? Unbelievable! I picked the wrong POKéMON!") reads as the end of
    whoever spoke last.
  * Run 22 got none of it: the escort fired inside cross(dir=north), whose
    cutscene rider pressed A through every page and returned "crossed
    (cutscene)", and the next plan began "Professor Oak has finally
    arrived", inferred from the room.

Pinned: the shim joins pages of one box with a space and boxes with " / ";
a line ending in a hyphen runs on; the cutscene rider records each page
before pressing past it and every cutscene return of cross quotes the
scene; the executor's excerpt keeps whole boxes, keeps a cut box's printed
speaker, and does not quote a crossing twice.

Synthetic (source anchors for the shim; the excerpt is run directly).
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E           # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


shim = (ROOT / "harness/shim.lua").read_text()

# ---- the shim's joins, run in Lua ------------------------------------------
# page_words and note_text are pure; lift them out and run them against the
# escort as the dialog trace recorded it (box table, page) in order.
def lua_block(src: str, start: str) -> str:
    i = src.index(start)
    depth, j = 0, i
    for m in re.finditer(r"\b(function|if|for|while|do|end)\b", src[i:]):
        w = m.group(1)
        if w in ("function", "if", "for", "while"):
            depth += 1
        elif w == "do":
            # `for ... do` and `while ... do` already counted
            pre = src[i:i + m.start()].rsplit("\n", 1)[-1]
            if not re.search(r"\b(for|while)\b", pre):
                depth += 1
        else:
            depth -= 1
            if depth == 0:
                j = i + m.end()
                break
    return src[i:j]


pw = lua_block(shim, "local function page_words(pg)")
nt = lua_block(shim, "function note_text(txt, box)")
prog = f"""
local recent_text, last_text, text_run, text_seq, text_box = nil, nil, nil, 0, nil
{pw}
local note_text
{nt.replace("function note_text(txt, box)", "note_text = function(txt, box)", 1)}
local A, B, C, D = {{}}, {{}}, {{}}, {{}}
note_text(page_words({{"OAK: Hey! Wait!", "Don't go out!"}}), A)
note_text(page_words({{"OAK: It's unsafe!", "Wild POKéMON live"}}), B)
note_text(page_words({{"You need your own", "POKéMON!"}}), B)
note_text(page_words({{"JERK: Gramps!", "I'm fed up"}}), C)
note_text(page_words({{"WHAT?", "Unbelievable!"}}), D)
print(last_text)
print(page_words({{"It's encyclopedia-", "like, but the"}}))
text_run, last_text, text_box = nil, nil, nil
local G1, G2 = {{}}, {{}}
note_text("I'm on guard duty.", G1)
note_text("I'm on guard duty.", G2)
print(last_text)
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
out = subprocess.run(["lua", f.name], capture_output=True, text=True,
                     timeout=20)
lines = out.stdout.splitlines()
ck("the shim's joins run", out.returncode == 0 and len(lines) == 3)
if len(lines) == 3:
    ck("pages of one box join with a space, boxes with ' / '",
       lines[0] == "OAK: Hey! Wait! Don't go out! / OAK: It's unsafe! Wild "
                   "POKéMON live You need your own POKéMON! / JERK: Gramps! "
                   "I'm fed up / WHAT? Unbelievable!")
    ck("an unnamed box is its own line, not the end of the last speaker's",
       lines[0].endswith(" / WHAT? Unbelievable!"))
    ck("a hyphen at a line break runs on",
       lines[1] == "It's encyclopedia-like, but the")
    ck("the same line said again in a new box starts over, it does not stack",
       lines[2] == "I'm on guard duty.")
else:
    print(out.stdout, out.stderr)

# ---- the cutscene rider and cross ------------------------------------------
cross = shim[shim.index("function OPS.cross(G, c)"):]
cross = cross[:cross.index("\nfunction OPS.", 10)]
ride = cross[cross.index("local function ride_cutscene()"):]
ride = ride[:ride.index("\n  end\n")]
ck("the cutscene rider records each page before pressing past it",
   ride.index("note_text(page_words(_pg), top)") < ride.index('U.tap(G, "a")'))
ck("every cutscene return of cross quotes the scene",
   cross.count('return true, "crossed (cutscene)"') == 0
   and cross.count('scene_said("crossed (cutscene)")') == 4
   and 'scene_said("crossed (mid-walk)")' in cross)
ck("the quote is only made when something was printed during the op",
   "text_seq ~= _seq_cross" in cross)
ck("every page read goes through page_words and names its box",
   "note_text(table.concat" not in shim
   and "note_text(page_words(pg), top)" in shim
   and "note_text(page_words(pg), t)" in shim)

# ---- the executor's excerpt ------------------------------------------------
SCENE = ("OAK: Hey! Wait! Don't go out! / OAK: It's unsafe! Wild POKéMON live "
         "in tall grass! You need your own POKéMON for your protection. I "
         "know! Here, come with me! / JERK: Gramps! I'm fed up with waiting! "
         "/ OAK: JERK? Let me think... Oh, that's right, I told you to come! "
         "Just wait! Here, SAGE! There are 3 POKéMON here! Haha! They are "
         "inside the POKé BALLs. When I was young, I was a serious POKéMON "
         "trainer! In my old age, I have only 3 left, but you can have one! "
         "Choose! / JERK: Hey! Gramps! What about me? / OAK: Be patient! "
         "JERK, you can have one too!")
for cap in (160, 220, 320, 480):
    ex = E.speech_excerpt(SCENE, cap)
    parts = ex.split(" / ")
    ck(f"at {cap}, the excerpt is whole boxes around its seams",
       parts[0] == "OAK: Hey! Wait! Don't go out!"
       and parts[-1] == "OAK: Be patient! JERK, you can have one too!"
       and parts[-2] == "JERK: Hey! Gramps! What about me?")
    ck(f"at {cap}, a cut box keeps the speaker the game printed",
       all(p == "..." or re.match(r"[A-Z]+: ", p) for p in parts))
ck("a scene that fits is untouched", E.speech_excerpt(SCENE, 2000) == SCENE)
ck("one long box is still cut head and tail",
   E.speech_excerpt("x" * 100 + " middle " + "y" * 200, 160).count(" ... ") == 1)
ck("a cut box starts on a whole word",
   " ... ung" not in E.speech_excerpt(SCENE, 320))

src = (ROOT / "planner/executor.py").read_text()
ck("a crossing that quoted its scene is not quoted twice",
   """if heard and 'the game said: "' not in note:""" in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

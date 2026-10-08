#!/usr/bin/env python3
"""Every boot turns the base's Union Room off, so Pokemon Centers have one
floor as in the original game.

gen1recomp e69b4087 (2026-10-07) added an upstairs Union Room to every Center,
default ON, with a missing key counting as ON; the run met a POKECENTER_2F the
original game does not have (user, 2026-10-08). run.sh asserts the rig's
options at every boot; unionRoom = false is one of them now, set whether the
key is there as true or missing. Runs the same two edits run.sh makes.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "run.sh").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

flip = re.search(r"s/\(unionRoom\[\[:space:\]\]\*=\[\[:space:\]\]\*\)true/\\1false/", src)
add = re.search(r"grep -q 'unionRoom' \"\$OPTS\" \|\| sed -i '([^']+)' \"\$OPTS\"", src)
ck("run.sh turns a true unionRoom false", flip)
ck("...and adds the key when it is missing", add)
if add:
    with tempfile.TemporaryDirectory() as d:
        for body in ('return {\n  colors = "gbc",\n}\n',
                     'return {\n  unionRoom = true,\n  colors = "gbc",\n}\n'):
            p = Path(d) / "options.lua"
            p.write_text(body)
            subprocess.run(["sed", "-i", "-E",
                            r"s/(unionRoom[[:space:]]*=[[:space:]]*)true/\1false/", str(p)])
            if "unionRoom" not in p.read_text():
                subprocess.run(["sed", "-i", add.group(1), str(p)])
            t = p.read_text()
            ck("an options file %s the key ends with it false"
               % ("with" if "unionRoom = true" in body else "without"),
               "unionRoom = false," in t and "unionRoom = true" not in t
               and t.startswith("return {\n"))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)

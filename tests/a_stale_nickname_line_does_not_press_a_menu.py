#!/usr/bin/env python3
"""A stale "nickname" line does not make a menu the nickname question.

After run 27 named its Abra, a party_swap before LT. SURGE backed out of the
PartyMenu; the back-out read last_text — still "Do you want to give a
nickname to ABRA?" — saw a cursor and no pages, and pressed A on slot 1.
The summary opened, each back-out opened it again, and the leg sat in
SummaryMenu four rounds with the badge fight one step away (2026-09-16,
user: "its stuck in the menus somehow when it tried to switch geodude into
first"). The executor's UI drain had the same stale-line test.

Pinned: the shim's back-out answers yes only on a ChoiceBox (onChoose, no
screenId); the executor's drain never treats a screen with a screenId as the
nickname question.

Synthetic: source anchors; no game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


SH = (ROOT / "harness/shim.lua").read_text()
bo = SH[SH.index("ui_back_out = function(G)"):]
bo = bo[:bo.index("\nend\n")]
ck("the back-out's nickname yes needs a ChoiceBox",
   "and t.onChoose ~= nil and t.screenId == nil then" in bo
   and bo.index("and t.onChoose ~= nil and t.screenId == nil then")
   < bo.index('_tx:find("nickname", 1, true)'))

SRC = (ROOT / "planner/executor.py").read_text()
ck("the drain's nickname yes skips any screen with a screenId",
   'and not _ui_d.get("screenId")):' in SRC)

cb = (Path.home() / "Developer/gen1recomp/src/ui/ChoiceBox.lua").read_text()
ck("the engine's ChoiceBox still carries onChoose",
   "self.onChoose = onChoose" in cb)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

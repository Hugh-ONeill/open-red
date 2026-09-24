#!/usr/bin/env python3
"""False facts in an outline: a confident claim the game does not bear out.

    planner/outline_facts.py plans/outline.authored plans/candidates/*.txt
    planner/outline_facts.py --run          the outline this run is playing:
                                            as authored, and every leg the
                                            chain inserted or reworded since

A GAP AND A FALSE FACT ARE NOT THE SAME SIZE OF FAULT (2026-09-19). Run 27
reached the Hall of Fame on an outline that never named the parcel, SURF,
the Secret Key or Victory Road: a gap stalls the run until the model writes
the missing leg, and it wrote five. A false fact sends the run somewhere
wrong for rounds, and the chain cannot simply be told "no": the model
builds them OUT OF TRUE ELEMENTS (user) -- the Coin Case is a real item and
the Game Corner a real place, and "Obtain the Coin Case from the Game
Corner" cost four attempts before the model voided it, with a reason that
was itself false ("not an item that can be obtained in this game").
Nothing on a page may correct it (the pamphlet standard: the harness never
hands over the answer), so the place to weigh it is OUR pick between
drafts, before a run is spent on one.

THREE KINDS, all read off one leg's own words:
  source    a real thing fetched from a place the game does not keep it
  badge     a badge name the game never prints
  garbled   something that is not in this game, or half-remembered past use

CHECK-SIDE ONLY. These tables are the game's answers. They are for the
person choosing between drafts (compare_outlines.py) and for reading trends
across draws (outline_trends.py); nothing here may reach a prompt.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (item, where the game gives it, the wrong places drafts name it)
SOURCES = [
    ("Secret Key", r"secret key", r"pokemon mansion|mansion",
     r"game corner|safari|celadon|saffron|ruins|cinnabar (gym|lab)|blaine"),
    ("HM03 SURF", r"hm03|\bsurf\b", r"safari|secret house|warden",
     r"cinnabar|gym|blaine|mansion|seafoam|fuchsia gym|koga|silph"),
    ("HM04 STRENGTH", r"hm04|strength", r"warden|fuchsia|safari|gold teeth",
     r"cinnabar|seafoam|victory|mansion|gym|celadon|game corner"),
    ("HM01 CUT", r"hm01|\bcut\b", r"s\.?\s?s\.?\s?anne|captain|vermilion",
     r"viridian|pewter|forest|mt\.? moon|cerulean|bill|celadon|game corner"),
    ("HM02 FLY", r"hm02|\bfly\b", r"route 16|celadon|cycling",
     r"vermilion|saffron|fuchsia|cinnabar|s\.?\s?s\.?\s?anne|lavender"),
    # ...AND NOT FROM BILL. "Obtain HM05 (FLASH) from Bill in his house on
    # Route 25" was inserted before Celadon and authored four times (run of
    # record, 2026-09-24); the aide who hands it over is on Route 2.
    ("HM05 FLASH", r"hm05|flash", r"route 2|oak's aide|aide|viridian forest",
     r"rock tunnel|celadon|lavender|vermilion|s\.?\s?s\.?\s?anne|bill|"
     r"route 25|cerulean|sea cottage"),
    ("Silph Scope", r"silph scope|\bscope\b", r"hideout|game corner|giovanni|rocket",
     r"silph co|saffron|lavender|tower|fuji|cinnabar"),
    ("Poke Flute", r"flute", r"fuji|tower|lavender",
     r"celadon|game corner|silph|saffron|vermilion|cycling|route 16"),
    # ...AND THE SHIP IT IS FOR IS NOT WHERE IT COMES FROM. Run 28 rewrote
    # its own leg to "from Bill on the S.S. Anne" and wrote four plans to
    # board the ship the ticket buys passage onto (2026-09-19).
    ("S.S. Ticket", r"ticket", r"bill|cerulean|sea cottage|route 25",
     r"captain|celadon|game corner|saffron|chief|vermilion|dock|fan club|"
     r"warden|s\.?\s?s\.? ?anne|\bship\b"),
    ("Bike Voucher", r"voucher", r"fan club|vermilion", r"cerulean|celadon|game corner"),
    ("Card Key", r"card key", r"silph|5f", r"celadon|game corner|hideout|saffron gym"),
    ("Gold Teeth", r"gold teeth", r"safari", r"tower|lavender|celadon|cinnabar"),
    ("Master Ball", r"master ball", r"silph|president", r"game corner|celadon|cinnabar"),
    ("Oak's Parcel", r"parcel", r"mart|viridian", r"pewter|oak's lab$|cerulean"),
    ("Old Amber", r"old amber|amber", r"museum|pewter", r"mt\.? moon|cinnabar|lab"),
    # run 27's own: inserted in play, four attempts, then voided with a
    # reason that was false too. The case is handed over in the Celadon
    # diner; the Game Corner is where it is USED.
    ("Coin Case", r"coin case", r"restaurant|diner|cafe",
     r"game corner|prize|hideout|rocket|mart|department"),
]

# names the game never prints
WRONG_BADGE = re.compile(r"\b(thunderbolt|grass|psychic|fire|poison|water|"
                         r"rock|electric|ground|ghost|fighting) badge", re.I)
BADGES = ["boulder", "cascade", "thunder", "rainbow", "soul", "marsh",
          "volcano", "earth"]

# things that are not in this game, or garbled past use
NONSENSE = [
    # A POKE BALL FROM THE MART IS WHERE POKE BALLS COME FROM. This row
    # read "(pokemon|poke balls?) from the (mart|...)" and refused the
    # wording rung's "Obtain the Poké Ball from the Poké Mart in Viridian
    # City and reach Pewter City" twice, on the run of record's leg 4
    # (2026-09-24) — the one answer that would have walked the run into
    # the clerk who hands over the parcel — and the chain stopped. What is
    # false is a POKEMON from the mart (the parcel, garbled) and a ball
    # from a resident who does not exist, or from a Center that sells none.
    ("a Pokemon 'retrieved' from the Poke Mart (the parcel, garbled)",
     r"(retrieve|get|obtain).*\bpokemon from the (poke ?mart|pokemon center|mart)"),
    ("a Poke Ball from the Pokemon Center, or from a resident who does not exist",
     r"(retrieve|get|obtain).*(pokemon|poke ?balls?) from the "
     r"(pokemon center|[a-z ]*(resident|villager|neighbou?r))"),
    ("an 'MT' fetched from somewhere", r"\bthe mt\b"),
    ("the Safari Zone entered by a trade", r"trade for the safari"),
    ("a Pikachu from the S.S. Anne", r"pikachu.*anne|anne.*pikachu"),
    ("an 'Ethereal' anything", r"ethereal"),
    ("Secret Key 'returned' anywhere", r"return the secret key"),
    ("'Secret Technique'", r"secret technique"),
    ("Cycling Road as a place to GET the bicycle", r"bicycle from the cycling road|bike from the cycling road"),
    ("Rival as Champion by name 'Champion' before the Elite Four", r"defeated rival as the champion"),
]


_ACQUIRE = re.compile(r"(obtain|retrieve|get|receive|collect|find|acquire|"
                      r"pick up|take|grab|buy|purchase|win|earn|fetch)", re.I)
_CLAUSE_END = re.compile(r"[,;:]|\b(then|afterwards?|next|and then|so that|"
                         r"in order to|to (?:board|use|reach|enter|open|show)|"
                         r"before|after|once)\b", re.I)
_FROM = re.compile(r"\b(from|in|at|inside|within|off)\b", re.I)


def _plain(leg: str) -> str:
    """The leg with accents folded (Poké -> Poke), for the tables above."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(leg or ""))
                   if not unicodedata.combining(c))


def false_facts(legs) -> list:
    """[(kind, leg, why)] for every leg that states something false.

    One row per leg at most, the first kind that fits: a leg is a single
    instruction, and it is wrong once however many ways it is wrong."""
    out = []
    for leg in legs:
        p = _plain(leg)
        hit = None
        # THE THING BEFORE THE PREPOSITION, THE PLACE AFTER IT. Read whole,
        # "Obtain the CUT HM from the S.S. Ticket/Captain" named the ticket
        # and the captain and was filed as the ticket got from the wrong
        # man, when it is CUT got from the right one.
        m = _FROM.search(p)
        head, tail = (p[:m.start()], p[m.end():]) if m else (p, "")
        # ...AND ONLY THE CLAUSE THAT SAYS WHERE IT COMES FROM. A wrong
        # place counts beside a right one ("from BILL on the S.S. ANNE"),
        # but a sentence that fetches it in one clause and uses it in the
        # next ("from Bill at the Sea Cottage, then board the S.S. Anne")
        # says nothing false and must not be caught (user, 2026-09-20:
        # "what were running the danger of is this grabbing true facts
        # too"). The clause ends at a comma, a semicolon, or a word that
        # starts the next deed.
        tail = _CLAUSE_END.split(tail, 1)[0]
        # ...and only a leg that GETS the thing claims where it is got:
        # "Use the Coin Case at the Game Corner" is true.
        if not _ACQUIRE.match(head.strip()):
            tail = ""
        for item, rx, right, wrong in SOURCES:
            # A WRONG PLACE IS WRONG EVEN BESIDE A RIGHT ONE. The right
            # name used to excuse the sentence, so "the S.S. Ticket from
            # BILL on the S.S. ANNE" read as true on the strength of Bill
            # (2026-09-19). Each table's wrong list names places the thing
            # is NOT kept, so naming one is the false claim whatever else
            # the sentence says.
            if (tail and re.search(rx, head, re.I)
                    and re.search(wrong, tail, re.I)):
                hit = ("source", leg, f"{item} is not got there")
                break
        if not hit:
            m = WRONG_BADGE.search(p)
            if m:
                hit = ("badge", leg, f"the game prints no "
                                     f"'{m.group(0).title()}'")
        if not hit:
            for label, rx in NONSENSE:
                if re.search(rx, p, re.I):
                    hit = ("garbled", leg, label)
                    break
        if hit:
            out.append(hit)
    return out


def _read(path: Path) -> list:
    try:
        return [l.strip() for l in path.read_text().splitlines() if l.strip()]
    except OSError:
        return []


def run_legs() -> list:
    """[(where it came from, leg)] for the outline this run is playing: as
    authored, plus what the chain has inserted or reworded since."""
    rows = [("authored", l) for l in _read(REPO / "plans/outline.authored")]
    for l in _read(REPO / "run/outline_inserts"):
        # LEG=<the leg it was put after>|<the new leg>
        if "|" in l:
            rows.append(("inserted in play", l.split("|", 1)[1].strip()))
    for l in _read(REPO / "run/outline_rewordings"):
        # <leg index>\t<old wording>\t<new wording>
        parts = l.split("\t")
        if len(parts) >= 3:
            rows.append(("reworded in play", parts[2].strip()))
    # ...AND WHAT WAS INSERTED AND THEN TAKEN BACK OUT. A voided leg leaves
    # run/outline_inserts, and the voided ones are exactly the false facts
    # worth counting (the Coin Case was one). The chain's own log keeps
    # every insert of this game: read it back to the last fresh start.
    try:
        log = (REPO / "run/chain.log").read_text(errors="ignore").splitlines()
    except OSError:
        log = []
    start = max((i for i, l in enumerate(log) if "ledgers cleared" in l),
                default=0)
    for l in log[start:]:
        m = re.match(r"inserted (?:before|after) leg \d+: (.+)", l)
        if m:
            rows.append(("inserted in play", m.group(1).strip()))
    seen, out = set(), []
    for src, leg in rows:
        if leg not in seen:
            seen.add(leg)
            out.append((src, leg))
    return out


def main(argv):
    if argv and argv[0] == "--run":
        rows = run_legs()
        bad = {leg: (kind, why) for kind, leg, why
               in false_facts([l for _, l in rows])}
        print(f"{len(rows)} leg(s): authored, inserted and reworded")
        n = 0
        for src, leg in rows:
            if leg in bad:
                n += 1
                kind, why = bad.pop(leg)
                print(f"  FALSE ({kind}, {src}): {leg!r} -- {why}")
        print(f"{n} false fact(s)")
        return
    if not argv:
        sys.exit(__doc__)
    for p in argv:
        legs = _read(Path(p))
        ff = false_facts(legs)
        print(f"{Path(p).name}: {len(ff)} false fact(s) in {len(legs)} legs")
        for kind, leg, why in ff:
            print(f"  {kind:<8} {leg!r} -- {why}")


if __name__ == "__main__":
    main(sys.argv[1:])

"""Where the party actually stands, as one line for a re-author's --start.

Extracted from campaign.sh so the outline chain and the replan loop
describe the world with the same words. Mechanical save-reading only —
manual-tier under CLAIM_RULES.
"""
import json
from pathlib import Path

# last_state.json is written by the executor as it exits, so it OUTLIVES the
# game process; obs.json belongs to the live bridge and is gone by the time
# the re-author runs.
o = None
for src in ("run/last_state.json", "run/obs.json"):
    try:
        o = json.load(open(src))
        break
    except Exception:
        continue
if o is None:
    print("a brand new game")
    raise SystemExit

# A SNAPSHOT WITH NO PARTY IS NOT THIS WORLD. An attempt that dies in
# bootstrap still leaves a state file behind, and it holds the pre-load
# screen: no party, no badges, 3000 money, an empty bag. Described in
# those words it is a LIE about a save wearing six badges, and the
# re-author writes its plan against it (leg 41, 2026-08-23; the same lie
# the "brand new game" fallback made before 2f2276a, arriving by another
# road). A run past its first minute always has a party; no party means
# the snapshot is not of the world this leg is being written for, and
# "an unknown location" is the honest thing to say about it.
if not (o.get("party") or []):
    print("an unknown location")
    raise SystemExit


# HP reaches the start text: the audit's ALREADY DONE check pruned
# buy_potions because the bag was visible here, but kept every heal leg —
# and the Pewter round trip serving them — because health never was.
def mon_text(p):
    s = f"{p.get('species')} L{p.get('level')}"
    # ITS TYPES ARE ON THE PARTY SCREEN. Without them the sweep's
    # already-done judgment saw "CHARIZARD L37" and could not tell it was
    # the FLYING type the objective wanted.
    tys = [str(t) for t in (p.get("types") or []) if t]
    if tys:
        s += f" ({'/'.join(tys)})"
    hp, mx = p.get("hp"), p.get("max_hp")
    if hp is not None and mx:
        s += f" {hp}/{mx}hp"
    # WHAT IT CAN ACTUALLY DO. The author was told a level and a HP bar and
    # nothing else, so it could not reason about the four slots at all —
    # Charmeleon lost to Misty twelve times swinging RAGE with GROWL and
    # LEER filling half its moveset and TM_MEGA_PUNCH in the bag, and every
    # rewrite came back "go, heal, enter, fight". The party screen shows
    # moves; a plan written without them is written half-blind.
    mv = [str(m.get("id") if isinstance(m, dict) else m)
          for m in (p.get("moves") or [])]
    if mv:
        s += " knowing " + "/".join(mv)
    st = str(p.get("status") or "")
    if st not in ("", "0", "NONE", "OK"):
        s += f" {st}"
    return s


def party_text(mons):
    txt = ", ".join(mon_text(p) for p in mons)
    full = [p for p in mons if p.get("max_hp")]
    if full and all(p.get("hp") == p.get("max_hp") for p in full):
        txt += " (party at full HP)"
    return txt


def _machine_numbers():
    """id -> number for the HMs (HM_FLY -> HM02), from the engine's own list.
    An HM is handed over by a person who names both ("HM02 ... FLY"), so
    both names are the player's; the judge read "Retrieve the HM02" against
    a bag saying HM_FLY and twice refused a leg that was done (run 16,
    2026-09-08). TMs are left as they are: the page reads them by number
    until booted, and this text is not where that rule lives."""
    out = {}
    try:
        for row in (Path(__file__).with_name("engine_tm_numbers.txt")
                    .read_text().splitlines()):
            parts = row.split()
            if len(parts) >= 2 and parts[0].startswith("HM_"):
                out[parts[0]] = parts[1]
    except OSError:
        pass
    return out


def _item_word(k, nums):
    return f"{k} ({nums[k]})" if k in nums else str(k)


def _stone_word(k):
    """A stone in the author's bag line says what a wrong try costs:
    nothing (2026-09-08; the executor's page says the same)."""
    if str(k).endswith("_STONE"):
        return (" (an evolution stone — used on a party member it suits it "
                "evolves them at once; on one it does not suit the game says "
                "\"It won't have any effect\" and keeps the stone)")
    return ""


def bag_text(bagd):
    nums = _machine_numbers()
    txt = (", ".join(f"{_item_word(k, nums)} x{v}{_stone_word(k)}"
                     for k, v in (bagd or {}).items())
           or "an empty bag")
    n = len(bagd or {})
    # the 20-kind cap is a wall the plan must plan around: a full bag
    # eats every gift silently, so its fullness belongs in the one line
    # every author and reviewer reads
    if n >= 20:
        txt += (" — the bag is FULL (20 of 20 kinds; gifts and pickups "
                "FAIL until something is used, sold or tossed)")
    elif n >= 18:
        txt += f" — the bag is NEARLY FULL ({n} of 20 kinds)"
    return txt


def pc_text(pc):
    """What the PC is holding, after the bag. On-screen tier: WITHDRAW ITEM
    at any Pokemon Center lists it. Without it a thing the run put away was
    gone from every plan: run 36 stored the GOLD TEETH at Viridian to make
    room for HM04, and the next HM04 drafts went looking for the teeth in
    the Safari Zone's Secret House (2026-10-05). Key items and machines
    are named in full; the rest is counted."""
    pc = {k: v for k, v in (pc or {}).items() if (v or 0) > 0}
    if not pc:
        return ""
    try:
        keys = {l.strip() for l in Path(__file__).with_name(
            "engine_key_items.txt").read_text().splitlines() if l.strip()}
    except OSError:
        keys = set()
    nums = _machine_numbers()
    named = sorted(k for k in pc if k in keys or k.startswith(("HM_", "TM_")))
    rest = len(pc) - len(named)
    return (" — and in the PC (WITHDRAW ITEM at any Pokemon Center): "
            + (", ".join(f"{_item_word(k, nums)} x{pc[k]}" for k in named)
               or "no key items or machines")
            + (f", and {rest} other kind(s) of item" if rest else ""))


def money_text(m):
    """How much money there is, next to what things cost.

    Everything else about a purchase reaches the author — the bag, the
    fullness of it, the price the day care asks — but never the wallet, so
    "it costs 100" could not be compared with anything. The run stood two
    coins short of its own CHARIZARD (98 against 100) with a NUGGET in the
    bag worth thousands, and no way to notice.
    """
    if m is None:
        return ""
    return f", {int(m)} money"


def hof_text(n):
    """The save's own count of Hall of Fame inductions (the PC shows it)."""
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        n = 0
    if n <= 0:
        return ""
    return (f" — the party has been entered into the HALL OF FAME "
            f"{n} time{'s' if n != 1 else ''}: the game is finished")


def respawn_text(r):
    """Where a faint sends you back to — the stake on every fight.

    Set by healing, so it can be hundreds of steps behind the party. It
    was never stated before the fact, only mourned after.
    """
    if not r or not r.get("map"):
        return ""
    where = r.get("outdoor") or r.get("map")
    return (f" — if your party faints you wake at {where}, the last Pokemon "
            f"Center you healed at (healing at a Center makes it the place "
            f"you wake)")


def centers_text(here_map):
    """Every room the run has seen a nurse in — any of them heals — with the
    ones on this map or one walked door from it named as such.

    The start line named one Center, the wake point, and the training plans
    for "every party member at level 50" all went back through Victory Road
    to heal at Viridian while INDIGO_PLATEAU_LOBBY, its nurse in the run's
    own sightings, was a few steps from Route 23 (run 27, 2026-09-18; user:
    "it kept trying to go to viridian"). The run's own record only."""
    try:
        import json as _json
        from pathlib import Path as _P
        d = _json.loads((_P(__file__).resolve().parents[1] / "run" / "explored.json")
                        .read_text() or "{}")
    except Exception:
        return ""
    rooms = sorted({str(r).split("|")[0]
                    for r, names in (d.get("sightings") or {}).items()
                    if any("NURSE" in str(n).upper() for n in (names or []))})
    if not rooms:
        return ""
    # walked hops between MAPS, up to three: the run's own edges only
    adj: dict = {}
    for r, ex in (d.get("explored") or {}).items():
        a = str(r).split("|")[0]
        for e in (ex or {}).values():
            b = str((e or {}).get("to") or "").split("|")[0]
            if b and b != a and not (e or {}).get("shut"):
                adj.setdefault(a, set()).add(b)
    hops = {str(here_map or ""): 0}
    frontier = [str(here_map or "")]
    for depth in (1, 2, 3):
        nxt = []
        for a in frontier:
            for b in adj.get(a, ()):
                if b not in hops:
                    hops[b] = depth
                    nxt.append(b)
        frontier = nxt
    words = []
    for m2 in sorted(rooms, key=lambda x: (hops.get(x, 9), x)):
        h = hops.get(m2)
        words.append(m2 + (" (right here)" if h == 0 else
                           f" ({h} walked hop(s) from here)" if h else ""))
    return (" — ANY Pokemon Center heals, and the rooms where you have seen a "
            "nurse are: " + ", ".join(words[:8])
            + (f" and {len(words) - 8} more" if len(words) > 8 else ""))


def daycare_text(dc):
    """The Pokemon that is NOT in the party because it is being raised.

    A missing party member is otherwise invisible: the start line simply
    reads one Pokemon shorter and nothing says why or how to undo it. The
    run handed a level 40 CHARIZARD to the Day Care Man and went on trying
    to win a grass gym with a level 6 MAGIKARP.
    """
    if not dc or not dc.get("species"):
        return ""
    lvl = f" L{dc['level']}" if dc.get("level") else ""
    cost = f" for {dc['cost']}" if dc.get("cost") else ""
    return (f" — your {dc['species']}{lvl} is NOT with you: it is at the "
            f"DAY CARE and can be taken back{cost} by talking to the man "
            f"there")


# THE EIGHT, AND WHICH ARE STILL TO WIN. The booklet shows all eight badges
# and names each gym's leader (pamphlet tier). Listing only the ones held let
# the run write "I have all 8 badges" holding six, at Viridian's locked gym
# with Blaine unbeaten (run 19, 2026-09-30; user: "it should recognize the
# lack of event_beat_blaine"). The ones still to win are named by LEADER, not
# by badge: the done guards search this text for badge names, and a badge
# named as missing would read there as a badge held.
_LEADERS = [("BOULDERBADGE", "Brock's (Pewter City gym)"),
            ("CASCADEBADGE", "Misty's (Cerulean City gym)"),
            ("THUNDERBADGE", "Lt. Surge's (Vermilion City gym)"),
            ("RAINBOWBADGE", "Erika's (Celadon City gym)"),
            ("SOULBADGE", "Koga's (Fuchsia City gym)"),
            ("MARSHBADGE", "Sabrina's (Saffron City gym)"),
            ("VOLCANOBADGE", "Blaine's (Cinnabar Island gym)"),
            ("EARTHBADGE", "Giovanni's (Viridian City gym)")]


def badges_text(held) -> str:
    held = [str(b) for b in (held or [])]
    if not held:
        return "no badges (8 to win)"
    left = [who for b, who in _LEADERS if b not in held]
    return (", ".join(held) + f" — {len(held)} of the 8 badges"
            + ("; not yet won: " + ", ".join(left) if left else ", all of them"))


if "region" in o:                    # last_state.json is already flattened
    m = o.get("map")
    party = party_text(o.get("party") or [])
    badges = badges_text(o.get("badges"))
    bag = bag_text(o.get("bag"))
    # A BOX UP AT THE SNAPSHOT IS NOT AN UNKNOWN WORLD. map is None while a
    # text box is open; with a party in hand that is still this run's world
    # and the done rung must be allowed to judge it (2026-08-29: leg 1 ended
    # holding CHARMANDER under a box and was refused as "no party").
    _where = m or "a spot not yet on record (a box was up when the snapshot was taken)"
    print(f"standing in {_where} with "
          f"{party or 'no party'}, {badges}"
          + money_text(o.get("money")) + f", and {bag}" + pc_text(o.get("pc_items"))
          + daycare_text(o.get("daycare"))
          + hof_text(o.get("hall_of_fame"))
          + respawn_text(o.get("respawn"))
          + centers_text(m))
    raise SystemExit
m = (o.get("map") or {}).get("id")
if not m:
    # no map AND no party: a stale or title-screen obs, not this world
    if not (o.get("party") or []):
        print("an unknown location")   # never "standing in None"
        raise SystemExit
    # no map but a party: a box was up when the snapshot was taken; the
    # party, badges and bag are this run's and the done rung may read them
    party = party_text(o.get("party") or [])
    badges = badges_text(o.get("badges"))
    print("standing in a spot not yet on record (a box was up when the "
          f"snapshot was taken) with {party}, {badges}"
          + money_text(o.get("money")) + f", and {bag_text(o.get('bag'))}"
          + pc_text(o.get("pc_items"))
          + daycare_text(o.get("daycare"))
          + hof_text(o.get("hall_of_fame"))
          + respawn_text(o.get("respawn")))
    raise SystemExit
party = party_text(o.get("party") or [])
badges = badges_text(o.get("badges"))
bag = bag_text(o.get("bag"))
print(f"standing in {m} with {party or 'no party'}, {badges}"
      + money_text(o.get("money")) + f", and {bag}" + pc_text(o.get("pc_items"))
      + daycare_text(o.get("daycare"))
      + hof_text(o.get("hall_of_fame"))
      + respawn_text(o.get("respawn"))
      + centers_text(m))

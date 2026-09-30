-- WHAT A THING IS CALLED IS WHAT THE SCREEN SHOWS OF IT.
--
-- The map data names every object by what it IS (MTMOONB2F_HELIX_FOSSIL,
-- POWERPLANT_ZAPDOS, TEXT_FUCHSIACITY_GYM_SIGN, FUCHSIACITY_ERIK), and
-- those names reached every prompt, ledger row and plan: the ROM telling
-- the model which fossil is which before the blind pick, which bird is a
-- legendary, what a signpost says before it is read (user, 2026-09-29:
-- "the player cant see the sign title"). Items were already renamed by
-- position (ITEM_<MAP>_x_y, 2026-08-18); this is the same rule for the
-- rest, keyed on the SPRITE, which is what a player actually sees:
--   * a signpost             -> SIGN_<MAP>_x_y (every signpost looks alike;
--                               its words come from reading it)
--   * a fossil, clipboard, book or paper on a table
--                            -> FOSSIL_/CLIPBOARD_/BOOK_/PAPER_<MAP>_x_y
--   * a Pokemon on a shared Monster/Bird/Fairy/Seel sprite
--                            -> POKEMON_<MAP>_x_y (its species shows at its
--                               cry or in the fight)
--   * a Poke Ball on the ground, whatever waits in it (the Power Plant's
--     Voltorb, the Eevee on the Mansion roof) -> ITEM_<MAP>_x_y
--   * a story person on a shared sprite whose name neither the sprite nor
--     the room supports (Erik on a Fisher sprite in the street, the Fan
--     Club's fans, the Mansion's game staff) -> <SPRITE CLASS>_<MAP>_x_y
-- Trainers, boulders, gym leaders (the booklet names them), clerks, nurses
-- and people whose room carries their name (BILLS_HOUSE, COPYCATS_HOUSE,
-- the Fan Club's Chairman, the Aides in Oak's gates) keep their names.
-- The real names still resolve in interact, so older macros keep replaying.
--
-- Loaded by harness/shim.lua and by tools/public_names_table.lua, which
-- writes the old->new table the planner uses to carry its ledger over.

local P = {}

P.POKEMON_SPRITES = {
  SPRITE_MONSTER = true, SPRITE_BIRD = true, SPRITE_FAIRY = true,
  SPRITE_SEEL = true,
}

P.THING_SPRITES = {
  SPRITE_FOSSIL = "FOSSIL", SPRITE_CLIPBOARD = "CLIPBOARD",
  SPRITE_POKEDEX = "BOOK", SPRITE_PAPER = "PAPER",
}

-- (user, 2026-09-29: "keep a name the screen supports (sprite + the room it
-- stands in)"). Each of these stands on a sprite shared with dozens of
-- strangers, in a room that does not carry the name.
P.MASKED_PEOPLE = {
  FUCHSIACITY_ERIK = true,
  MTMOONPOKECENTER_MAGIKARP_SALESMAN = true,
  CELADONMANSION3F_GAME_DESIGNER = true,
  CELADONMANSION3F_GRAPHIC_ARTIST = true,
  CELADONMANSION3F_WRITER = true,
  CELADONMANSION3F_PROGRAMMER = true,
  POKEMONFANCLUB_PIKACHU_FAN = true,
  POKEMONFANCLUB_SEEL_FAN = true,
}

local function at(prefix, mapid, x, y)
  return ("%s_%s_%d_%d"):format(prefix, tostring(mapid or "?"),
                                tonumber(x) or 0, tonumber(y) or 0)
end

function P.is_ball(d)
  d = d or {}
  return ((d.name or ""):find("POKE_BALL") or d.item
          or d.sprite == "SPRITE_POKE_BALL") and true or false
end

-- The published name of a map object (a def from md.objects / npc.def).
-- Placed by where the map puts it (d.x, d.y), not where it stands now: the
-- Chansey in Fuchsia and the Spearow in the nickname house walk, and a name
-- that moved with them would be a new thing every few steps. x, y are the
-- fallback for a def that carries no position.
function P.object(mapid, d, x, y)
  d = d or {}
  x, y = d.x or x, d.y or y
  local name = d.name or ""
  if P.is_ball(d) then return at("ITEM", mapid, x, y) end
  if d.trainerClass or d.sprite == "SPRITE_BOULDER" then return name end
  local s = d.sprite or ""
  if P.POKEMON_SPRITES[s] then return at("POKEMON", mapid, x, y) end
  if P.THING_SPRITES[s] then return at(P.THING_SPRITES[s], mapid, x, y) end
  if P.MASKED_PEOPLE[name] and s ~= "" then
    return at((s:gsub("^SPRITE_", "")), mapid, x, y)
  end
  return name
end

-- The published name of a live overworld npc, or `fallback` when the map
-- gives it no name at all.
function P.of(mapid, npc, fallback)
  local d = (npc and npc.def) or {}
  if not d.name and not P.is_ball(d) then return fallback end
  return P.object(mapid, d, npc.cellX, npc.cellY)
end

-- The published name of an md.signs entry. A signpost (and a Trainer Tips
-- board, which is one) says nothing until read; the rest of that list is
-- scenery whose name is what it looks like (a PC, a TV, binoculars, a
-- vending machine) and keeps it. The captain's book is a book.
function P.sign(mapid, sg)
  sg = sg or {}
  local nm = sg.name or sg.text or ("SIGN_" .. tostring(sg.x) .. "_"
                                    .. tostring(sg.y))
  if nm:find("SEASICK_BOOK") then return at("BOOK", mapid, sg.x, sg.y) end
  if nm:find("SIGN") or nm:find("TRAINER_TIPS") then
    return at("SIGN", mapid, sg.x, sg.y)
  end
  return nm
end

-- The map's own name for a thing, from a published name: the object or
-- sign on this map whose published name is `name`, or nil.
function P.resolve(mapid, md, name)
  for _, od in ipairs((md and md.objects) or {}) do
    if P.object(mapid, od, od.x, od.y) == name then return od, "object" end
  end
  for _, sg in ipairs((md and md.signs) or {}) do
    if P.sign(mapid, sg) == name then return sg, "sign" end
  end
  return nil
end

return P

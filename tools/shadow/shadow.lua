-- SHADOW: plays a recorded run again, step for step, at watching speed.
--
-- A POKEPORT_DRIVER like the shim, but it decides nothing: every button,
-- every audio answer and every jump comes from the log harness/replay_rec.lua
-- wrote for one boot of the 200x game ($SHADOW_SEG). Launched by
-- tools/shadow/play.py under its own love identity, so nothing it saves can
-- reach the run's save.
--
-- Pacing: a step near something happening (a button, an audio wait, a held
-- button, a jump) plays at $SHADOW_SPEED (1 = the game's own speed); the
-- model's thinking time, where the game only idles, is run through faster,
-- up to $SHADOW_IDLE_MAX x. Speed changes at a fixed acceleration both ways
-- and brakes ahead of the next thing that happens, so an idle stretch
-- speeds up and slows down instead of jumping (user, 2026-10-03: "a
-- smoother pace through the idle stretches, instead of jumping to x200").
-- The sound fades out as the speed rises. The idle steps still have to run:
-- NPCs wander on them and draw from the random generator.
--
-- THE VIEW IS LOGIC TOO. How much map the window shows decides which
-- neighbor maps are loaded (their NPCs wander and draw randomness every
-- step) and which NPCs a map entry sends back to their spawn (an off-camera
-- reset draws randomness too): OverworldController rebuildNeighbors and
-- applyPendingSpawnResets read Renderer:worldViewSize, which is the window's
-- size. A copy in a different window had an NPC in the path that the run
-- did not (run 36, step 369,000, Pallet Town). So this copy takes the run's
-- window and view size from its V lines (or $SHADOW_WINDOW=WxH for a log
-- recorded before they existed).
--
-- Every 1800 steps (the recorder's CHECK_EVERY) the run's random state, map
-- and cell are compared with this copy's; the first difference is printed
-- and written to $SHADOW_SEG/shadow_report, which is how a desync is found.
local SEG = assert(os.getenv("SHADOW_SEG"), "SHADOW_SEG is not set")
local PLAY = tonumber(os.getenv("SHADOW_SPEED") or "1") or 1
local IDLE_MAX = tonumber(os.getenv("SHADOW_IDLE_MAX") or "200") or 200
local RAMP_S = tonumber(os.getenv("SHADOW_RAMP") or "1.5") or 1.5  -- seconds 1x -> max
local ACCEL = math.max(0.05, (IDLE_MAX - PLAY) / (60 * RAMP_S))     -- steps/frame per frame
local LOOKAHEAD = 30           -- steps before an event that already play
local TRAIL = 60               -- ...and after one
local FF_SLICE = 0.012         -- seconds of stepping per frame at most
local FOLLOW = os.getenv("SHADOW_FOLLOW") == "1"   -- wait for the log to grow
-- WHICH BATTLES ARE SHOWN (user, 2026-10-03: "we can skip through wild
-- battles, maybe we just show trainer fights, or if that ends up being too
-- much then just the gym leaders / e4 maybe a couple of the specific event
-- battles"). A skipped battle still runs every step (the copy must stay in
-- step with the run) but fast, muted, under a card that says what it was.
--   all       every battle
--   trainers  trainer battles and event battles (a scripted wild fight:
--             Snorlax, the legendaries, Mewtwo), not grass/cave/water ones
--   bosses    gym leaders, the rival, Giovanni, the Elite Four and champion,
--             and event battles
--   none      nothing
local SHOW = os.getenv("SHADOW_SHOW_BATTLES") or "trainers"
local SKIP_SPEED = tonumber(os.getenv("SHADOW_SKIP_SPEED") or "400") or 400
-- WHICH OPS ARE SKIPPED, the same way: a grind is minutes of pacing in grass
-- that the 200x run makes in seconds, and played at 1x it put the copy over an
-- hour behind (2026-10-03, ROUTE_4). Comma list of op names; "" skips none.
local SKIP_OPS = {}
for name in (os.getenv("SHADOW_SKIP_OPS") or "grind"):gmatch("[^,%s]+") do SKIP_OPS[name] = true end
-- CATCHING UP: once the copy is more than CATCHUP_AFTER seconds of play
-- behind the log, plain walking (the overworld with nothing on screen to
-- read) plays at CATCHUP_SPEED; text, menus and shown battles stay at 1x.
local CATCHUP_AFTER = (tonumber(os.getenv("SHADOW_CATCHUP_AFTER") or "180") or 180) * 60
local CATCHUP_SPEED = tonumber(os.getenv("SHADOW_CATCHUP_SPEED") or "3") or 3
-- WALKING, ALWAYS A LITTLE QUICKER: the overworld with nothing on screen to
-- read plays at WALK_SPEED even when the copy is not behind (user,
-- 2026-10-03: "was there a speedup of walking in general because that might
-- be nice"); text, menus and shown battles stay at 1x.
local WALK_SPEED = tonumber(os.getenv("SHADOW_WALK_SPEED") or "2") or 2
-- THE LAG CAP: more than MAX_LAG seconds behind the run's clock and the copy
-- runs everything through under a CATCHING UP card until it is within
-- CATCHUP_TO again. Whatever the run does, the stream cannot drift hours
-- behind (2026-10-04: 4 h 45 m behind after a night of a stuck elevator).
local MAX_LAG = tonumber(os.getenv("SHADOW_MAX_LAG") or "600") or 600
local CATCHUP_TO = tonumber(os.getenv("SHADOW_CATCHUP_TO") or "180") or 180
catching_up = false
-- THE CARD STAYS UP LONG ENOUGH TO READ: a skipped trainer fight is a few
-- frames at skip speed and its card only flashed (user, 2026-10-03). If the
-- skip ends sooner than CARD_MIN seconds after the card came up, the card
-- stays with its last words and the copy holds still until it has been read.
local CARD_MIN = tonumber(os.getenv("SHADOW_CARD_MIN") or "2.5") or 2.5
-- what this copy shows, for the HUD (tools/hud.py reads it before obs.json)
local SNAP = os.getenv("SHADOW_SNAPSHOT")
  or ((os.getenv("HOME") or ".") .. "/.local/state/red-recomp/shadow_obs.json")
local QUIET = os.getenv("SHADOW_QUIET") == "1"

local Game = require("src.core.Game")
local Input = require("src.core.Input")

-- ------------------------------------------------------------------ the log
local L = {
  pos = 0, horizon = 0, boot = nil,
  inputs = {}, in_i = 1,          -- {step, pressed, held, alias}
  audio = {}, au_i = 1,           -- {start, len, {answers}}
  events = {}, ev_i = 1,          -- {step, kind, arg}
  checks = {}, ck_i = 1,          -- {step, rng, map, x, y}
  views = {}, vw_i = 1,           -- {step, window w, h, view w, h}
  times = {}, tm_i = 1,           -- {step, epoch}: when the run ran that step
  ops = {}, op_i = 1,             -- {start, stop or nil, name}
  ended = false,
}
local function split(s, sep)
  local out = {}
  if s == "-" or s == nil then return out end
  for part in string.gmatch(s, "[^" .. sep .. "]+") do out[#out + 1] = part end
  return out
end
local function set_of(s)
  local t = {}
  for _, k in ipairs(split(s, ",")) do t[k] = true end
  return t
end
local function read_more()
  local f = io.open(SEG .. "/log", "rb")
  if not f then return end
  f:seek("set", L.pos)
  local chunk = f:read("*a") or ""
  f:close()
  local last_nl = chunk:match(".*()\n")
  if not last_nl then return end
  L.pos = L.pos + last_nl
  for line in string.gmatch(chunk:sub(1, last_nl), "([^\n]*)\n") do
    local kind, rest = line:match("^(%a) (.*)$")
    if kind == "I" then
      local s, p, h, a = rest:match("^(%d+) (%S+) (%S+) (%S+)$")
      if s then
        L.inputs[#L.inputs + 1] = { tonumber(s), set_of(p), set_of(h), set_of(a) }
        L.horizon = math.max(L.horizon, tonumber(s))
      end
    elseif kind == "A" then
      local s, n, seq = rest:match("^(%d+) (%d+) (%S+)$")
      if s then
        local ans = {}
        for _, a in ipairs(split(seq, ",")) do
          local tag, v = a:sub(1, 1), a:sub(2)
          local val
          if v == "1" and tag ~= "t" then val = true
          elseif v == "0" and tag ~= "t" then val = false
          elseif v == "n" then val = nil
          else val = tonumber(v) end
          ans[#ans + 1] = { tag, val }
        end
        L.audio[#L.audio + 1] = { tonumber(s), tonumber(n), ans }
        L.horizon = math.max(L.horizon, tonumber(s) + tonumber(n) - 1)
      end
    elseif kind == "R" or kind == "G" or kind == "W" or kind == "P" then
      local s, arg = rest:match("^(%d+) ?(.*)$")
      if s then
        L.events[#L.events + 1] = { tonumber(s), kind, arg }
        L.horizon = math.max(L.horizon, tonumber(s) - 1)
      end
    elseif kind == "H" then
      local s, r, m, x, y = rest:match("^(%d+) (%S+) (%S+) (%S+) (%S+)$")
      if s then
        L.checks[#L.checks + 1] = { tonumber(s), r, m, x, y }
        L.horizon = math.max(L.horizon, tonumber(s) - 1)
      end
    elseif kind == "O" then
      local s, name = rest:match("^(%d+) (%S+)$")
      if s then
        s = tonumber(s)
        if name == "-" then
          local last = L.ops[#L.ops]
          if last and not last[2] then last[2] = s end
        else
          L.ops[#L.ops + 1] = { s, nil, name }
        end
        L.horizon = math.max(L.horizon, s - 1)
      end
    elseif kind == "T" then
      local s, t = rest:match("^(%d+) (%d+)$")
      if s then
        L.times[#L.times + 1] = { tonumber(s), tonumber(t) }
        L.horizon = math.max(L.horizon, tonumber(s) - 1)
      end
    elseif kind == "V" then
      local s, pw, ph, vw, vh = rest:match("^(%d+) (%d+) (%d+) (%d+) (%d+)$")
      if s then
        L.views[#L.views + 1] = { tonumber(s), tonumber(pw), tonumber(ph), tonumber(vw), tonumber(vh) }
        L.horizon = math.max(L.horizon, tonumber(s) - 1)
      end
    elseif kind == "B" then
      local t, s, r = rest:match("^(%d+) (%d+) (%S+)$")
      L.boot = { tonumber(t), tonumber(s), r }
    end
  end
end
read_more()
assert(L.boot, "no boot line in " .. SEG .. "/log")

local STEP = { on = false }        -- inside Game:step (set by its wrapper below)
local function in_step_flag() return STEP.on end
local report_n = 0
local function report(msg, always)
  report_n = report_n + 1
  if report_n <= 50 or always then
    print("[shadow] " .. msg)
    local f = io.open(SEG .. "/shadow_report", "a")
    if f then f:write(msg .. "\n"); f:close() end
  end
end

-- the run's generator as it stood when its driver loaded: same point here
pcall(love.math.setRandomState, L.boot[3])
pcall(love.window.setTitle, os.getenv("SHADOW_TITLE") or "red-recomp 1x")
pcall(function()                         -- which GPU (or none) draws this copy
  local name, version, vendor, device = love.graphics.getRendererInfo()
  print(("[shadow] renderer %s %s | %s | %s"):format(tostring(name), tostring(version), tostring(vendor), tostring(device)))
end)

-- this copy's own draws outside a step (its draw code runs every frame, the
-- run's once per 200 steps) come from a generator of their own, so they can
-- never move the stream its logic reads; the run's are in its G lines
do
  local private = love.math.newRandomGenerator(12345)
  for _, fname in ipairs({ "random", "randomNormal" }) do
    local o = love.math[fname]
    love.math[fname] = function(...)
      if in_step_flag() then return o(...) end
      return private[fname](private, ...)
    end
  end
end

-- A MOD ON THE COPY ALONE MAKES THE SAVE LOOK CHANGED: the load report lists
-- the mod set as differing from the one the save was written with, and the
-- report screen it pushes held the stack for 3 logic steps the run never took
-- (2026-10-04, Dramatic Shape). With SHADOW_MOD set, that screen is not shown.
if (os.getenv("SHADOW_MOD") or "") ~= "" then
  pcall(function()
    local Screens = require("src.ui.Screens")
    local o_push = Screens.push
    Screens.push = function(game, id, ...)
      if id == "QuarantineReport" then return true end
      return o_push(game, id, ...)
    end
  end)
end

-- SHADOW_TRACE=FROM-TO: every draw from the game's generator inside a step
-- in that range, with its value and call site, to $SHADOW_SEG/trace.<pid>.
-- Diff two of them to find what makes a copy part from the run.
do
  local a, b = (os.getenv("SHADOW_TRACE") or ""):match("^(%d+)-(%d+)$")
  if a then
    a, b = tonumber(a), tonumber(b)
    local tf = io.open(SEG .. "/trace." .. tostring(os.getenv("SHADOW_TRACE_TAG") or "x"), "w")
    local o = love.math.random
    love.math.random = function(...)
      local r = o(...)
      local n = Game.logicStep or 0
      if tf and STEP.on and n >= a and n <= b then
        tf:write(n, " ", tostring(r), " ", (debug.traceback("", 2) or ""):gsub("\n%s*", " | "):sub(1, 400), "\n")
        tf:flush()
      end
      return r
    end
  end
end

-- ---------------------------------------------------------------- the view
local view = nil                 -- {vw, vh} the run's logic saw, once known
local function set_window(w, h)
  if not (w and h) then return end
  local cw, ch = love.graphics.getDimensions()
  if cw == w and ch == h then return end
  local _, _, flags = love.window.getMode()
  flags = flags or {}
  flags.resizable = false
  pcall(love.window.updateMode or love.window.setMode, w, h, flags)
end
do
  local env_w, env_h = (os.getenv("SHADOW_WINDOW") or ""):match("^(%d+)x(%d+)$")
  if env_w then set_window(tonumber(env_w), tonumber(env_h)) end
  local v = L.views[1]
  if v and v[1] <= 1 then
    if os.getenv("SHADOW_OWN_VIEW") ~= "1" then set_window(v[2], v[3]) end
    view = { v[4], v[5] }
  end
  local okR, Renderer = pcall(require, "src.render.Renderer")
  if okR and type(Renderer) == "table" and Renderer.worldViewSize then
    local o_wvs = Renderer.worldViewSize
    local own = os.getenv("SHADOW_OWN_VIEW") == "1"   -- the control
    Renderer.worldViewSize = function(self, ...)
      if view and not own then return view[1], view[2] end
      return o_wvs(self, ...)
    end
  end
end

-- NO LIVE INPUT. The copy takes every button from the log, but a window on
-- the desktop also gets the mouse, the keyboard's own hotkeys (zoom, the
-- mod's camera keys) and touch; in a battle a hover or click can choose for
-- the copy (user, 2026-10-04: "part of the difference might be with how it
-- interprets mouse position on the screen when in battle it changes the
-- viewport"). None of them reach the game here.
for _, name in ipairs({ "mousepressed", "mousereleased", "mousemoved", "wheelmoved",
                        "touchpressed", "touchmoved", "touchreleased",
                        "keypressed", "keyreleased", "textinput",
                        "gamepadpressed", "gamepadreleased", "gamepadaxis",
                        "joystickpressed", "joystickreleased", "joystickaxis" }) do
  love[name] = function() end
end
-- and nothing that asks directly: the cursor is off the window, nothing held
if love.mouse then
  love.mouse.getPosition = function() return -1, -1 end
  love.mouse.getX = function() return -1 end
  love.mouse.getY = function() return -1 end
  love.mouse.isDown = function() return false end
end
if love.keyboard then love.keyboard.isDown = function() return false end end

-- ------------------------------------------------------------- the buttons
local held, alias_held = {}, {}
local function fill(t, from)
  for k in pairs(t) do t[k] = nil end
  for k in pairs(from) do t[k] = true end
end
Input.step = function(self)
  local n = Game.logicStep or 0
  local pressed = {}
  while L.inputs[L.in_i] and L.inputs[L.in_i][1] < n do L.in_i = L.in_i + 1 end
  local rec = L.inputs[L.in_i]
  if rec and rec[1] == n then
    pressed, held, alias_held = rec[2], rec[3], rec[4]
    L.in_i = L.in_i + 1
  end
  self.pressQueue = {}
  self.pressed = self.pressed or {}
  self.state = self.state or {}
  fill(self.pressed, pressed)
  fill(self.state, held)
  self.aliasHeld = next(alias_held) and alias_held or nil
  if self.sources then for k in pairs(self.sources) do self.sources[k] = nil end end
end

-- ----------------------------------------------------------- audio answers
local in_step, cur, cur_i, cur_step = false, nil, 1, -1
local function answers_for(n)
  while L.audio[L.au_i] and L.audio[L.au_i][1] + L.audio[L.au_i][2] - 1 < n do
    L.au_i = L.au_i + 1
  end
  local a = L.audio[L.au_i]
  if a and a[1] <= n then return a[3] end
  return nil
end
-- SHADOW_OWN_AUDIO=1 asks this copy's own speakers instead (the control
-- that shows why the answers are needed)
local OWN_AUDIO = os.getenv("SHADOW_OWN_AUDIO") == "1"
local function answer(tag, real_fn, ...)
  if OWN_AUDIO or not in_step then return real_fn(...) end
  local a = cur and cur[cur_i]
  if a and a[1] == tag then
    cur_i = cur_i + 1
    return a[2]
  end
  report(("step %d: logic asked audio %q the run did not (answer %d)"):format(cur_step, tag, cur_i))
  return real_fn(...)
end
pcall(function()
  local src = love.audio.newQueueableSource(8000, 16, 1, 1)
  local mt = getmetatable(src)
  local idx = mt and (type(mt.__index) == "table" and mt.__index or mt)
  local o_play, o_tell = idx.isPlaying, idx.tell
  idx.isPlaying = function(s, ...) return answer("p", o_play, s, ...) end
  if o_tell then idx.tell = function(s, ...) return answer("t", o_tell, s, ...) end end
  pcall(src.release, src)
end)
pcall(function()
  local Music = require("src.core.Music")
  local o = Music.oneShotPlaying
  Music.oneShotPlaying = function(...) return answer("o", o, ...) end
end)

-- ----------------------------------------------------------------- battles
local BOSS_CLASSES = { OPP_RIVAL1 = true, OPP_RIVAL2 = true, OPP_RIVAL3 = true,
  OPP_GIOVANNI = true, OPP_LORELEI = true, OPP_BRUNO = true, OPP_AGATHA = true,
  OPP_LANCE = true }
local skip = nil                 -- { battle = obj, what = "wild battle" } while one is skipped
-- ONE CARD FOR A STRETCH OF SKIPS. The run's grind op ends where a wild
-- battle starts and the battle's own ops follow, so a grind is grind, battle,
-- grind, battle: one card each made the text flip between TRAINING and WILD
-- BATTLE (user, 2026-10-03: "the wild-battle and grinding cards write over
-- eachother"). Now a card covers back-to-back skips: a grind anywhere in it
-- makes it TRAINING, each skipped battle counts on it, and it lingers
-- LINGER_STEPS of fast play after the last skip so the next one joins it; then
-- it stays up until CARD_MIN seconds have passed, the copy holding still. A
-- shown battle ends it at once.
local LINGER_STEPS = 180
local card = { active = false }
-- ...BUT A TRAINER IS ONE FIGHT, ONE CARD. Merging is for a grind's string
-- of wild battles; Silph's trainers, a few steps apart, came out as one card
-- reading "5 BATTLES" (user, 2026-10-04: "the trainer battle stuff should
-- just be 1 battle each"). A trainer battle starts a card of its own, and
-- its card does not linger for the next skip to join.
local function card_touch(kind, info)
  if not card.active or kind == "trainer" or card.trainer then
    local ow = Game.overworld
    card = { active = true, since = love.timer.getTime(), battles = 0, gap = 0,
             where = ow and ow.map and ow.map.id, trainer = kind == "trainer" }
    if not QUIET then print(("[shadow] card up at step %d"):format((Game.logicStep or 0) + 1)) end
  end
  card.gap = 0
  if kind == "op" then
    card.title = info == "grind" and "TRAINING" or tostring(info):upper()
  else
    card.battles = card.battles + 1
    card.title = card.title or (kind == "trainer" and "TRAINER BATTLE" or "WILD BATTLE")
    if kind == "trainer" and info then card.who = tostring(info):upper() end
  end
end
local skipped_n = 0
local function battle_shown(battle, npc)
  if SHOW == "all" then return true end
  if SHOW == "none" then return false end
  local event = battle.kind ~= "trainer" and npc ~= nil   -- a scripted wild fight
  if battle.kind ~= "trainer" then return event end
  if SHOW == "trainers" then return true end
  if BOSS_CLASSES[battle.oppClass] then return true end
  local okv, victories = pcall(require, "data.scripts.victories")
  local r = okv and victories[tostring(battle.oppClass) .. "#" .. tostring(battle.partyIndex or 1)]
  return r ~= nil and r.badge ~= nil
end
pcall(function()
  local OW = require("src.world.OverworldController")
  local o_push = OW.pushBattle
  OW.pushBattle = function(self, battle, npc, ...)
    if battle and not battle_shown(battle, npc) then
      local what = battle.kind == "trainer"
        and ("trainer battle" .. (battle.trainer and battle.trainer.name
             and (": " .. tostring(battle.trainer.name)) or ""))
        or "wild battle"
      skip = { battle = battle, what = what }
      skipped_n = skipped_n + 1
      card_touch(battle.kind == "trainer" and "trainer" or "wild",
                 battle.trainer and battle.trainer.name)
      if not QUIET then print(("[shadow] skipping a %s (%d so far)"):format(what, skipped_n)) end
    end
    if battle and battle_shown(battle, npc) then card.active = false end
    return o_push(self, battle, npc, ...)
  end
end)
-- skipping lasts while the battle (or the wipe before it) is on the stack;
-- what comes after it, an evolution say, is shown
-- the op the run was in at step n, if it is one to skip
local function skipped_op(n)
  while L.ops[L.op_i] and L.ops[L.op_i][2] and L.ops[L.op_i][2] <= n do L.op_i = L.op_i + 1 end
  local o = L.ops[L.op_i]
  if o and o[1] <= n and (not o[2] or n < o[2]) and SKIP_OPS[o[3]] then return o end
  return nil
end
local op_skip = nil              -- { op = record, battles = n, map = id } while one is skipped

local function skipping(game)
  if op_skip then return true end
  if not skip then return false end
  local st = game.stack and game.stack.states or {}
  for _, s_ in ipairs(st) do
    if s_ == skip.battle then skip.seen = true; return true end
  end
  if not skip.seen then return true end    -- still the wipe before it
  skip = nil
  return false
end

-- ---------------------------------------------------------------- snapshot
local function jstr(v)
  local t = type(v)
  if t == "nil" then return "null" end
  if t == "boolean" then return v and "true" or "false" end
  if t == "number" then return (v ~= v or v == math.huge or v == -math.huge) and "null" or string.format("%.14g", v) end
  if t == "string" then
    return '"' .. v:gsub('[%c"\\]', function(c)
      return string.format("\\u%04x", c:byte()) end) .. '"'
  end
  if t == "table" then
    if #v > 0 or next(v) == nil then
      local out = {}
      for i = 1, #v do out[i] = jstr(v[i]) end
      return "[" .. table.concat(out, ",") .. "]"
    end
    local out = {}
    for k, x in pairs(v) do
      if type(k) == "string" then out[#out + 1] = jstr(k) .. ":" .. jstr(x) end
    end
    return "{" .. table.concat(out, ",") .. "}"
  end
  return "null"
end
-- the run's wall time at the step this copy is on (the latest T at or before it)
local function run_time(n)
  while L.times[L.tm_i + 1] and L.times[L.tm_i + 1][1] <= n do L.tm_i = L.tm_i + 1 end
  local tm = L.times[L.tm_i]
  return tm and tm[1] <= n and tm[2] or nil
end

-- the battle on top of the stack as the HUD reads it, or nil
local function battle_view(game)
  local top = game.stack and game.stack:top()
  if not (top and (top.enemy or top.kind) and top.player) then return nil end
  local save = game.save or {}
  local function side(sd, mine)
    if not sd then return nil end
    local mon = sd.mon or {}
    local d = { species = mon.species, level = mon.level, hp = sd.shownHP or mon.hp,
                maxhp = sd.curStats and sd.curStats.hp,
                status = sd.shownStatus or mon.status }
    if mine then
      for i, pm in ipairs(save.party or {}) do if pm == mon then d.slot = i break end end
    end
    return d
  end
  local foe = side(top.enemy, false)
  -- THE GHOST IS A GHOST, as on the run's own observation (shim): without
  -- the SILPH SCOPE the Pokemon Tower's foe is drawn and named "GHOST" while
  -- the battle still holds the real species, and the HUD showed the real mon
  -- (user, 2026-10-06). The disguise is the name: it stays "GHOST" until the
  -- scope's reveal puts the real one back
  if foe and (top.ghost or (top.enemy and top.enemy.name == "GHOST")) then
    foe.species = "GHOST"
  end
  return { kind = top.kind, me = side(top.player, true), foe = foe,
           trainer = top.trainer and top.trainer.name or nil }
end

local function snapshot(game)
  -- nothing until this boot has a game loaded: the title has an empty party,
  -- and the HUD would show no team while each boot starts (2026-10-03)
  local ow0 = game.overworld
  if not (ow0 and ow0.map and ow0.map.id) then return end
  local save = game.save or {}
  local o = { step = Game.logicStep or 0, seg = SEG, t = os.time(), source = "copy",
              run_t = run_time(Game.logicStep or 0) }
  o.player_name = save.player and save.player.name
  o.party = {}
  for i, mon in ipairs(save.party or {}) do
    local m = { species = mon.species, nickname = mon.nickname, level = mon.level,
                hp = mon.hp, max_hp = mon.stats and mon.stats.hp,
                status = mon.status ~= nil and tostring(mon.status) or nil, moves = {} }
    for j, mv in ipairs(mon.moves or {}) do
      if type(mv) == "table" then
        local def = game.data and game.data.moves and game.data.moves[mv.id] or {}
        local ups = tonumber(mv.ppUps) or 0
        m.moves[j] = { id = mv.id, pp = mv.pp, type = def.type, power = def.power,
                       max_pp = def.pp and (def.pp + ups * math.floor(def.pp / 5)) or nil }
      end
    end
    local pdef = game.data and game.data.pokemon and game.data.pokemon[mon.species]
    m.types = pdef and pdef.types or nil
    o.party[i] = m
  end
  o.badges = {}
  for k in pairs(save.inventory or {}) do
    if type(k) == "string" and k:match("BADGE$") then o.badges[#o.badges + 1] = k end
  end
  table.sort(o.badges)
  local ow = game.overworld
  local p = ow and ow.player
  local mid = ow and ow.map and ow.map.id
  o.map = mid and { id = mid } or nil          -- no map yet (the title): leave it out
  o.player = p and { x = p.cellX, y = p.cellY, facing = p.facing } or nil
  local top = game.stack and game.stack:top()
  local bv = battle_view(game)
  if bv then
    o.mode, o.battle = "battle", bv
  elseif card.active and card.battle then
    -- A SKIPPED BATTLE STAYS ON THE HUD FOR AS LONG AS ITS CARD: the fight
    -- itself is over in a blink at skip speed, and the HUD showed no foe at
    -- all while the card said there was one (user, 2026-10-05: "sync up the
    -- enemy mon on the HUD with the card length"). The last look at it.
    o.mode, o.battle = "battle", card.battle
  else
    o.mode = (ow and top == ow) and "overworld" or "ui"
  end
  local tmp = SNAP .. ".tmp"
  local f = io.open(tmp, "w")
  if f then f:write(jstr(o)); f:close(); os.rename(tmp, SNAP) end
end

-- ------------------------------------------------------------- fog of war
-- THE RUN'S SEEN-GROUND OVERLAY, on the copy too (user, 2026-10-03: "the 1x
-- speed doesnt show the shadow overlay"). The shim draws it on the run's own
-- window from its SEEN table; the copy keeps its own: the ground seen when
-- this boot began (the recorder's copy of seen.json, else the run's current
-- one), then the same 10x9 window around the player painted as the copy
-- walks, so the screen reveals ground as the screen reaches it. Drawn the
-- shim's way: unseen cells shaded, a red edge along the seen boundary, the
-- connected maps out to three hops, the blue square of the view. Off with
-- SHADOW_OVERLAY=0.
local VIEW_L, VIEW_R, VIEW_U, VIEW_D = 4, 5, 4, 4
local SEEN = {}
local function seen_load(path)
  local f = path and io.open(path, "r")
  if not f then return false end
  local body = f:read("*a"); f:close()
  local chunk = body and load(body, "seen", "t", {})
  local ok, t = pcall(chunk or function() end)
  if not (ok and type(t) == "table") then return false end
  for mid, cells in pairs(t) do
    local st = SEEN[mid] or {}
    SEEN[mid] = st
    for _, k in ipairs(cells) do st[k] = true end
  end
  return true
end
if not seen_load(SEG .. "/seen.json") then seen_load(os.getenv("SHADOW_SEEN_FALLBACK")) end
local function seen_dims(game, map)
  local md = map and map.id and game.data and game.data.maps and game.data.maps[map.id]
  return ((md and md.width) or 0) * 2, ((md and md.height) or 0) * 2
end
local seen_last = nil
local function seen_paint(game)
  local ow = game.overworld
  local p, map = ow and ow.player, ow and ow.map
  if not (p and map and map.id and p.cellX and p.cellY) or ow.transitioning then return end
  local key = map.id .. "|" .. p.cellX .. "," .. p.cellY
  if key == seen_last then return end
  seen_last = key
  local W, H = seen_dims(game, map)
  local t = SEEN[map.id] or {}
  SEEN[map.id] = t
  local changed = false
  for y = math.max(0, p.cellY - VIEW_U), math.min(H - 1, p.cellY + VIEW_D) do
    for x = math.max(0, p.cellX - VIEW_L), math.min(W - 1, p.cellX + VIEW_R) do
      local k = x .. "," .. y
      if not t[k] then t[k] = true; changed = true end
    end
  end
  if changed and FOG_IMG and FOG_IMG[map.id] then FOG_IMG[map.id].dirty = true end
end

-- THE SAME GROUND FOR A 3D MOD: one texel per cell, white where seen, for the
-- diorama's terrain shader (tools/shadow/dramatic.py patches it to ask
-- Game.redFog for the map it is about to draw). Rebuilt only when cells
-- were added since the last frame asked.
-- how close the diorama's camera sits: the share of the run's view it frames
-- (drawing only; tools/shadow/dramatic.py)
Game.redZoom = tonumber(os.getenv("SHADOW_DS_ZOOM") or "0.7")
FOG_IMG = {}
Game.redFog = function(map_id)
  if os.getenv("SHADOW_FOG3D") == "0" then return nil end
  local W, H = seen_dims(Game, { id = map_id })
  if not (W and W > 0 and H > 0) then return nil end
  local e = FOG_IMG[map_id]
  if not e then
    local data = love.image.newImageData(W, H)
    e = { data = data, dirty = true }
    FOG_IMG[map_id] = e
  end
  if e.dirty then
    local t = SEEN[map_id] or {}
    e.data:mapPixel(function(x, y)
      local v = t[x .. "," .. y] and 1 or 0
      return v, v, v, 1
    end)
    if e.img then e.img:replacePixels(e.data)
    else
      e.img = love.graphics.newImage(e.data)
      e.img:setFilter("nearest", "nearest")
    end
    e.dirty = false
  end
  return e.img, W, H
end
local function draw_fog(game)
  local ow = game.overworld
  if not (ow and game.stack and game.stack:top() == ow) then return end
  local map, p = ow.map, ow.player
  local R, cam = game.renderer, ow.camera
  if not (map and map.id and p and p.cellX and R and R.fitScale and R.worldCanvas and cam and cam.x) then return end
  local W, H = seen_dims(game, map)
  if W <= 0 or H <= 0 then return end
  local okz, Zoom = pcall(require, "src.render.Zoom")
  local Sp = R:fitScale()
  local sp = (okz and Zoom and Zoom.scale) and Zoom.scale(Sp) or Sp
  local ww = love.graphics.getWidth()
  local pw, ph = love.graphics.getPixelDimensions()
  local dpi = (ww > 0) and (pw / ww) or 1
  local wvw, wvh = R.worldCanvas:getWidth(), R.worldCanvas:getHeight()
  local wox = math.floor((pw - wvw * sp) / 2) / dpi
  local woy = math.floor((ph - wvh * sp) / 2) / dpi
  local S = sp / dpi
  local c = 16 * S
  local function cell_xy(cx, cy) return wox + (cx * 16 - cam.x) * S, woy + (cy * 16 - cam.y) * S end
  local vx0, vy0 = math.floor(cam.x / 16) - 1, math.floor(cam.y / 16) - 1
  local vx1, vy1 = math.floor((cam.x + wvw) / 16) + 1, math.floor((cam.y + wvh) / 16) + 1
  local function paint(m, mW, mH, ox, oy)
    local x0, y0 = math.max(0, vx0 - ox), math.max(0, vy0 - oy)
    local x1, y1 = math.min(mW - 1, vx1 - ox), math.min(mH - 1, vy1 - oy)
    if x0 > x1 or y0 > y1 then return end
    love.graphics.setColor(0, 0, 0, 0.5)
    for cy = y0, y1 do
      for cx = x0, x1 do
        if not m[cx .. "," .. cy] then
          local X, Y = cell_xy(ox + cx, oy + cy)
          love.graphics.rectangle("fill", X, Y, c, c)
        end
      end
    end
    love.graphics.setColor(1, 0.15, 0.15, 0.95)
    love.graphics.setLineWidth(math.max(1, S))
    for cy = y0, y1 do
      for cx = x0, x1 do
        if m[cx .. "," .. cy] then
          local X, Y = cell_xy(ox + cx, oy + cy)
          if cy > 0 and not m[cx .. "," .. (cy - 1)] then love.graphics.line(X, Y, X + c, Y) end
          if cy < mH - 1 and not m[cx .. "," .. (cy + 1)] then love.graphics.line(X, Y + c, X + c, Y + c) end
          if cx > 0 and not m[(cx - 1) .. "," .. cy] then love.graphics.line(X, Y, X, Y + c) end
          if cx < mW - 1 and not m[(cx + 1) .. "," .. cy] then love.graphics.line(X + c, Y, X + c, Y + c) end
        end
      end
    end
  end
  paint(SEEN[map.id] or {}, W, H, 0, 0)
  local maps = game.data and game.data.maps
  if maps then
    local placed = { [map.id] = true }
    local queue = { { id = map.id, ox = 0, oy = 0, w = W, h = H, depth = 0 } }
    local qi = 1
    while queue[qi] do
      local cur = queue[qi]
      qi = qi + 1
      local md = maps[cur.id]
      if cur.depth < 3 then
        local conns = (md and md.connections) or {}
        local dirs = {}
        for d in pairs(conns) do dirs[#dirs + 1] = d end
        table.sort(dirs)
        for _, d in ipairs(dirs) do
          local cn = conns[d]
          local nd = cn and cn.map and maps[cn.map]
          if nd and not placed[cn.map] and nd.width and nd.height then
            placed[cn.map] = true
            local nW, nH, off = nd.width * 2, nd.height * 2, (cn.offset or 0) * 2
            local ox, oy
            if d == "north" then ox, oy = cur.ox + off, cur.oy - nH
            elseif d == "south" then ox, oy = cur.ox + off, cur.oy + cur.h
            elseif d == "west" then ox, oy = cur.ox - nW, cur.oy + off
            elseif d == "east" then ox, oy = cur.ox + cur.w, cur.oy + off end
            if ox then
              paint(SEEN[cn.map] or {}, nW, nH, ox, oy)
              queue[#queue + 1] = { id = cn.map, ox = ox, oy = oy, w = nW, h = nH, depth = cur.depth + 1 }
            end
          end
        end
      end
    end
  end
  local X, Y = cell_xy(p.cellX - VIEW_L, p.cellY - VIEW_U)
  love.graphics.setColor(0.3, 0.6, 1, 0.9)
  love.graphics.rectangle("line", X, Y, (VIEW_L + VIEW_R + 1) * c, (VIEW_U + VIEW_D + 1) * c)
end
local FOG = os.getenv("SHADOW_OVERLAY") ~= "0"

-- THE CARD over whatever is being skipped: the game keeps running underneath,
-- fast, dimmed, so the screen is a fast-forward and not a black hole, and a
-- Game Boy text box in the game's own font and frame says what it is (user,
-- 2026-10-03: "well have to have a cooler looking card showing"). The HUD
-- beside it keeps counting levels as they come.
local function pretty(id)
  return (tostring(id or ""):gsub("_", " "))
end
local function card_lines()
  local n = card.battles or 0
  local count = (card.title == "TRAINING" or n > 1) and (n == 1 and "1 BATTLE" or (n .. " BATTLES")) or ""
  return { card.title or "", card.who or pretty(card.where), count }
end
local function card_linger()
  return card.trainer and 0 or LINGER_STEPS
end
local function card_hold()
  return card.active and not (skip or op_skip) and card.gap >= card_linger()
    and love.timer.getTime() - card.since < CARD_MIN
end
pcall(function()
  local Font = require("src.render.Font")
  local o_draw = love.draw
  love.draw = function(...)
    if o_draw then o_draw(...) end
    -- screenshots, for checking a look: SHADOW_SHOT=step[,step...], each
    -- saved as shadow_shot_<step>.png in the identity's save folder
    if os.getenv("SHADOW_SHOT") and not shot_list then
      shot_list = {}
      for v in os.getenv("SHADOW_SHOT"):gmatch("%d+") do shot_list[#shot_list + 1] = tonumber(v) end
    end
    if shot_list and shot_list[1] and (Game.logicStep or 0) >= shot_list[1] then
      love.graphics.captureScreenshot(("shadow_shot_%d.png"):format(shot_list[1]))
      table.remove(shot_list, 1)
    end
    if FOG and not card.active and not booting and not catching_up then
      love.graphics.push("all")
      pcall(draw_fog, Game)
      love.graphics.pop()
    end
    if not card.active and not booting and not catching_up then return end
    local w, h = love.graphics.getDimensions()
    love.graphics.push("all")
    love.graphics.origin()
    -- the fast-forward, dimmed; a boot or a catch-up is not worth seeing at
    -- all (the title showed through the CONTINUING card, 2026-10-04)
    -- (and a skipped battle is not seen at all: it showed through, 2026-10-04)
    local top = Game.stack and Game.stack:top()
    local in_battle = skip ~= nil or (top and (top.enemy or top.kind)) and true or false
    love.graphics.setColor(0.04, 0.05, 0.06,
      (((booting or catching_up) and not card.active) or in_battle) and 1 or 0.62)
    love.graphics.rectangle("fill", 0, 0, w, h)
    -- a 20x10-tile box in Game Boy pixels, scaled whole to the window
    local k = math.max(1, math.floor(math.min(w / 176, h / 176)))
    local tw, th = 20, 10
    love.graphics.translate(math.floor((w - tw * 8 * k) / 2), math.floor((h - th * 8 * k) / 2))
    love.graphics.scale(k, k)
    love.graphics.setColor(1, 1, 1, 1)
    Font.drawBox(0, 0, tw, th)
    love.graphics.setColor(1, 1, 1, 1)
    local lines = (catching_up and { "CATCHING UP", "", "" })
      or (booting and not card.active and { "CONTINUING", "", "" }) or card_lines()
    for i, line in ipairs(lines) do
      line = tostring(line):sub(1, tw - 4)
      local x = math.floor((tw * 8 - Font.width(line)) / 2)
      Font.draw(line, x, 12 + (i - 1) * 16)
    end
    -- the fast-forward mark, blinking at the game's own blink rate
    if math.floor(love.timer.getTime() * 2) % 2 == 0 then
      local ff = "▶▶ FAST FORWARD"
      Font.draw(ff, math.floor((tw * 8 - Font.width(ff)) / 2), (th - 2) * 8 - 4)
    end
    love.graphics.pop()
  end
end)

-- ------------------------------------------------------------------- jumps
local okC, Checkpoint = pcall(require, "src.core.Checkpoint")
local okS, SaveSerializer = pcall(require, "src.core.SaveSerializer")
local function apply(game, ev)
  local kind, arg = ev[2], ev[3]
  if kind == "P" then
    -- the party list's remembered cursor, written by the run's harness
    -- without a button (replay_rec R.event)
    game.partyMenuSavedIndex = tonumber(arg) or game.partyMenuSavedIndex
  elseif kind == "G" then
    pcall(love.math.setRandomState, arg)
  elseif kind == "W" then
    pcall(game.writeSave, game)          -- lands in this copy's own identity
  elseif kind == "R" then
    local f = arg ~= "-" and io.open(SEG .. "/" .. arg, "rb")
    if not f then report(("step %d: restore %s has no blob"):format(ev[1], arg)); return end
    local blob = f:read("*a"); f:close()
    local ck = okS and SaveSerializer.decode(blob)
    local ok, code, msg = false, "no checkpoint module", ""
    if okC and ck then ok, code, msg = Checkpoint.restore(game, ck) end
    if not ok then report(("step %d: restore refused: %s %s"):format(ev[1], tostring(code), tostring(msg))) end
    -- the shim redraws a map whose tiles come from its flags (CINNABAR_GYM)
    local ow = game.overworld
    local mid = ow and ow.map and ow.map.id
    if mid == "CINNABAR_GYM" then
      local okms, MS = pcall(require, "src.script.MapScripts")
      local hooks = okms and MS and MS.get(mid)
      if hooks and hooks.onEnter then pcall(hooks.onEnter, game, ow, mid) end
    end
  end
end

local first_bad = nil
-- CAUGHT UP: the copy has played everything the log holds and waits for the
-- run. It must keep yielding frames, or LOVE's loop stops, the window stops
-- drawing and answering, and the desktop calls it not responding (2026-10-03,
-- once skipping let the copy catch up while the run held still for the
-- model). So it yields as usual and its logic holds still instead, the way the
-- run's does while the model thinks.
local HOLD = { on = false }
local o_step = Game.step
Game.step = function(self, dt, ...)
  if HOLD.on then return end
  local n = (Game.logicStep or 0) + 1
  -- the run's jumps draw from the game's generator as the run's did (a
  -- restore builds the map's NPCs, each drawing a wander timer), so they
  -- count as logic here, not as this copy's own drawing
  STEP.on = true
  while L.events[L.ev_i] and L.events[L.ev_i][1] <= n do
    if L.events[L.ev_i][1] == n then apply(self, L.events[L.ev_i]) end
    L.ev_i = L.ev_i + 1
  end
  STEP.on = false
  while L.views[L.vw_i] and L.views[L.vw_i][1] <= n do
    local v = L.views[L.vw_i]
    if os.getenv("SHADOW_OWN_VIEW") ~= "1" then set_window(v[2], v[3]) end
    view = { v[4], v[5] }
    L.vw_i = L.vw_i + 1
  end
  while L.checks[L.ck_i] and L.checks[L.ck_i][1] < n do L.ck_i = L.ck_i + 1 end
  local c = L.checks[L.ck_i]
  if c and c[1] == n then
    local ow = self.overworld
    local m = ow and ow.map and ow.map.id or "-"
    local p = ow and ow.player
    local x, y = tostring(p and p.cellX or "-"), tostring(p and p.cellY or "-")
    local ok_r = select(2, pcall(love.math.getRandomState)) == c[2]
    if ok_r and m == c[3] and x == c[4] and y == c[5] then
      if not QUIET and n % 6000 == 0 then print(("[shadow] step %d matches (%s %s,%s)"):format(n, m, x, y)) end
    elseif not first_bad then
      first_bad = n
      report(("step %d: FIRST MISMATCH run=%s %s,%s rng %s | copy=%s %s,%s rng %s"):format(
        n, c[3], c[4], c[5], ok_r and "same" or "differs", m, x, y, ok_r and "same" or "differs"), true)
    end
    L.ck_i = L.ck_i + 1
  end
  local o = skipped_op(n)
  if o and not (op_skip and op_skip.op == o) then
    local ow = self.overworld
    op_skip = { op = o, battles = 0, map = ow and ow.map and ow.map.id }
    card_touch("op", o[3])
    if not QUIET then print(("[shadow] skipping a %s at %s"):format(o[3], tostring(op_skip.map))) end
  elseif not o and op_skip then
    op_skip = nil
  end
  if card.active then
    if op_skip or skip then card.gap = 0 else card.gap = card.gap + 1 end
  end
  in_step, cur_step, cur, cur_i = true, n, answers_for(n), 1
  STEP.on = true
  local a, b, d = o_step(self, dt, ...)
  STEP.on = false
  -- A SKIP IS FOLLOWED STEP BY STEP, NOT FRAME BY FRAME. skipping() learns
  -- the battle is up by finding it on the stack, and asked once a frame, a
  -- window the compositor throttles (19 fps off the visible workspace) ran
  -- 1,200 steps a frame at 400x: a whole wild battle came and went between
  -- two looks, was never seen, and was taken for the wipe before it for
  -- good, the card standing until the run moved again (user, 2026-10-05)
  if skip then
    -- (and keep the latest look at it for the card's HUD, every few steps)
    if card.active and (not card.battle or n % 8 == 0) then
      local ok, bv = pcall(battle_view, self)
      if ok and bv then card.battle = bv end
    end
    pcall(skipping, self)
  end
  pcall(seen_paint, self)
  if cur and cur_i <= #cur and not OWN_AUDIO then
    report(("step %d: the run asked %d audio question(s) this copy did not"):format(n, #cur - cur_i + 1))
  end
  in_step = false
  return a, b, d
end

-- ------------------------------------------------------------------ pacing
local function busy_near(n)
  if next(held) then return true end
  local function near(s) return s and s >= n - TRAIL and s <= n + LOOKAHEAD end
  local i = L.in_i
  if L.inputs[i] and near(L.inputs[i][1]) then return true end
  if i > 1 and L.inputs[i - 1] and near(L.inputs[i - 1][1]) then return true end
  -- (audio answers alone are not "something happening": a box waiting on a
  -- sound with nobody pressing is a wait, and the elevator's uncapped wait
  -- held the copy at 1x for ~2.5 h of a stuck run, 2026-10-04)
  local e = L.events[L.ev_i]
  if e and near(e[1]) then return true end
  return false
end
local function next_busy(n)
  local best = math.huge
  if L.inputs[L.in_i] then best = math.min(best, L.inputs[L.in_i][1]) end
  if L.events[L.ev_i] then best = math.min(best, L.events[L.ev_i][1]) end
  return best
end
local function segment_done()
  -- a newer segment beside this one means the run's game was restarted
  local parent = SEG:match("^(.*)/[^/]+$")
  local me = SEG:match("([^/]+)$")
  local p = io.popen('ls "' .. parent .. '" 2>/dev/null')
  if not p then return false end
  local newer = false
  for name in p:lines() do if name > me then newer = true end end
  p:close()
  return newer
end

-- the sound fades out as the speed rises: whole at 2x, gone by 8x
local volume = 1
local function set_volume(speed)
  local v = math.max(0, math.min(1, (8 - speed) / 6))
  if math.abs(v - volume) > 0.02 then
    pcall(love.audio.setVolume, v)
    volume = v
  end
end

-- where a frame's time goes, for the fps line: Game:update, love.draw, the
-- copy's own extra steps
PROF = { upd = 0, draw = 0, ff = 0, frames = 0, drv = 0, gap = 0, last = nil }
pcall(function()
  local o_upd = Game.update
  Game.update = function(self, ...)
    local t0 = love.timer.getTime()
    if PROF.last then PROF.gap = PROF.gap + (t0 - PROF.last) end   -- frame to frame
    PROF.last = t0
    local a, b = o_upd(self, ...)
    PROF.upd = PROF.upd + love.timer.getTime() - t0
    return a, b
  end
  local o_draw = love.draw
  love.draw = function(...)
    local t0 = love.timer.getTime()
    if o_draw then o_draw(...) end
    PROF.draw = PROF.draw + love.timer.getTime() - t0
    PROF.frames = PROF.frames + 1
  end
end)

-- ONE LOGIC STEP, NOTHING ELSE. The fast-forward runs many steps per drawn
-- frame; through Game:update each also ran the per-frame extras, the render
-- pipelines' update among them, and a voxel mod pumping meshes there for a few
-- ms a call took the copy to ~10 fps and a crawl (2026-10-04). The main loop
-- still runs one whole Game:update per frame; the extra steps only step.
local FixedStep = require("src.core.FixedStep")
local function step_once(G)   -- (PROF.drv: the driver's own time per frame, see the loop)
  local before = Game.logicStep or 0
  for _ = 1, 4 do                        -- the accumulator can come up a hair short
    FixedStep.maxAccum = FixedStep.catchupLimit(1, 1 / 60)
    FixedStep:update(1 / 60, 1)
    if (Game.logicStep or 0) ~= before then return end
  end
end
local speed, carry, snap_n = PLAY, 0, 0
local startup = { done = false, since = nil, idle = 0 }   -- the mod's first mesh build, this boot
local STARTUP_MAX = tonumber(os.getenv("SHADOW_STARTUP_MAX") or "15") or 15
local frame_t = nil
booting = true                         -- until this boot has a map (global: the draw reads it)
local last_done_check = nil
return function(G)
  local last_read = 0
  local drv_t0 = love.timer.getTime()
  while true do
    local n = (Game.logicStep or 0) + 1
    if love.timer.getTime() - last_read > 0.5 then
      read_more(); last_read = love.timer.getTime()
    end
    -- never run past what the log has written: wait for the run, or stop
    -- when its game has gone (a later segment, or not following)
    while n > L.horizon do
      local now = love.timer.getTime()
      -- has the run's game restarted (a newer boot beside this one)? Its own
      -- clock: the log re-read below reset the shared one at the very moment
      -- it came due, so this never asked and the copy waited at the end of
      -- an old boot for hours (2026-10-03)
      local ended = false
      if FOLLOW and now - (last_done_check or 0) > 1 then
        last_done_check = now
        ended = segment_done()
      end
      if not FOLLOW or ended then
        read_more()
        if n > L.horizon then
          HOLD.on = false
          print(("[shadow] end of the log at step %d%s"):format(n - 1,
                first_bad and (", first mismatch at " .. first_bad) or ", every check matched"))
          return
        end
      else
        -- CAUGHT UP, AND THE RUN IS HOLDING STILL (the model thinking): no
        -- step comes to count the linger down, and a card done with its skip
        -- stood over the screen until the run moved again (user, 2026-10-04:
        -- "currently its just stuck on the same battle card"). Out of steps,
        -- the linger is over; the card still keeps its CARD_MIN
        -- (skipping() is what ends a skip whose battle has left the stack,
        -- and this wait never reaches the main body that asks it: a battle
        -- the run won just before a model call kept its card up for the
        -- whole call, about a minute; user, 2026-10-05)
        skipping(G)
        -- ...and a skipped op (a grind) the run has already moved past ends
        -- here too, not on a next step that waits on the model
        if op_skip and not skipped_op(n) then op_skip = nil end
        if card.active and (snap_n or 0) % 6 == 0 then pcall(snapshot, G) end
        snap_n = (snap_n or 0) + 1
        if card.active and not (skip or op_skip)
            and love.timer.getTime() - card.since >= CARD_MIN then
          card.active = false
          if not QUIET then print(("[shadow] card down at step %d after %.1f s (caught up)"):format(n - 1, love.timer.getTime() - card.since)) end
          pcall(snapshot, G)                   -- and the HUD drops its foe with it
        end
        HOLD.on = true                   -- this frame draws; no step runs
        G.driverSpeed = 1
        set_volume(1)
        coroutine.yield()
        if love.timer.getTime() - last_read > 0.25 then
          read_more(); last_read = love.timer.getTime()
        end
      end
    end
    HOLD.on = false
    -- a card done lingering: hold still until it has been up CARD_MIN, then drop it
    if card.active and not (skip or op_skip) and card.gap >= card_linger()
        and not card_hold() then
      card.active = false
      if not QUIET then print(("[shadow] card down at step %d after %.1f s"):format(n - 1, love.timer.getTime() - card.since)) end
      pcall(snapshot, G)                   -- and the HUD drops its foe with it
    end
    if card_hold() then
      -- (the HUD still hears from the copy while the card holds: its foe
      -- stays up for the card's whole length)
      snap_n = (snap_n or 0) + 1
      if snap_n % 6 == 0 then pcall(snapshot, G) end
      HOLD.on = true
      G.driverSpeed = 1
      coroutine.yield()
      HOLD.on = false
      goto continue
    end
    -- the speed this frame: PLAY near an event; otherwise rising toward
    -- IDLE_MAX at ACCEL, and capped so it can brake to PLAY by the next
    -- event (v^2 = 2*a*d) and by the end of what the log holds
    local target
    local loaded = G.overworld and G.overworld.map and G.overworld.map.id
    -- the boot: the CONTINUING card from the window's first frame (booting
    -- starts true) until the run's save has loaded a map, then the game
    -- (user, 2026-10-06: "start with the continuing card until the game is
    -- loaded, at which point it can show the game")
    booting = not loaded
    -- A 3D MOD BUILDS ITS MESHES AFTER THE MAP LOADS: the card stays up and
    -- the game holds still until the build queue has stood empty a few
    -- frames running (the queue only fills once the scene first draws), or
    -- STARTUP_MAX seconds; once per boot (user, 2026-10-04: "show the card
    -- for the whole startup sequence until everythings loaded for the mod")
    if loaded and not startup.done then
      local pend = Game.redMeshPending
      startup.since = startup.since or love.timer.getTime()
      if not pend or love.timer.getTime() - startup.since > STARTUP_MAX then
        startup.done = true
        Game.redCovered = nil
      else
        local ok, n_jobs = pcall(pend)
        startup.idle = (ok and n_jobs == 0) and (startup.idle + 1) or 0
        if startup.idle >= 10 then
          startup.done = true
          Game.redCovered = nil
          print(("[shadow] the mod's map was built in %.1f s"):format(love.timer.getTime() - startup.since))
          io.stdout:flush()
        else
          booting = true
          Game.redCovered = true           -- the mod may build with its covered slice
          HOLD.on = true
          G.driverSpeed = 1
          coroutine.yield()
          HOLD.on = false
          goto continue
        end
      end
    end
    do
      local rt = run_time(n)
      local lag = rt and (os.time() - rt) or 0
      if lag > MAX_LAG then catching_up = true elseif lag < CATCHUP_TO then catching_up = false end
    end
    -- asked EVERY frame: it is also what ends a skip once its battle has left
    -- the stack, and asked only down the branch below, a copy catching up
    -- never asked, the skip never ended, and one card stood over every battle
    -- that followed ("5 BATTLES" across Silph, 2026-10-04)
    local skipping_now = skipping(G)
    if catching_up then
      target = SKIP_SPEED
    elseif booting then
      -- THE BOOT ITSELF: title, CONTINUE, the save loading. Every attempt
      -- reboots the run's game, and playing that out each time read as the
      -- game starting over and over (2026-10-03); run it through under a card
      booting = true
      target = SKIP_SPEED
    elseif skipping_now or card.active then
      booting = false
      target = SKIP_SPEED              -- under the card: a skip, or the linger after one
    elseif busy_near(n) then
      booting = false
      target = PLAY
      -- plain walking goes quicker, and quicker still when far behind;
      -- text, menus and battles do not
      local ow = G.overworld
      if ow and G.stack and G.stack:top() == ow then
        target = (L.horizon - n > CATCHUP_AFTER) and math.max(WALK_SPEED, CATCHUP_SPEED) or WALK_SPEED
      end
    else
      local d_ev = math.max(0, next_busy(n) - LOOKAHEAD - n)
      local d_h = math.max(0, L.horizon - n)
      target = math.min(IDLE_MAX, math.max(PLAY, math.sqrt(2 * ACCEL * math.min(d_ev, d_h))))
    end
    if skip or op_skip or card.active or booting or catching_up then
      speed = target                   -- under the card: no ramp to watch
    elseif target <= WALK_SPEED then
      speed = target                   -- 1x or walking pace: no ramp to wait through
    elseif target > speed then
      speed = math.min(target, speed + ACCEL)
    else
      speed = math.max(target, speed - ACCEL)
    end
    set_volume(speed)
    -- this frame's steps: the main loop runs one after the yield, the rest here
    -- BY THE CLOCK, NOT BY THE FRAME: a step per drawn frame made 1x as slow
    -- as the window was drawn, and a window the compositor throttles (not on
    -- the visible workspace: 15 fps, 2026-10-04) played a third of real time.
    -- Steps owed = elapsed seconds x 60 x speed, capped so a stall cannot
    -- become a leap.
    local now_t = love.timer.getTime()
    local dt = math.min(0.25, math.max(0, now_t - (frame_t or now_t)))
    frame_t = now_t
    carry = carry + speed * dt * 60
    local steps = math.floor(carry)
    carry = carry - steps
    steps = math.min(steps, L.horizon - n + 1)
    if steps < 1 then
      -- this frame owes no step (a display faster than 60 Hz): draw, hold
      HOLD.on = true
      G.driverSpeed = 1
      coroutine.yield()
      HOLD.on = false
      goto continue
    end
    local t0 = love.timer.getTime()
    for _ = 2, steps do
      if love.timer.getTime() - t0 > FF_SLICE then break end
      -- a card whose linger has run out is dropped by the next frame, not
      -- 1,600 steps later at the end of a throttled frame's batch: the walk
      -- between two battles was raced through under the card
      if card.active and not (skip or op_skip) and card.gap >= card_linger() then break end
      step_once(G)
    end
    PROF.ff = PROF.ff + love.timer.getTime() - t0
    if love.timer.getTime() - (fps_at or 0) > 10 then        -- the frame rate, for judging a mod's cost
      fps_at = love.timer.getTime()
      local f = math.max(1, PROF.frames)
      print(("[shadow] fps %d at step %d (speed %.1f); ms per frame: update %.1f, draw %.1f, extra steps %.1f, driver %.1f, frame-to-frame %.1f"):format(
        love.timer.getFPS(), n, speed, PROF.upd / f * 1000, PROF.draw / f * 1000, PROF.ff / f * 1000,
        PROF.drv / f * 1000, PROF.gap / f * 1000))
      PROF.upd, PROF.draw, PROF.ff, PROF.frames, PROF.drv, PROF.gap = 0, 0, 0, 0, 0, 0
      io.stdout:flush()
    end
    snap_n = (snap_n or 0) + 1
    if (snap_n % 6 == 0 and ((not skip and not op_skip) or card.active))
        or (snap_n % 30 == 0 and op_skip and not skip) then
      pcall(snapshot, G)
    end
    G.driverSpeed = 1
    PROF.drv = PROF.drv + love.timer.getTime() - drv_t0
    coroutine.yield()
    drv_t0 = love.timer.getTime()
    ::continue::
  end
end

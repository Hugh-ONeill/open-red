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
    elseif kind == "R" or kind == "G" or kind == "W" then
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
      if not QUIET then print(("[shadow] skipping a %s (%d so far)"):format(what, skipped_n)) end
    end
    return o_push(self, battle, npc, ...)
  end
end)
-- skipping lasts while the battle (or the wipe before it) is on the stack;
-- what comes after it, an evolution say, is shown
local function skipping(game)
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
local function snapshot(game)
  local save = game.save or {}
  local o = { step = Game.logicStep or 0, seg = SEG, t = os.time(), source = "copy" }
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
  o.map = { id = ow and ow.map and ow.map.id }
  o.player = p and { x = p.cellX, y = p.cellY, facing = p.facing } or nil
  local top = game.stack and game.stack:top()
  if top and (top.enemy or top.kind) and top.player then
    o.mode = "battle"
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
    o.battle = { kind = top.kind, me = side(top.player, true), foe = side(top.enemy, false),
                 trainer = top.trainer and top.trainer.name or nil }
  else
    o.mode = (ow and top == ow) and "overworld" or "ui"
  end
  local tmp = SNAP .. ".tmp"
  local f = io.open(tmp, "w")
  if f then f:write(jstr(o)); f:close(); os.rename(tmp, SNAP) end
end

-- the card over a skipped battle, drawn on top of the game's own frame
local card_font, card_font_size
pcall(function()
  local o_draw = love.draw
  love.draw = function(...)
    if o_draw then o_draw(...) end
    if skip then
      local w, h = love.graphics.getDimensions()
      love.graphics.push("all")
      love.graphics.origin()
      love.graphics.setColor(0.07, 0.07, 0.08, 1)
      love.graphics.rectangle("fill", 0, 0, w, h)
      love.graphics.setColor(0.85, 0.85, 0.8, 1)
      local size = math.max(16, math.floor(h / 30))
      if not card_font or card_font_size ~= size then
        card_font, card_font_size = love.graphics.newFont(size), size
      end
      local font = card_font
      love.graphics.setFont(font)
      love.graphics.printf(skip.what .. " (skipped)", 0, h / 2 - font:getHeight(), w, "center")
      love.graphics.pop()
    end
  end
end)

-- ------------------------------------------------------------------- jumps
local okC, Checkpoint = pcall(require, "src.core.Checkpoint")
local okS, SaveSerializer = pcall(require, "src.core.SaveSerializer")
local function apply(game, ev)
  local kind, arg = ev[2], ev[3]
  if kind == "G" then
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
local o_step = Game.step
Game.step = function(self, dt, ...)
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
  in_step, cur_step, cur, cur_i = true, n, answers_for(n), 1
  STEP.on = true
  local a, b, d = o_step(self, dt, ...)
  STEP.on = false
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
  local a = L.audio[L.au_i]
  if a and a[1] <= n + LOOKAHEAD and a[1] + a[2] - 1 >= n - TRAIL then return true end
  local e = L.events[L.ev_i]
  if e and near(e[1]) then return true end
  return false
end
local function next_busy(n)
  local best = math.huge
  if L.inputs[L.in_i] then best = math.min(best, L.inputs[L.in_i][1]) end
  if L.audio[L.au_i] then best = math.min(best, L.audio[L.au_i][1]) end
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

local speed, carry, snap_n = PLAY, 0, 0
return function(G)
  local last_read = 0
  while true do
    local n = (Game.logicStep or 0) + 1
    if love.timer.getTime() - last_read > 0.5 then
      read_more(); last_read = love.timer.getTime()
    end
    -- never run past what the log has written: wait for the run, or stop
    -- when its game has gone (a later segment, or not following)
    while n > L.horizon do
      if not FOLLOW or segment_done() then
        read_more()
        if n > L.horizon then
          print(("[shadow] end of the log at step %d%s"):format(n - 1,
                first_bad and (", first mismatch at " .. first_bad) or ", every check matched"))
          return
        end
      else
        love.timer.sleep(0.25)
        read_more()
      end
    end
    -- the speed this frame: PLAY near an event; otherwise rising toward
    -- IDLE_MAX at ACCEL, and capped so it can brake to PLAY by the next
    -- event (v^2 = 2*a*d) and by the end of what the log holds
    local target
    if skipping(G) then
      target = SKIP_SPEED              -- a skipped battle: through it under the card
    elseif busy_near(n) then
      target = PLAY
    else
      local d_ev = math.max(0, next_busy(n) - LOOKAHEAD - n)
      local d_h = math.max(0, L.horizon - n)
      target = math.min(IDLE_MAX, math.max(PLAY, math.sqrt(2 * ACCEL * math.min(d_ev, d_h))))
    end
    if skip then
      speed = target                   -- under the card: no ramp to watch
    elseif target <= PLAY then
      speed = PLAY                     -- something is happening: show it now
    elseif target > speed then
      speed = math.min(target, speed + ACCEL)
    else
      speed = math.max(target, speed - ACCEL)
    end
    set_volume(speed)
    -- this frame's steps: the main loop runs one after the yield, the rest here
    carry = carry + speed
    local steps = math.floor(carry)
    carry = carry - steps
    steps = math.min(steps, L.horizon - n + 1)
    local t0 = love.timer.getTime()
    for _ = 2, steps do
      if love.timer.getTime() - t0 > FF_SLICE then break end
      G:update(1 / 60)
    end
    snap_n = (snap_n or 0) + 1
    if snap_n % 6 == 0 and not skip then pcall(snapshot, G) end
    G.driverSpeed = 1
    coroutine.yield()
  end
end

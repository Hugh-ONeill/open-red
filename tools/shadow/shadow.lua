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

local speed, carry = PLAY, 0
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
    if busy_near(n) then
      target = PLAY
    else
      local d_ev = math.max(0, next_busy(n) - LOOKAHEAD - n)
      local d_h = math.max(0, L.horizon - n)
      target = math.min(IDLE_MAX, math.max(PLAY, math.sqrt(2 * ACCEL * math.min(d_ev, d_h))))
    end
    if target <= PLAY then
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
    G.driverSpeed = 1
    coroutine.yield()
  end
end

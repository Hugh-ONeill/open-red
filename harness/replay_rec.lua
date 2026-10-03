-- REPLAY RECORDER: everything a second copy of the game needs to play this
-- run again, step for step, at watching speed (tools/shadow/).
--
-- The run plays at 200x and the stream wants 1x. Game logic is deterministic
-- given three things, so those are what this writes, keyed by the game's own
-- logic step (Game.logicStep, one per 1/60 s FixedStep):
--   * the buttons logic saw on each step (after Input:step: pressed, held,
--     aliased), written only when something is pressed or the held set moved
--   * the answers to the audio questions logic asked during a step (a source
--     still playing? how far into it? a one-shot jingle still pending?). A
--     text box or a battle cry waits on "sound stopped OR frame budget", and
--     at 200x the budget runs out long before the sound does, at 1x not; so
--     the copy is handed the run's answers instead of asking its own speakers
--   * jumps the driver makes between steps: a checkpoint restored (written
--     out whole), the random generator set, a save written by the harness
-- plus the generator's state at boot and every CHECK_EVERY steps, which the
-- copy compares to say where it stopped matching.
--
-- Viewer-only: nothing here is read by the planner or the model. Off with
-- RED_REPLAY_REC=0. One directory per boot under $RED_BRIDGE_DIR/replay/.
return function(BRIDGE)
  if os.getenv("RED_REPLAY_REC") == "0" or not BRIDGE then return nil end
  local okG, Game = pcall(require, "src.core.Game")
  local okI, Input = pcall(require, "src.core.Input")
  if not (okG and okI and type(Game) == "table" and type(Input) == "table"
          and type(Game.step) == "function" and type(Input.step) == "function") then
    return nil
  end
  local CHECK_EVERY = 1800        -- 30 s of game time: a sync check, and the
                                  -- copy's horizon while the run only idles
  local FLUSH_LINES = 512
  local seg = string.format("%s/replay/%d-%d", BRIDGE, os.time(),
                            math.floor((os.clock() * 1e6) % 1e6))
  os.execute('mkdir -p "' .. seg .. '" 2>/dev/null')
  local R = { dir = seg, buf = {}, n_ck = 0, in_step = false }

  local function rng()
    local ok, s = pcall(love.math.getRandomState)
    return ok and s or "?"
  end
  local function put(line)
    R.buf[#R.buf + 1] = line .. "\n"
    if #R.buf >= FLUSH_LINES and not R.closing then R.close() end
  end
  function R.flush()
    if #R.buf == 0 then return end
    local buf = R.buf
    R.buf = {}
    pcall(function()
      local f = io.open(seg .. "/log", "a")
      if f then f:write(table.concat(buf)); f:close() end
    end)
  end
  local function copy_file(from, to)
    local f = io.open(from, "rb")
    if not f then return false end
    local body = f:read("*a"); f:close()
    local g = io.open(to, "wb")
    if not g then return false end
    g:write(body); g:close()
    return true
  end

  -- what the game boots from: the save it will CONTINUE and the options
  -- file (which is also the slot registry). Copied now, before anything in
  -- this process can write either.
  pcall(function()
    local base = love.filesystem.getSaveDirectory()
    copy_file(base .. "/options.lua", seg .. "/options.lua")
    local game = os.getenv("POKEPORT_GAME") or "red"
    copy_file(base .. "/saves/" .. game .. "/slot1.lua", seg .. "/slot1.lua")
  end)
  put(string.format("B %d %d %s", os.time(), Game.logicStep or 0, rng()))

  -- the step being run, and the driver's jumps to apply before the next
  local function step_no() return Game.logicStep or 0 end
  local function next_step() return (Game.logicStep or 0) + 1 end
  local rng_dirty = false

  -- 1. buttons: what logic sees after Input:step
  local function keys(t)
    if type(t) ~= "table" then return "-" end
    local out = {}
    for k, v in pairs(t) do if v then out[#out + 1] = tostring(k) end end
    if #out == 0 then return "-" end
    table.sort(out)
    return table.concat(out, ",")
  end
  local last_held = "- -"
  local in_step_orig = Input.step
  Input.step = function(self, ...)
    local r = in_step_orig(self, ...)
    local p = keys(self.pressed)
    local h = keys(self.state) .. " " .. keys(self.aliasHeld)
    if p ~= "-" or h ~= last_held then
      put(string.format("I %d %s %s", step_no(), p, h))
      last_held = h
    end
    return r
  end

  -- 2. audio answers asked inside a step, run-length per identical step
  local ans = nil                      -- this step's answers, in order
  local run_start, run_len, run_seq = nil, 0, nil
  local function close_run()
    if run_seq then put(string.format("A %d %d %s", run_start, run_len, run_seq)) end
    run_start, run_len, run_seq = nil, 0, nil
  end
  local function note(tag, v)
    if not R.in_step then return end
    ans = ans or {}
    local s
    if type(v) == "boolean" then s = tag .. (v and "1" or "0")
    elseif type(v) == "number" then s = tag .. string.format("%.17g", v)
    else s = tag .. "n" end
    ans[#ans + 1] = s
  end
  pcall(function()
    local src = love.audio.newQueueableSource(8000, 16, 1, 1)
    local mt = getmetatable(src)
    local idx = mt and (type(mt.__index) == "table" and mt.__index or mt)
    if idx and idx.isPlaying then
      local o_play, o_tell = idx.isPlaying, idx.tell
      idx.isPlaying = function(s, ...)
        local v = o_play(s, ...)
        note("p", v)
        return v
      end
      if o_tell then
        idx.tell = function(s, ...)
          local v = o_tell(s, ...)
          note("t", v)
          return v
        end
      end
      R.audio = true
    end
    pcall(src.release, src)
  end)
  pcall(function()
    local Music = require("src.core.Music")
    local o = Music.oneShotPlaying
    if type(o) == "function" then
      Music.oneShotPlaying = function(...)
        local v = o(...)
        note("o", v)
        return v
      end
    end
  end)

  -- 3. the step itself: jumps first, then the check, then the step
  local o_step = Game.step
  Game.step = function(self, dt, ...)
    local n = next_step()
    if rng_dirty then
      put(string.format("G %d %s", n, rng()))
      rng_dirty = false
    end
    if n % CHECK_EVERY == 0 then
      local ow = self.overworld
      local m = ow and ow.map and ow.map.id or "-"
      local p = ow and ow.player
      put(string.format("H %d %s %s %s %s", n, rng(), m,
                        tostring(p and p.cellX or "-"), tostring(p and p.cellY or "-")))
    end
    R.in_step = true
    ans = nil
    local a, b, c = o_step(self, dt, ...)
    R.in_step = false
    local seq = ans and table.concat(ans, ",") or nil
    if seq and seq == run_seq and run_start + run_len == n then
      run_len = run_len + 1
    else
      close_run()
      if seq then run_start, run_len, run_seq = n, 1, seq end
    end
    return a, b, c
  end

  -- 4. the driver's jumps between steps
  local okC, Checkpoint = pcall(require, "src.core.Checkpoint")
  local okS, SaveSerializer = pcall(require, "src.core.SaveSerializer")
  if okC and okS and type(Checkpoint.restore) == "function" then
    local o_restore = Checkpoint.restore
    Checkpoint.restore = function(game, ck, ...)
      local ok, code, msg = o_restore(game, ck, ...)
      if ok and not R.in_step then
        R.n_ck = R.n_ck + 1
        local name = string.format("ck%04d.lua", R.n_ck)
        local eok, blob = pcall(SaveSerializer.encode, ck)
        if eok and blob then
          local f = io.open(seg .. "/" .. name, "wb")
          if f then f:write(blob); f:close() end
          put(string.format("R %d %s", next_step(), name))
        else
          put(string.format("R %d -", next_step()))
        end
        rng_dirty = true
      end
      return ok, code, msg
    end
  end
  for _, fname in ipairs({ "setRandomSeed", "setRandomState" }) do
    local o = love.math[fname]
    if type(o) == "function" then
      love.math[fname] = function(...)
        local r = o(...)
        if not R.in_step then rng_dirty = true end
        return r
      end
    end
  end
  if type(Game.writeSave) == "function" then
    local o_ws = Game.writeSave
    Game.writeSave = function(self, ...)
      if not R.in_step then put(string.format("W %d", next_step())) end
      return o_ws(self, ...)
    end
  end
  -- the map a restore lands on may redraw from its flags (the shim's
  -- CINNABAR_GYM onEnter after a restore): the copy does the same itself
  -- written out at every observation: a run of identical audio answers
  -- still growing is split there, so the copy never reads past the file
  -- (every flush closes the open run first: the file is then complete up to
  -- its newest line, and the copy may play everything up to it)
  R.close = function()
    R.closing = true
    close_run()
    R.closing = false
    R.flush()
  end
  return R
end

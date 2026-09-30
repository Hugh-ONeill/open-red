-- Writes planner/public_names.json: {old map-data name: published name} for
-- every object and sign harness/public_names.lua renames, so the planner can
-- carry a ledger written under the old names over to the new ones.
-- Run from anywhere:  lua tools/public_names_table.lua [maps.lua] [out.json]
local here = (debug.getinfo(1, "S").source:gsub("^@", "")):match("^(.*)/tools/") or "."
local maps = arg[1] or ((os.getenv("HOME") or ".")
  .. "/Developer/gen1recomp/data/generated/maps.lua")
local out = arg[2] or (here .. "/planner/public_names.json")
local P = dofile(here .. "/harness/public_names.lua")
local M = dofile(maps)
local map, clash = {}, {}
local function put(old, new)
  if not old or old == "" or old == new then return end
  if map[old] and map[old] ~= new then clash[old] = true end
  map[old] = new
end
local ids = {}
for id in pairs(M) do ids[#ids + 1] = id end
table.sort(ids)
for _, id in ipairs(ids) do
  local m = M[id]
  for _, od in ipairs(m.objects or {}) do
    put(od.name, P.object(id, od, od.x, od.y))
  end
  for _, sg in ipairs(m.signs or {}) do
    put(sg.name or sg.text, P.sign(id, sg))
  end
end
for old in pairs(clash) do
  io.stderr:write("ambiguous, left out: " .. old .. "\n")
  map[old] = nil
end
local keys = {}
for k in pairs(map) do keys[#keys + 1] = k end
table.sort(keys)
local f = assert(io.open(out, "w"))
f:write("{\n")
for i, k in ipairs(keys) do
  f:write(('  "%s": "%s"%s\n'):format(k, map[k], i < #keys and "," or ""))
end
f:write("}\n")
f:close()
print(("%d names -> %s"):format(#keys, out))

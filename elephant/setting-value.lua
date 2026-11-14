local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local function read(path)
    local handle = io.open(path, "r")
    if not handle then return {} end
    local raw = handle:read("*a")
    handle:close()
    local valid, value = pcall(jsonDecode, raw)
    return valid and type(value) == "table" and value or {}
end

return function(script, key)
    local schema = read(paths.code("quickshell/desktop-bar/login-settings.json"))[script:match("[^/]+$")]
    if not schema or schema.defaults[key] == nil then return nil end
    local data = read(paths.config .. "/" .. schema.path)
    if script:match("bar%-settings.py$") and data.layout == "split" then data.layout = "centered" end
    local value = data[key]
    local selected = schema.defaults[key]
    for _, option in ipairs(schema.options[key]) do
        if type(option) == type(value) and option == value then selected = value end
    end
    if key == "workspaceAlwaysShow" then
        local count = data.workspaceCount
        if type(count) ~= "number" or count % 1 ~= 0 or count < 5 or count > 10 then count = 10 end
        if selected > count then selected = math.min(5, count) end
    end
    return tostring(selected)
end

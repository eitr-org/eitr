-- One resolver for normal and Focus bindings. Missing or broken preferences use defaults.
return function(paths)
    local overrides = {}
    local loader = loadfile(paths.config .. "/hypr/keybinds.lua")
    if loader then
        local valid, saved = pcall(loader)
        if valid and type(saved) == "table" then overrides = saved end
    end
    local function normalize(key)
        local modifiers, name = {}, nil
        for token in key:gmatch("[^+]+") do
            local part = token:match("^%s*(.-)%s*$"):upper()
            if part == "SUPER" or part == "CTRL" or part == "ALT" or part == "SHIFT" then
                modifiers[part] = true
            elseif name or not part:match("^[%w_]+$") then return nil
            else name = part end
        end
        if not name then return nil end
        local parts = {}
        for _, modifier in ipairs({"SUPER", "CTRL", "ALT", "SHIFT"}) do
            if modifiers[modifier] then parts[#parts + 1] = modifier end
        end
        parts[#parts + 1] = name
        return table.concat(parts, " + ")
    end
    local protected = {["SUPER + M"] = true, D = true, ["SUPER + D"] = true, ["SUPER + SHIFT + D"] = true}
    local function resolve(key)
        if key:find("mouse", 1, true) or key:find("switch:", 1, true) then return key end
        local default = normalize(key)
        -- Keep the lock and dictation release available, including hand-edited files.
        if protected[default] then return key end
        local value = overrides[default]
        if value == false then return nil end
        if type(value) == "string" and value:match("^[%w_ +]+$") then
            local target = normalize(value)
            if target and not protected[target] then return value end
        end
        return key
    end
    return {resolve = resolve, bind = function(key, ...)
        local effective = resolve(key)
        if effective then hl.bind(effective, ...) end
    end}
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local search = dofile(paths.code("elephant/search-index-entries.lua"))

local function copy(value)
    if type(value) ~= "table" then return value end
    local result = {}
    for key, item in pairs(value) do result[key] = copy(item) end
    return result
end

-- load() returns browse rows and optional descendant groups {parent, entries}.
-- Descendant actions must bind their context explicitly, never lastMenuValue.
-- Empty queries refresh the snapshot; typing only reads it. Elephant does the
-- matching, just as it does for scoped-menu's prepared index rows.
return function(name, load, context)
    local cached
    return function(query)
        local current = (context and context() or "") .. "\n" .. dofile(paths.code("elephant/i18n.lua")).language()
        -- Elephant creates a fresh Lua VM for every query. Its menu state is a
        -- list of strings shared across those VMs, not a Lua closure cache.
        if not cached and type(state) == "function" then
            local saved = state()
            if saved[1] == "eitr-live-menu-v1" then
                local valid, snapshot = pcall(jsonDecode, saved[2] or "")
                if valid and type(snapshot) == "table" then cached = snapshot end
            end
        end
        if not query or query == "" then
            local entries, descendants = load()
            cached = {entries = entries or {}, descendants = descendants or {}, context = current}
            if type(setState) == "function" then
                setState({"eitr-live-menu-v1", jsonEncode(cached)})
            end
        end
        if not cached or cached.context ~= current then return {} end
        local entries = {}
        for _, entry in ipairs(cached.entries) do table.insert(entries, copy(entry)) end
        if query and query ~= "" then
            for _, group in ipairs(cached.descendants) do
                for _, original in ipairs(group.entries) do
                    local entry = copy(original)
                    entry.Keywords = entry.Keywords or {}
                    if entry.Subtext then table.insert(entry.Keywords, entry.Subtext) end
                    table.insert(entry.Keywords, group.parent)
                    entry.Subtext = group.parent
                    table.insert(entries, entry)
                end
            end
            for _, entry in ipairs(search(name)) do table.insert(entries, entry) end
        end
        if query and query ~= "" then
            return dofile(paths.code("elephant/policies.lua")).filter(entries, name)
        end
        return entries
    end
end

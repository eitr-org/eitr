local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- GetEntries for a menu whose rows live in elephant/menu-rows/<name>.json. With an
-- empty query it lists its own rows in their fixed order; while typing it also
-- offers every row of the menus below it (Main: every menu), so search works
-- inside submenus. jsonDecode exists only once Elephant queries the menu, so the
-- rows are read then, not when the file loads.
local search = dofile(paths.code("elephant/search-index-entries.lua"))
local row_entry = dofile(paths.code("elephant/row-entry.lua"))
local i18n = dofile(paths.code("elephant/i18n.lua"))

return function(name, configure)
    local source = paths.code("elephant/menu-rows/" .. name .. ".json")

    local function own_entries()
        local handle = io.open(source, "r")
        if not handle then return {} end
        local raw = handle:read("*a")
        handle:close()
        local ok, rows = pcall(jsonDecode, raw)
        local entries = {}
        local battery = (name == "system-devices" or name == "battery-limit") and dofile(paths.code("elephant/battery-state.lua"))() or {}
        for _, row in ipairs(ok and rows or {}) do
            if (row.submenu ~= "battery-limit" and name ~= "battery-limit") or battery.available then
                local entry = row_entry(row)
                entry.SubMenu = row.submenu
                entry.Actions = row.actions
                table.insert(entries, entry)
            end
        end
        if configure then entries = configure(entries) end
        -- Assistant menus keep New before the other translated, sorted actions.
        local new_entry
        for _, entry in ipairs(entries) do
            if entry.Text == "New" and name:match("^ai%-") then new_entry = entry end
        end
        entries = i18n.entries(entries, name == "main")
        if new_entry then
            for index, entry in ipairs(entries) do
                if entry == new_entry then
                    table.remove(entries, index)
                    local position = 1
                    while entries[position] and entries[position].SubMenu do position = position + 1 end
                    table.insert(entries, position, new_entry)
                    break
                end
            end
        end
        return entries
    end

    return function(query)
        local entries = own_entries()
        if query and query ~= "" then
            for _, entry in ipairs(search(name)) do table.insert(entries, entry) end
        end
        return entries
    end
end

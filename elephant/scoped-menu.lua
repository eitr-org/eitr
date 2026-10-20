local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- GetEntries for a menu whose rows live in elephant/menu-rows/<name>.json. With an
-- empty query it lists its own rows in their fixed order; while typing it also
-- offers every row of the menus below it (Main: every menu), so search works
-- inside submenus. jsonDecode exists only once Elephant queries the menu, so the
-- rows are read then, not when the file loads.
local search = dofile(paths.code("elephant/search-index-entries.lua"))
local i18n = dofile(paths.code("elephant/i18n.lua"))

return function(name)
    local source = paths.code("elephant/menu-rows/" .. name .. ".json")

    local function own_entries()
        local handle = io.open(source, "r")
        if not handle then return {} end
        local raw = handle:read("*a")
        handle:close()
        local ok, rows = pcall(jsonDecode, raw)
        local entries = {}
        for _, row in ipairs(ok and rows or {}) do
            -- A ">" subtext marks a row that opens a submenu: the layout draws the
            -- marker on the right, leaving the subtitle line for descriptions.
            local submenu = row.subtext == ">"
            table.insert(entries, {Text = row.text, Subtext = not submenu and row.subtext or nil,
                State = submenu and {"submenu"} or nil, Keywords = row.keywords,
                Icon = row.icon, SubMenu = row.submenu, Actions = row.actions})
        end
        entries = i18n.entries(entries, name == "main")
        for _, entry in ipairs(entries) do
            if entry.SubMenu == nil and entry.Text == i18n.tr("Language") then
                entry.Text = i18n.tr("Language · {language}", {language = i18n.language()})
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

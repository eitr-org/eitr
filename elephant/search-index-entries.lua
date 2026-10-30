local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- Rows from the prepared search index. scope "main" (or nil) offers every menu's
-- rows; another menu name offers only the rows of the menus below it. The menu's
-- own rows are left out: its definition already lists them.
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/menus/search-index.py")
local row_entry = dofile(paths.code("elephant/row-entry.lua"))
local runtime = os.getenv("XDG_RUNTIME_DIR")

local function in_scope(row, scope)
    if row.provider == "menus:" .. scope then return false end
    if scope == "main" then return true end
    for _, menu in ipairs(row.menus or {}) do
        if menu == scope then return true end
    end
    return false
end

return function(scope)
    scope = scope or "main"
    if not runtime then return {} end
    local handle = io.open(runtime .. "/eitr-search/index.json", "r")
    if not handle then return {} end
    local raw = handle:read("*a")
    handle:close()
    local ok, index = pcall(jsonDecode, raw)
    if not ok or not index.rows then return {} end
    local entries = {}
    local battery = dofile(paths.code("elephant/battery-state.lua"))()
    for _, row in ipairs(index.rows) do
        if in_scope(row, scope) and (battery.available or (row.submenu ~= "battery-limit" and row.provider ~= "menus:battery-limit")) then
            local entry = row_entry(row)
            entry.Value = row.key
            entry.Provider = row.provider
            if row.submenu then
                -- Walker opens it like any submenu row, so Shift+Backspace leads to its parent.
                entry.SubMenu = row.submenu
            else
                local actions = {}
                for _, action in ipairs(row.actions or {}) do
                    if row.provider ~= "menus:apps" or action == "open" then
                        local binding = row.provider == "menus:apps" and "app_launch" or action
                        actions[binding] = "python3 " .. quote(helper) .. " activate " .. quote(row.key) .. " " .. quote(action)
                    end
                end
                entry.Actions = actions
            end
            if dofile(paths.code("elephant/policies.lua")).row(entry, row.provider:gsub("^menus:", "")) then
                table.insert(entries, entry)
            end
        end
    end
    return entries
end

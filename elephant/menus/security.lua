local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/security.json. Typing also searches the menus below this one.
Name = "security"
NamePretty = i18n.tr("Security")
Parent = "system"
Icon = "󰒃"
FixedOrder = true
local shellQuote = dofile(paths.code("elephant/shell-quote.lua"))
local security_entries = dofile(paths.code("elephant/scoped-menu.lua"))("security")
function GetEntries(query)
    local entries = security_entries(query)
    local command = "python3 " .. shellQuote(paths.code("walker/scripts/actions/system/users.py")) .. " --entries"
    local handle = io.popen(command)
    if handle then
        local raw = handle:read("*a")
        handle:close()
        local ok, users = pcall(jsonDecode, raw)
        if ok and type(users) == "table" then
            for _, user in ipairs(users) do table.insert(entries, user) end
        end
    end
    return i18n.entries(entries, false)
end

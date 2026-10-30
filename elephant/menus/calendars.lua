local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/tools/calendars.py")
local own_rows = dofile(paths.code("elephant/scoped-menu.lua"))("calendars")
Name = "calendars"
NamePretty = i18n.tr("Calendar Sources")
Parent = "tools"
Icon = "󰃭"
FixedOrder = true

-- Add Calendar… comes from menu-rows/calendars.json; each added calendar follows,
-- sorted by name. The helper prints names and hosts, never the secret addresses.
function GetEntries()
    local entries = own_rows("")
    local handle = io.popen("python3 " .. quote(helper) .. " rows")
    if handle then
        local output = handle:read("*a"); handle:close()
        local ok, calendars = pcall(jsonDecode, output)
        for _, calendar in ipairs(ok and calendars or {}) do
            table.insert(entries, {Text = calendar.name, Icon = "󰃭", Value = calendar.id,
                Subtext = i18n.tr("Read-only from {host} · Enter refreshes, Delete removes", {host = calendar.host}),
                Actions = {open = "python3 " .. quote(helper) .. " sync",
                           calendar_delete = "python3 " .. quote(helper) .. " remove " .. quote(calendar.id)}})
        end
    end
    return entries
end

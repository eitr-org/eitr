local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/install/webapps.py")
local software = paths.code("walker/scripts/actions/install/software.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")
Name = "webapps"
NamePretty = i18n.tr("Web Apps")
Parent = "install"
Icon = "󰘔"
FixedOrder = true

function GetEntries()
    local entries = {{
        Text = "Create Web App",
        Subtext = "Name a site and its address",
        Icon = "󰐕",
        Actions = {open = "kitty --class eitr-software -e python3 " .. quote(presenter) .. " python3 " .. quote(helper) .. " create"},
    }}
    local handle = io.popen("python3 " .. quote(helper) .. " list")
    if not handle then return entries end
    local output = handle:read("*a"); handle:close()
    local apps = {}
    for _, app in ipairs(jsonDecode(output) or {}) do
        table.insert(apps, {Text = app.name, Subtext = app.url, Value = app.path, Icon = app.icon,
            Actions = {open = "python3 " .. quote(helper) .. " launch " .. quote(app.id),
                app_uninstall = "python3 " .. quote(software) .. " uninstall " .. quote(app.path)}})
    end
    table.sort(apps, function(a, b) return a.Text:lower() < b.Text:lower() end)
    for _, app in ipairs(apps) do table.insert(entries, app) end
    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

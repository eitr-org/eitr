local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "workspace-always-show"
NamePretty = i18n.tr("Always show")
Parent = "workspaces"
Icon = "󰍹"
FixedOrder = true
function GetEntries()
    local options = {}
    local maximum = 10
    local quote = dofile(paths.code("elephant/shell-quote.lua"))
    local reader = io.popen("python3 " .. quote(paths.code("quickshell/desktop-bar/scripts/desktop-style.py")) .. " get workspaceCount")
    if reader then maximum = tonumber(reader:read("*l")) or 10; reader:close() end
    for number = 2, maximum do
        table.insert(options, {tostring(number), tostring(number), Icon, i18n.mark("Choose workspace count")})
    end
    return i18n.entries(choices(paths.code("quickshell/desktop-bar/scripts/desktop-style.py"), "workspaceAlwaysShow", options), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries, dofile(paths.code("elephant/workspace-context.lua")))

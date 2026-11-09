local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "workspace-count"
NamePretty = i18n.tr("Number of workspaces")
Parent = "workspaces"
Icon = "󰍹"
FixedOrder = true
function GetEntries()
    local options = {}
    local maximum = 10
    for number = 5, maximum do
        table.insert(options, {tostring(number), tostring(number), Icon, i18n.mark("Choose workspace count")})
    end
    return i18n.entries(choices(paths.code("quickshell/desktop-bar/scripts/desktop-style.py"), "workspaceCount", options), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries, dofile(paths.code("elephant/workspace-context.lua")))

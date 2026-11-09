local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local catalog = dofile(paths.code("elephant/choice-lists.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "workspace-monitors"
NamePretty = i18n.tr("Monitors")
Parent = "workspaces"
Icon = "󰍹"
FixedOrder = true
function GetEntries()
    local options = {}
    for _, choice in ipairs(catalog.workspace_modes) do
        table.insert(options, {choice.label, choice.id, Icon, choice.description})
    end
    return i18n.entries(choices(paths.code("quickshell/desktop-bar/scripts/desktop-style.py"), "workspaceMode", options), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries, dofile(paths.code("elephant/workspace-context.lua")))

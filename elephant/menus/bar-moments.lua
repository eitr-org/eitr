local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-moments"
NamePretty = i18n.tr("Bar moments")
Parent = "bar"
Icon = "󰍡"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("moments", {
        {i18n.mark("Off"), "false", "󰍡", i18n.mark("Use separate volume and brightness popups")},
        {i18n.mark("On"), "true", "󰍡", i18n.mark("Show brief notifications, levels and song changes in the bar.")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

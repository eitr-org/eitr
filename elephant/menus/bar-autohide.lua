local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-autohide"
NamePretty = i18n.tr("Auto-hide")
Parent = "bar"
Icon = "󰍜"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("autohide", {
        {i18n.mark("Always visible"), "no", "󰍜", i18n.mark("Keep the bar on screen")},
        {i18n.mark("Auto-hide"), "yes", "󰍜", i18n.mark("Reveal the bar at the screen edge")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

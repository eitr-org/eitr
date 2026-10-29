local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-dock"
NamePretty = i18n.tr("Dock")
Parent = "bar"
Icon = "󰍜"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("dock", {
        {i18n.mark("Disabled"), "no", "󰍜", i18n.mark("Hide the application dock")},
        {i18n.mark("Dock"), "yes", "󰍜", i18n.mark("Reveal open apps at the opposite edge")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

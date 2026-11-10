local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-glow"
NamePretty = i18n.tr("Glow")
Parent = "bar"
Icon = "󰍜"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("glow", {
        {i18n.mark("Disabled"), "no", "󰍜", i18n.mark("Disabled")},
        {i18n.mark("Glow"), "yes", "󰍜", i18n.mark("A soft glow in the theme colour around the bar.")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

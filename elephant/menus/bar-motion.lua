local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-motion"
NamePretty = i18n.tr("Reduce motion")
Parent = "bar"
Icon = "󰍜"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("reduceMotion", {
        {i18n.mark("Full motion"), "no", "󰍜", i18n.mark("Animate panels and bar controls")},
        {i18n.mark("Reduce motion"), "yes", "󰍜", i18n.mark("Show panels and bar controls instantly")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

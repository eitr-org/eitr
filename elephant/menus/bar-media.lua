local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-media"
NamePretty = i18n.tr("Media style")
Parent = "bar"
Icon = "󰍜"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("mediaStyle", {
        {i18n.mark("Bars"), "bars", "󰍜", i18n.mark("Seven audio spectrum bars")},
        {i18n.mark("Line"), "line", "󰍜", i18n.mark("A simple audio spectrum wave")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

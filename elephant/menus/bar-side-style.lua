local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-side-style"
NamePretty = i18n.tr("Side style")
Parent = "bar"
Icon = "󰓩"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("sideStyle", {
        {i18n.mark("Slopes"), "slopes", "󰓩", i18n.mark("Tabs and Centered meet the screen edge with 45° slopes")},
        {i18n.mark("Straight"), "straight", "󰓩", i18n.mark("Tabs and Centered meet the screen edge with straight sides")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

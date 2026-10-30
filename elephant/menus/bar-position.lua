local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-position"
NamePretty = i18n.tr("Position")
Parent = "bar"
Icon = "󰆾"
FixedOrder = true

local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("edge", {
        {"Top", "top", "󰁝", i18n.mark("Place the bar at the top")},
        {"Bottom", "bottom", "󰁅", i18n.mark("Place the bar at the bottom")},
        {"Left", "left", "󰁍", i18n.mark("Place the bar on the left")},
        {"Right", "right", "󰁔", i18n.mark("Place the bar on the right")},
    })
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

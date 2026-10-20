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
        {"Top", "top", "󰁝"},
        {"Bottom", "bottom", "󰁅"},
        {"Left", "left", "󰁍"},
        {"Right", "right", "󰁔"},
    })
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

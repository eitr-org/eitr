local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-layout"
NamePretty = i18n.tr("Layout")
Parent = "bar"
Icon = "󰕰"
FixedOrder = true

local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("layout", {
        {"One Bar", "unified", "󰍜"},
        {"Centered Bar", "centered", "󰕰"},
        {i18n.mark("Tabs"), "notch", "󰍜"},
        {i18n.mark("Islands"), "islands", "󰍜"},
    })
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

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
        {"Full", "unified", "󰍜", i18n.mark("Show the full desktop bar"), {"Full"}},
        {"Centered", "centered", "󰕰", i18n.mark("Show the clock and expand on hover"), {"Centered"}},
        {i18n.mark("Tabs"), "notch", "󰍜", i18n.mark("Show three compact edge tabs")},
        {i18n.mark("Islands"), "islands", "󰍜", i18n.mark("Show separate floating pills")},
    })
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

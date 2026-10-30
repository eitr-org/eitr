local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-clock"
NamePretty = i18n.tr("Clock")
Parent = "bar"
Icon = "󰥔"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("clock", {
        {i18n.mark("12-hour"), "12h", "󰥔", i18n.mark("Time with AM or PM, like 09:30 PM")},
        {i18n.mark("24-hour"), "24h", "󰥔", i18n.mark("Time from 00:00 to 23:59, like 21:30")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

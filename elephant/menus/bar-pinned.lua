local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-pinned"
NamePretty = i18n.tr("Keep expanded")
Parent = "bar"
Icon = "󰐃"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("pinned", {
        {i18n.mark("Off"), "no", Icon, i18n.mark("The centered bar expands while hovered")},
        {i18n.mark("On"), "yes", Icon, i18n.mark("Keep the centered bar expanded")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

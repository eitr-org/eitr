local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-screens"
NamePretty = i18n.tr("Displays")
Parent = "bar"
Icon = "\243\176\141\185"
FixedOrder = true

local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("screens", {
        {"All Displays", "all", "\243\176\141\186", i18n.mark("Show the bar on every display")},
        {"Main Display Only", "main", "\243\176\141\185", i18n.mark("Show the bar on the main display")},
    })
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

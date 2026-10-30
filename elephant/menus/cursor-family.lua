local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "cursor-family"
NamePretty = i18n.tr("Cursor Family")
Parent = "cursor"
Icon = "󰇀"
FixedOrder = true
CursorGroup = "family"
dofile(paths.code("walker/scripts/menus/cursor-menu.lua"))

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

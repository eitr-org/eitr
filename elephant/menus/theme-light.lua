local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "theme-light"
NamePretty = i18n.tr("Light")
Parent = "theme"
Icon = "󰖙"
FixedOrder = true

GetEntries = dofile(paths.code("elephant/theme-entries.lua"))("light")

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

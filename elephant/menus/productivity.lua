local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "productivity"
NamePretty = i18n.tr("Productivity")
Parent = "install"
Icon = "󰃖"
FixedOrder = true
SoftwareGroup = "productivity"
dofile(paths.code("walker/scripts/menus/software-menu.lua"))

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

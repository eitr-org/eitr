local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "developer-apps"
NamePretty = i18n.tr("Developer Apps")
Parent = "install"
Icon = "󱌢"
FixedOrder = true
SoftwareGroup = "developer-apps"
dofile(paths.code("walker/scripts/menus/software-menu.lua"))

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

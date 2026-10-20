local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "ai-install"
NamePretty = i18n.tr("AI CLIs")
Parent = "install"
Icon = "󱜙"
FixedOrder = true
SoftwareGroup = "ai"
dofile(paths.code("walker/scripts/menus/software-menu.lua"))

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

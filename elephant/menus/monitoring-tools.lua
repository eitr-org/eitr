local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "monitoring-tools"
NamePretty = i18n.tr("Monitoring Tools")
Parent = "monitoring"
Icon = "\239\144\165"
FixedOrder = true
SoftwareGroup = "monitoring"
dofile(paths.code("walker/scripts/menus/software-menu.lua"))

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

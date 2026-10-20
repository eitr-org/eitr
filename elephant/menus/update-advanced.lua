local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "update-advanced"
NamePretty = i18n.tr("Advanced Updates")
Parent = "update"
Icon = "󰒓"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("update-advanced")

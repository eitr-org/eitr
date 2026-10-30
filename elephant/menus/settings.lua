local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "settings"
NamePretty = i18n.tr("Settings")
Parent = "main"
Icon = ""
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("settings")

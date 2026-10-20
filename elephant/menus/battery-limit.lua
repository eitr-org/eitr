local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "battery-limit"
NamePretty = i18n.tr("Battery Charge Limit")
Parent = "system-devices"
Icon = "󰂄"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("battery-limit")

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/system-devices.json. Typing also searches the menus below this one.
Name = "system-devices"
NamePretty = i18n.tr("Devices & Input")
Parent = "system"
Icon = "󰍹"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("system-devices")

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/event-sounds.json. Charger sounds shows only on PCs with a battery.
Name = "event-sounds"
NamePretty = i18n.tr("Event Sounds")
Parent = "system-devices"
Icon = "󰂚"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("event-sounds")

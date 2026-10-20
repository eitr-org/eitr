local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/tools.json. Typing also searches the menus below this one.
Name = "tools"
NamePretty = i18n.tr("Tools")
Parent = "main"
Icon = "󱁤"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("tools")

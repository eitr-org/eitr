local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/main.json. Typing searches every menu, so search also
-- works when Shift+Backspace returns here.
Name = "main"
NamePretty = i18n.tr("Main")
Description = "Main menu"
Icon = "󰣇"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("main")

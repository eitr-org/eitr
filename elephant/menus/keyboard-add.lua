local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "keyboard-add"
NamePretty = i18n.tr("Add Layout")
Parent = "keyboard"
Icon = "󰌌"
FixedOrder = true

GetEntries = dofile(paths.code("elephant/keyboard-catalog.lua"))

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

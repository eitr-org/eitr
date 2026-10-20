local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "ai-claude"
NamePretty = i18n.tr("Claude")
Parent = "ai-tools"
Icon = "󰙴"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("ai-claude")

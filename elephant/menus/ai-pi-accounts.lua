local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "ai-pi-accounts"
NamePretty = i18n.tr("Accounts")
Parent = "ai-pi"
Icon = "󰀄"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/ai-account-entries.lua"))("pi")

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

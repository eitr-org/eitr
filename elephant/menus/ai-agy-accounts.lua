local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "ai-agy-accounts"
NamePretty = i18n.tr("Accounts")
Parent = "ai-agy"
Icon = "󰀄"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/ai-account-entries.lua"))("agy")

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

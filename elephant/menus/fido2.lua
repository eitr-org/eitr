local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "fido2"
NamePretty = i18n.tr("FIDO2 Security Key")
Parent = "security"
Icon = "󰌆"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("fido2")

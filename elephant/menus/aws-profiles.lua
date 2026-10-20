local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "aws-profiles"
NamePretty = i18n.tr("AWS")
Parent = "cloud"
Icon = ""
FixedOrder = true

GetEntries = dofile(paths.code("elephant/aws-profile-entries.lua"))("", true)

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

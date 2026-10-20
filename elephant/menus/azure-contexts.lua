local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "azure-contexts"
NamePretty = i18n.tr("Azure")
Parent = "cloud"
Icon = "󰠅"
GetEntries = dofile(paths.code("elephant/cloud-context-entries.lua"))("azure", Icon)

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

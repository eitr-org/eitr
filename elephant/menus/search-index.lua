local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "search-index"
NamePretty = i18n.tr("Search")
HideFromProviderlist = true
FixedOrder = false

local search = dofile(paths.code("elephant/search-index-entries.lua"))

function GetEntries()
    return search("main")
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "plugins"
NamePretty = i18n.tr("Plugins")
Parent = "main"
Icon = ""
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("plugins", function(entries)
    for _, entry in ipairs(dofile(paths.code("elephant/plugin-entries.lua"))("plugins")) do
        table.insert(entries, entry)
    end
    return entries
end)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "plugins-install"
NamePretty = i18n.tr("Plugins")
Parent = "install"
Icon = "󰏖"
FixedOrder = true

GetEntries = function() return dofile(paths.code("elephant/plugin-entries.lua"))("plugins-install") end

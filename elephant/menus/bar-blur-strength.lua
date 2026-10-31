local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-blur-strength"
NamePretty = i18n.tr("Blur strength")
Parent = "bar"
Icon = "󰐾"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    return choices(paths.code("quickshell/desktop-bar/scripts/bar-settings.py"), "blur-strength", {
        {i18n.mark("Gentle"), "light", "󰐾", i18n.mark("Set blur strength: Gentle")},
        {i18n.mark("Medium"), "medium", "󰐾", i18n.mark("Set blur strength: Medium")},
        {i18n.mark("Strong"), "strong", "󰐾", i18n.mark("Set blur strength: Strong")},
    })
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

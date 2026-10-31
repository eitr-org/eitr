local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "terminal-padding"
NamePretty = i18n.tr("Padding")
Parent = "terminal"
Icon = "󰐾"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    return choices(paths.code("walker/scripts/actions/style/terminal.py"), "padding", {
        {i18n.mark("None"), "none", "󰐾", i18n.mark("Set padding: None")},
        {i18n.mark("Small"), "small", "󰐾", i18n.mark("Set padding: Small")},
        {i18n.mark("Comfortable"), "comfortable", "󰐾", i18n.mark("Set padding: Comfortable")},
    })
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

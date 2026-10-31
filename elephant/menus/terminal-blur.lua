local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "terminal-blur"
NamePretty = i18n.tr("Blur")
Parent = "terminal"
Icon = "󰐾"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    return choices(paths.code("walker/scripts/actions/style/terminal.py"), "blur", {
        {i18n.mark("Off"), "off", "󰐾", i18n.mark("Set blur: Off")},
        {i18n.mark("On"), "on", "󰐾", i18n.mark("Set blur: On")},
    })
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

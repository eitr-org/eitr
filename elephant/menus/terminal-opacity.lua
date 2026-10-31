local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "terminal-opacity"
NamePretty = i18n.tr("Opacity")
Parent = "terminal"
Icon = "󰐾"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    return choices(paths.code("walker/scripts/actions/style/terminal.py"), "opacity", {
        {i18n.mark("Solid (100%)"), "solid", "󰐾", i18n.mark("Set opacity: Solid (100%)")},
        {i18n.mark("Light (90%)"), "light", "󰐾", i18n.mark("Set opacity: Light (90%)")},
        {i18n.mark("Medium (80%)"), "medium", "󰐾", i18n.mark("Set opacity: Medium (80%)")},
        {i18n.mark("Default (75%)"), "default", "󰐾", i18n.mark("Set opacity: Default (75%)")},
        {i18n.mark("Strong (70%)"), "strong", "󰐾", i18n.mark("Set opacity: Strong (70%)")},
    })
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

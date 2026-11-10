local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "wallpaper-per-display"
NamePretty = i18n.tr("Wallpaper per display")
Parent = "appearance"
Icon = "󰍹"
FixedOrder = true
function GetEntries()
    return i18n.entries(choices(paths.code("walker/scripts/actions/wallpaper/assignments.py"), "per-display", {
        {i18n.mark("Off"), "off", Icon, i18n.mark("A new wallpaper changes every display")},
        {i18n.mark("On"), "on", Icon, i18n.mark("A new wallpaper changes only the display you are using")},
    }), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

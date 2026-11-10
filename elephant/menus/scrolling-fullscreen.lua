local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "scrolling-fullscreen"
NamePretty = i18n.tr("Fullscreen when one column")
Parent = "window-layout"
Icon = "󰍹"
FixedOrder = true
function GetEntries()
    return i18n.entries(choices(paths.code("quickshell/desktop-bar/scripts/desktop-style.py"), "scrollFullscreen", {
        {i18n.mark("Off"), "no", Icon, i18n.mark("A lone column keeps its width")},
        {i18n.mark("On"), "yes", Icon, i18n.mark("A lone column fills the screen")},
    }), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

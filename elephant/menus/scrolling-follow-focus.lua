local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "scrolling-follow-focus"
NamePretty = i18n.tr("Follow focus")
Parent = "window-layout"
Icon = "󰍹"
FixedOrder = true
function GetEntries()
    return i18n.entries(choices(paths.code("quickshell/desktop-bar/scripts/desktop-style.py"), "scrollFollowFocus", {
        {i18n.mark("Off"), "no", Icon, i18n.mark("Keep the view still when focus moves")},
        {i18n.mark("On"), "yes", Icon, i18n.mark("Scroll to the window that gets focus")},
    }), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "focus"
NamePretty = i18n.tr("Focus")
Parent = "style"
Icon = "󰍹"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    return i18n.entries(choices(paths.code("quickshell/desktop-bar/scripts/focus-mode.py"), "focus", {
        {i18n.mark("Off"), "off", Icon, i18n.mark("Restore the normal desktop")},
        {i18n.mark("On"), "on", Icon, i18n.mark("Distraction-free tabbed desktop")},
    }), false)
end

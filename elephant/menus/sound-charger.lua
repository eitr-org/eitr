local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "sound-charger"
NamePretty = i18n.tr("Charger sounds")
Parent = "event-sounds"
Icon = "󰂄"
FixedOrder = true
function GetEntries()
    return i18n.entries(choices(paths.code("walker/scripts/actions/system/event-sounds.py"), "charger", {
        {i18n.mark("Off"), "off", Icon, i18n.mark("Plug and unplug the charger silently")},
        {i18n.mark("On"), "on", Icon, i18n.mark("Play a sound when the charger is connected")},
    }), false)
end
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "lighting"
NamePretty = i18n.tr("Lighting")
Parent = "system-devices"
Icon = "󰌵"
FixedOrder = true

local choices = dofile(paths.code("elephant/choice-entries.lua"))
local script = paths.code("walker/scripts/actions/system/lighting.py")
function GetEntries()
    return choices(script, "follow", {
        {i18n.mark("Follow Theme"), "on", "󰏘", i18n.mark("Fans, keyboard and other OpenRGB devices take the theme's colour")},
        {i18n.mark("Leave As Is"), "off", "󰌶", i18n.mark("Theme changes do not touch device lighting")},
    })
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

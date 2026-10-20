local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "terminal-cursor-fire"
NamePretty = i18n.tr("Cursor Fire")
Parent = "terminal"
Icon = "󰈸"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
local helper = paths.code("walker/scripts/actions/style/terminal-effects.py")
function GetEntries()
    return choices(helper, "cursor-fire", {
        {i18n.mark("Disabled"), "off", "󰈸", i18n.mark("Keep the normal fast cursor trail")},
        {i18n.mark("Enabled"), "on", "󰈸", i18n.mark("Use Kitty’s built-in blazing cursor trail")},
    })
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

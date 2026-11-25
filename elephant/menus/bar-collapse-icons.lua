local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-collapse-icons"
NamePretty = i18n.tr("Collapse icons")
Parent = "bar"
Icon = "󰅁"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("collapseIcons", {
        {i18n.mark("Off"), "no", "󰅁", i18n.mark("Keep all available status icons visible.")},
        {i18n.mark("On"), "yes", "󰅁", i18n.mark("Show a button to hide or reveal status icons in Full, Centered, Tabs and Islands.")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-lyrics"
NamePretty = i18n.tr("Online lyrics")
Parent = "bar"
Icon = "󰍡"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("lyrics", {
        {i18n.mark("Off"), "no", "󰍡", i18n.mark("Show lyrics only when the player sends them")},
        {i18n.mark("On"), "yes", "󰍡", i18n.mark("Look up lyrics on LRCLIB; sends each song's title, artist and album")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

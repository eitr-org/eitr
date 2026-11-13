local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-island-style"
NamePretty = i18n.tr("Island style")
Parent = "bar"
Icon = "󰕰"
FixedOrder = true
local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
function GetEntries()
    return entries("islandStyle", {
        {i18n.mark("Floating"), "floating", "󰕰", i18n.mark("Islands float half the outer gap off the screen edge")},
        {i18n.mark("Attached"), "attached", "󰕰", i18n.mark("Islands sit against the screen edge with straight sides")},
    })
end
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local catalog = dofile(paths.code("elephant/choice-lists.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "window-layout"
NamePretty = i18n.tr("Window layout")
Parent = "style"
Icon = "󰍹"
FixedOrder = true
local load = dofile(paths.code("elephant/scoped-menu.lua"))("window-layout", function(entries)
    local options = {}
    for _, choice in ipairs(catalog.window_layouts) do
        table.insert(options, {choice.label, choice.id, Icon, choice.description})
    end
    for _, entry in ipairs(choices(paths.code("quickshell/desktop-bar/scripts/desktop-style.py"), "layout", options)) do
        table.insert(entries, entry)
    end
    return entries
end)
GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, load)

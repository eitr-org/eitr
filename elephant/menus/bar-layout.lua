local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-layout"
NamePretty = i18n.tr("Layout")
Parent = "bar"
Icon = "󰕰"
FixedOrder = true

local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
-- The layouts, their icons and descriptions come from tools/choice-lists.json.
local layouts = dofile(paths.code("elephant/choice-lists.lua")).bar_layouts
function GetEntries()
    local options = {}
    for _, layout in ipairs(layouts) do
        table.insert(options, {layout.label, layout.id, layout.icon, layout.description, layout.keywords})
    end
    return entries("layout", options)
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

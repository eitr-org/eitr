local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "bar-appearance"
NamePretty = i18n.tr("Appearance")
Parent = "bar"
Icon = "󰏘"
FixedOrder = true

local entries = dofile(paths.code("elephant/bar-settings-entries.lua"))
-- The appearances, their icons and descriptions come from tools/choice-lists.json.
local appearances = dofile(paths.code("elephant/choice-lists.lua")).bar_appearances
function GetEntries()
    local options = {}
    for _, appearance in ipairs(appearances) do
        table.insert(options, {appearance.label, appearance.id, appearance.icon, appearance.description})
    end
    return entries("appearance", options)
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

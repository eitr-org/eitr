local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- The styles come from quickshell/desktop-bar/corner-styles.json; the current one is checked.
Name = "corners"
NamePretty = i18n.tr("Corners")
Parent = "style"
Icon = "󰕰"
FixedOrder = true

local choices = dofile(paths.code("elephant/choice-entries.lua"))
local script = paths.code("quickshell/desktop-bar/scripts/desktop-style.py")
local descriptions = {
    ["extra-rounded"] = "Softest corners on windows, panels and menus",
    rounded = "Gently rounded corners (default)",
    square = "Sharp corners everywhere",
}

function GetEntries()
    local handle = io.open(paths.code("quickshell/desktop-bar/corner-styles.json"), "r")
    if not handle then return {} end
    local ok, definitions = pcall(jsonDecode, handle:read("*a"))
    handle:close()
    local options = {}
    for key, style in pairs(ok and definitions.styles or {}) do
        table.insert(options, {style.label, key, Icon, descriptions[key] or ""})
    end
    table.sort(options, function(first, second) return first[1]:lower() < second[1]:lower() end)
    return choices(script, "corners", options)
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/shortcuts.json. Typing also searches the menus below this one.
Name = "shortcuts"
NamePretty = i18n.tr("Shortcuts")
Parent = "learn"
Icon = "󰌌"
FixedOrder = true
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = "python3 " .. quote(paths.code("quickshell/desktop-bar/scripts/focus-mode.py"))
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("shortcuts", function(entries)
    local reader = io.popen(helper .. " status")
    local focused = reader and reader:read("*l") == "on"
    if reader then reader:close() end
    if not focused then return entries end
    local kept = {}
    for _, entry in ipairs(entries) do
        if entry.Text ~= "Toggle Floating And Pin" and entry.Text ~= "Toggle Fullscreen" and entry.Text ~= "Toggle Desktop Bar" then
            table.insert(kept, entry)
        end
    end
    reader = io.popen(helper .. " entries")
    if reader then
        local ok, shortcuts = pcall(jsonDecode, reader:read("*a"))
        reader:close()
        if ok then for _, entry in ipairs(shortcuts) do table.insert(kept, entry) end end
    end
    return kept
end)

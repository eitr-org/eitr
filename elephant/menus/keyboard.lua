local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "keyboard"
NamePretty = i18n.tr("Keyboard")
Parent = "system-devices"
Icon = "󰌌"
FixedOrder = true

-- Layouts are added and removed only here: the bar panel and the Control
-- Center just switch between them.
local script = paths.code("quickshell/desktop-bar/scripts/keyboard-layout.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local entries = {{Text = "Add Layout", Icon = "󰌌", State = {"submenu"}, SubMenu = "keyboard-add"}}
    local layouts = {}
    local reader = io.popen("python3 " .. quote(script) .. " list")
    if reader then
        for line in reader:lines() do
            local index, label, active = line:match("^(%d+)\t(.-)\t([01])$")
            if index then table.insert(layouts, {index = index, label = label, active = active == "1"}) end
        end
        reader:close()
    end
    for _, layout in ipairs(layouts) do
        local entry = {
            Text = layout.label, Value = layout.index,
            Subtext = layout.active and i18n.mark("Current layout") or i18n.mark("Switch to this layout"),
            Icon = layout.active and "\239\128\140" or "󰌌",
            State = layout.active and {"current"} or {},
            Actions = {open = "python3 " .. quote(script) .. " --notify select " .. layout.index},
        }
        if #layouts > 1 then
            entry.Subtext = layout.active and i18n.mark("Current layout · Delete removes it") or i18n.mark("Switch to this layout · Delete removes it")
            entry.Actions.keyboard_delete = "python3 " .. quote(script) .. " --notify remove " .. layout.index
        end
        table.insert(entries, entry)
    end
    local catalog = dofile(paths.code("elephant/keyboard-catalog.lua"))()
    return entries, {{parent = i18n.tr("Add Layout"), entries = i18n.entries(catalog, false)}}
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

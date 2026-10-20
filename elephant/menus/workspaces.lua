local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "workspaces"
NamePretty = i18n.tr("Workspaces")
Parent = "style"
Icon = "󰍹"
FixedOrder = true

local script = paths.code("quickshell/desktop-bar/scripts/workspace-style.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local current = "Runes"
    local reader = io.popen("python3 " .. quote(script) .. " current")
    if reader then current = reader:read("*l") or current; reader:close() end
    local choices = {"Dots", "Glyph", "Numbers", "Runes"}
    local entries = {}
    for _, choice in ipairs(choices) do
        local state = {"workspace-" .. choice:lower()}
        if choice == current then table.insert(state, "current") end
        table.insert(entries, {
            Text = choice, Value = choice,
            Icon = choice == current and "" or "󰍹",
            State = state,
            Actions = {open = "python3 " .. quote(script) .. " " .. quote(choice)},
        })
    end
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

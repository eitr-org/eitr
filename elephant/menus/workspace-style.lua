local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "workspace-style"
NamePretty = i18n.tr("Workspace style")
Parent = "workspaces"
Icon = "󰍹"
FixedOrder = true

local script = paths.code("quickshell/desktop-bar/scripts/workspace-style.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local current = "Runes"
    local sample_count = 4
    local reader = io.popen("python3 " .. quote(script) .. " summary")
    if reader then
        local raw = reader:read("*a")
        reader:close()
        local ok, summary = pcall(jsonDecode, raw)
        if ok and type(summary) == "table" then
            current = summary.current or current
            sample_count = tonumber(summary.previewCount) or sample_count
        end
    end
    local choices = {"Dots", "Glyph", "Numbers", "Runes"}
    local entries = {}
    for _, choice in ipairs(choices) do
        local state = {"workspace-" .. choice:lower(), "workspace-preview-" .. sample_count}
        if choice == current then table.insert(state, "current") end
        table.insert(entries, {
            Text = choice, Subtext = i18n.mark("Use these workspace markers"), Value = choice,
            Icon = choice == current and "\239\128\140" or "󰍹",
            State = state,
            Actions = {open = "python3 " .. quote(script) .. " " .. quote(choice)},
        })
    end
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries, dofile(paths.code("elephant/workspace-context.lua")))

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "system-shortcuts"
NamePretty = i18n.tr("System Shortcuts")
HideFromProviderlist = true
FixedOrder = true

function GetEntries()
    local panels = paths.code("quickshell/desktop-bar/scripts/show-panel.sh")
    local quote = dofile(paths.code("elephant/shell-quote.lua"))
    return {
        {Text = "Calendar", Subtext = "Open the calendar panel", Icon = "󰃭", Actions = {open = "bash " .. quote(panels) .. " calendar"}},
        {Text = "Workspace Overview", Subtext = "Show occupied workspaces", Icon = "󰕮", Keywords = {"workspaces", "windows", "overview"},
            Actions = {open = "bash " .. quote(panels) .. " overview"}},
        {Text = "Ragnarök", Subtext = "Open the Ragnarök realm", Icon = "ᚺ", Keywords = {"ragnarok", "fenrir"},
            Actions = {open = "eitr-shell desktop-bar ipc call -- realm ragnarok"}},
    }
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- The current channel is marked; choosing the other opens a terminal only for the
-- password that switching needs (update-channel.py set).
Name = "update-channel"
NamePretty = i18n.tr("Update Channel")
Parent = "update"
Icon = "󰚰"
FixedOrder = true

local quote = dofile(paths.code("elephant/shell-quote.lua"))
local script = paths.code("walker/scripts/actions/system/update-channel.py")
local channels = {
    {name = "stable", text = i18n.mark("Stable"), subtext = i18n.mark("Eitr builds once they have been tried on testing")},
    {name = "testing", text = i18n.mark("Testing"), subtext = i18n.mark("New Eitr builds first; less tested, snapshots still protect updates")},
}

function GetEntries()
    local current = "stable"
    local status = io.popen("/usr/lib/eitr/eitr-system channel-status 2>/dev/null")
    if status then current = (status:read("*l") or ""):match("^%s*(.-)%s*$"); status:close() end
    local entries = {}
    for _, channel in ipairs(channels) do
        local active = channel.name == current
        local entry = {Text = channel.text, Value = channel.name, Icon = active and "\239\128\140" --[[U+F00C]] or "󰚰",
            Subtext = active and (channel.name == "stable" and i18n.tr("Current channel · Stable builds, tried on testing") or i18n.tr("Current channel · Testing builds, less tested; snapshots protect updates")) or i18n.tr(channel.subtext),
            State = active and {"current"} or {}}
        if not active then
            entry.Actions = {open = "kitty -e python3 " .. quote(paths.code("walker/scripts/actions/task-terminal.py"))
                .. " python3 " .. quote(script) .. " set " .. channel.name}
        end
        table.insert(entries, entry)
    end
    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

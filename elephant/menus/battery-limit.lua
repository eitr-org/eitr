local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "battery-limit"
NamePretty = i18n.tr("Battery Charge Limit")
Parent = "system-devices"
Icon = "󰂄"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("battery-limit", function(entries)
    local current = dofile(paths.code("elephant/battery-state.lua"))().current
    for _, entry in ipairs(entries) do
        if entry.Actions and entry.Actions.open:match(" set " .. (current or "unknown") .. "$") then
            entry.Icon = "\239\128\140"
            entry.State = {"current"}
        end
    end
    return entries
end)

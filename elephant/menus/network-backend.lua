local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "network-backend"
NamePretty = i18n.tr("Network Backend")
Parent = "system-connectivity"
Icon = "󰖩"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("network-backend", function(entries)
    local handle = io.open("/var/lib/eitr/network-backend/selected", "r")
    local current = handle and handle:read("*l") or nil
    if handle then handle:close() end
    if not current then
        local enabled = io.popen("systemctl is-enabled NetworkManager.service 2>/dev/null")
        current = enabled and enabled:read("*l") == "enabled" and "networkmanager" or "iwd"
        if enabled then enabled:close() end
    end
    for _, entry in ipairs(entries) do
        if entry.Actions and entry.Actions.open:match("network%-backend.py " .. current .. "$") then
            entry.Icon = "\239\128\140"
            entry.State = {"current"}
        end
    end
    return entries
end)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "remote-share-setup"
NamePretty = i18n.tr("Setup")
Parent = "remote-share"
Icon = ""
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("remote-share-setup")

local entries = GetEntries
GetEntries = function(query)
    local result = entries(query)
    local handle = io.popen("systemctl --user is-enabled eitr-sunshine.service 2>/dev/null")
    local enabled = handle and handle:read("*l") == "enabled"
    if handle then handle:close() end
    local choice = enabled and "login" or "no-login"
    for _, entry in ipairs(result) do
        if entry.Actions and entry.Actions.open and entry.Actions.open:match(" host " .. choice .. "$") then
            entry.Icon = "\239\128\140"
            entry.State = {"current"}
        end
    end
    return result
end

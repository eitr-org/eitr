local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "remote-share-setup"
NamePretty = i18n.tr("Sharing Setup")
Parent = "remote-access"
Icon = ""
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("remote-share-setup")

local function enabled(command)
    local handle = io.popen(command .. " 2>/dev/null")
    local result = handle and handle:read("*l") == "enabled"
    if handle then handle:close() end
    return result
end

local entries = GetEntries
GetEntries = function(query)
    local result = entries(query)
    -- The current choice of each pair: sharing at sign-in, and on the login screen.
    local choices = {
        enabled("systemctl --user is-enabled eitr-sunshine.service") and "login" or "no-login",
        enabled("systemctl is-enabled eitr-login-share.service") and "login-screen" or "no-login-screen",
    }
    for _, entry in ipairs(result) do
        for _, choice in ipairs(choices) do
            if entry.Actions and entry.Actions.open and entry.Actions.open:match(" host " .. choice .. "$") then
                entry.Icon = "\239\128\140"
                entry.State = {"current"}
            end
        end
    end
    return result
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/vpn.json. Typing also searches the menus below this one.
Name = "vpn"
NamePretty = i18n.tr("VPN")
Parent = "install"
Icon = "󰏖"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("vpn")
local entries = GetEntries
local quote = dofile(paths.code("elephant/shell-quote.lua"))
function GetEntries()
    local installed = {}
    for _, group in ipairs({"vpn", "remote-access"}) do
        local handle = io.popen("python3 " .. quote(paths.code("walker/scripts/actions/install/software.py")) .. " recipes " .. group)
        if handle then
            local output = handle:read("*a")
            handle:close()
            for _, recipe in ipairs(jsonDecode(output)) do
                if recipe.installed then installed[i18n.tr(recipe.label)] = true end
            end
        end
    end
    local rows = entries()
    for _, row in ipairs(rows) do
        if installed[row.Text] then
            row.Icon = "\239\128\140"
            row.State = {"current"}
        end
    end
    return rows
end

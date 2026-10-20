local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
Name = "oracle-contexts"
NamePretty = i18n.tr("Oracle Cloud")
Parent = "cloud"
Icon = ""
function GetEntries()
    local command = "python3 " .. quote(paths.code("walker/scripts/menus/cloud/providers.py")) .. " oracle"
    local handle = io.popen(command .. " entries")
    if not handle then return {} end
    local entries = {}
    for line in handle:lines() do
        local text, detail, action = line:match("^([^\t]+)\t([^\t]+)\t(.+)$")
        if text then
            table.insert(entries, {Text = text, Subtext = detail, Icon = Icon, Actions = {open = action}})
        end
    end
    handle:close()
    return entries
end

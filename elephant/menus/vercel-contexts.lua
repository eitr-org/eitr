local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
Name = "vercel-contexts"
NamePretty = i18n.tr("Vercel")
Parent = "cloud"
Icon = "󰅟"
FixedOrder = true
function GetEntries()
    local command = "python3 " .. quote(paths.code("walker/scripts/menus/cloud/providers.py")) .. " vercel"
    local handle = io.popen(command .. " entries")
    if not handle then return {} end
    local entries = {}
    for line in handle:lines() do
        local text, detail, action, remove, icon = line:match("^([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]*)\t([^\t]+)$")
        if text then
            table.insert(entries, {Text = text, Subtext = remove == "" and detail or nil, Icon = icon,
                Keywords = {detail}, State = remove ~= "" and {"submenu"} or nil, Actions = {open = action, cloud_delete = remove ~= "" and remove or nil}})
        end
    end
    handle:close()
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

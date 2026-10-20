local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local helper = paths.code("walker/scripts/actions/install/software.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
function GetEntries()
    local handle = io.popen("python3 " .. quote(helper) .. " recipes " .. quote(SoftwareGroup))
    if not handle then return {} end
    local output = handle:read("*a"); handle:close()
    local entries = {}
    for _, row in ipairs(jsonDecode(output)) do
        if row.error then
            -- Show why the catalog is unavailable instead of an empty menu.
            table.insert(entries, {Text = row.label, Subtext = "", Icon = Icon})
        elseif row.id then
            local actions = {open = "python3 " .. quote(helper) .. " recipe-launch " ..
                quote(SoftwareGroup) .. " " .. quote(row.id)}
            if row.removable then
                actions.app_uninstall = "python3 " .. quote(helper) .. " recipe-uninstall " ..
                    quote(SoftwareGroup) .. " " .. quote(row.id)
            end
            local origin = row.manager or (row.source == "aur" and "AUR · review before installing" or row.source)
            table.insert(entries, {Text = row.label, Value = row.id,
                Subtext = row.installed and ("Installed · " .. (row.manager or row.source)) or origin,
                State = row.installed and {"current"} or {},
                Icon = row.installed and "\239\128\140" --[[U+F00C]] or Icon, Actions = actions})
        end
    end
    return entries
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "plugin-actions"
NamePretty = i18n.tr("Plugins")
Parent = "plugins-install"
Icon = "󰏖"
FixedOrder = true
HideFromProviderlist = true
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/install/plugins.py")

-- Update is offered only when the last check found a new commit for this plugin.
local function has_update(id)
    local handle = io.popen("python3 " .. quote(helper) .. " installed")
    if not handle then return false end
    local raw = handle:read("*a")
    handle:close()
    local ok, rows = pcall(jsonDecode, raw)
    for _, row in ipairs(ok and rows or {}) do
        if row.id == id then return (tonumber(row.updateCount) or 0) > 0 end
    end
    return false
end

GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("plugin-actions", function(entries)
    local id = lastMenuValue("plugins-install") or ""
    local update = has_update(id)
    local shown = {}
    for _, entry in ipairs(entries) do
        if entry.SubMenu then
            table.insert(shown, entry)
        elseif entry.Text == "Remove" or update then
            local action = entry.Text == "Remove" and "remove" or "update"
            entry.Actions = {open = "kitty --class eitr-plugins -e python3 " .. quote(paths.code("walker/scripts/actions/task-terminal.py"))
                .. " python3 " .. quote(helper) .. " " .. action .. " " .. quote(id)}
            table.insert(shown, entry)
        end
    end
    return shown
end)

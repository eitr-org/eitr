local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "plugin-actions"
NamePretty = i18n.tr("Plugins")
Parent = "plugins-install"
Icon = "󰏖"
FixedOrder = true
HideFromProviderlist = true
local quote = dofile(paths.code("elephant/shell-quote.lua"))
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("plugin-actions", function(entries)
    local id = lastMenuValue("plugins-install") or ""
    for _, entry in ipairs(entries) do
        if not entry.SubMenu then
            local action = entry.Text == "Remove" and "remove" or "update"
            entry.Actions = {open = "kitty --class eitr-plugins -e python3 " .. quote(paths.code("walker/scripts/actions/task-terminal.py"))
                .. " python3 " .. quote(paths.code("walker/scripts/actions/install/plugins.py")) .. " " .. action .. " " .. quote(id)}
        end
    end
    return entries
end)

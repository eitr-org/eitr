local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local presenter = paths.code("walker/scripts/actions/task-terminal.py")
local names = {gcp = "GCP", azure = "Azure"}
return function(provider, icon)
    return function()
        local base = paths.code("walker/scripts/menus/cloud/")
        local command = "python3 " .. quote(base .. "contexts.py") .. " " .. provider
        local function form(arguments)
            return "kitty --class eitr-cloud -e python3 " .. quote(presenter) .. " python3 "
                .. quote(base .. "accounts.py") .. " " .. arguments
        end
        local entries = {{Text = i18n.tr("Add {provider} Account", {provider = names[provider]}), Subtext = i18n.tr("Name it, then sign in"),
            Keywords = {"Add " .. names[provider] .. " Account", "Name it, then sign in"},
            Icon = "󰐕", Actions = {open = form("add " .. provider)}}}
        local handle = io.popen(command .. " --list 2>/dev/null")
        if handle then
            for line in handle:lines() do
                local label, token, key = line:match("^([^\t]+)\t([^\t]+)\t(.+)$")
                if label then
                    table.insert(entries, { Text = label, Icon = icon,
                        Actions = { open = command .. " --open " .. quote(token),
                            cloud_rename = form("rename " .. provider .. " " .. quote(key)) } })
                end
            end
            handle:close()
        end
        if #entries == 1 then
            table.insert(entries, {Text = "Refresh", Subtext = "Signed in already? Read the CLI's accounts again",
                Icon = icon, Actions = {open = command .. " --refresh"}})
        end
        return entries
    end
end

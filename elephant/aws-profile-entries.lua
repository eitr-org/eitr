local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- One entry per AWS profile, as listed by the cloud menus' shared helper
-- (EITR_AWS_PROFILES in ~/.config/eitr/cloud.env, else `aws configure list-profiles`).
local home = os.getenv("HOME")
local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))
local aws_dir = paths.code("walker/scripts/menus/cloud/aws")
local accounts = paths.code("walker/scripts/menus/cloud/accounts.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")

local function form(arguments)
    return "kitty --class eitr-cloud -e python3 " .. shell_quote(presenter) .. " python3 "
        .. shell_quote(accounts) .. " " .. arguments
end

-- script: file in aws_dir run with the profile; icon: entry icon;
-- manage: also offer Add AWS Account and renaming (the AWS menu, not Grafana).
return function(script, icon, manage)
    return function()
        local entries = {}
        if manage then
            table.insert(entries, {Text = "Add AWS Account", Subtext = "Name it, then sign in with SSO or access keys",
                Icon = "󰐕", Actions = {open = form("add aws")}})
        end
        local handle = io.popen(shell_quote(aws_dir .. "/menu.sh") .. " --list-profiles 2>/dev/null")
        if not handle then return entries end

        for line in handle:lines() do
            local label, profile = line:match("^([^\t]+)\t(.+)$")
            if label then
                table.insert(entries, {
                    Text = label,
                    Subtext = label ~= profile and profile or nil,
                    Value = profile,
                    Icon = icon,
                    Actions = { open = shell_quote(aws_dir .. "/" .. script) .. " " .. shell_quote(profile),
                        cloud_rename = manage and form("rename aws " .. shell_quote(profile)) or nil },
                })
            end
        end
        handle:close()
        return entries
    end
end

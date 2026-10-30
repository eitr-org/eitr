local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- Git projects two levels below DEV_DIR (default ~/Development), matching
-- walker/scripts/actions/development/open-project.sh.
local home = os.getenv("HOME")
local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))

local function dev_dir()
    local dir = os.getenv("DEV_DIR")
    if not dir or dir == "" then dir = home .. "/Development" end
    return (dir:gsub("/+$", ""))
end

-- open_command receives a shell-quoted path and returns the command to run.
return function(icons, open_command)
    return function()
        local root = dev_dir()
        local entries = {
            {
                Text = "Open Development",
                Subtext = "Open your development folder",
                Value = root,
                Icon = icons.root,
                Actions = { open = open_command(shell_quote(root)) },
            },
        }

        local handle = io.popen("find " .. shell_quote(root) .. " -mindepth 3 -maxdepth 3 -type d -name .git 2>/dev/null | sort")
        if not handle then return entries end

        for git_dir in handle:lines() do
            local path = git_dir:gsub("/%.git$", "")
            table.insert(entries, {
                Text = path:sub(#root + 2),
                Subtext = "Open this project in the editor",
                Value = path,
                Icon = icons.project,
                Actions = { open = open_command(shell_quote(path)) },
            })
        end
        handle:close()
        return entries
    end
end

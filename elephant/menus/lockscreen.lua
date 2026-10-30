local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "lockscreen"
NamePretty = i18n.tr("Lockscreen")
Parent = "style"
Icon = "󰌾"
FixedOrder = true

local root = paths.code("quickshell/lockscreen/scripts/")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local own = paths.code("walker/scripts/actions/style/own.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")
local yours = i18n.mark("Yours")

function GetEntries()
    local entries = {{
        Text = "Create Lockscreen",
        Subtext = "A design with your own picture, color and greeting",
        Icon = "󰐕",
        Actions = {open = "kitty --class eitr-menu-terminal -e python3 " .. quote(presenter) .. " python3 " .. quote(own) .. " lockscreen create"},
    }}
    local current = "hyprlock"
    local state = io.open(os.getenv("HOME") .. "/.config/lockscreen/selected", "r")
    if state then current = state:read("*a"):match("^%s*(.-)%s*$"); state:close() end
    local list = io.popen("python3 " .. quote(root .. "settings.py") .. " list")
    if list then
        for line in list:lines() do
            local value, label = line:match("^(.-)\t(.*)$")
            if value then
                local mine = value:sub(1, 5) == "user:"
                local preview = paths.code("quickshell/lockscreen/themes/") .. value .. "/preview.png"
                if value == "theme-wallpaper" or mine then
                    local reader = io.popen("python3 " .. quote(root .. "settings.py") .. " preview " .. quote(value))
                    if reader then preview = reader:read("*l") or preview; reader:close() end
                end
                table.insert(entries, {
                    Text = label, Value = value,
                    Subtext = (mine and yours .. " · " or "") .. i18n.tr("Select or preview this lockscreen"),
                    Icon = value == current and "\239\128\140" or "󰌾",
                    State = value == current and {"current"} or {},
                    Preview = preview,
                    PreviewType = "file",
                    Actions = {
                        lockscreen_apply = "bash " .. quote(root .. "launch.sh") .. " select " .. quote(value),
                        lockscreen_preview = "bash " .. quote(root .. "preview.sh") .. " " .. quote(value),
                        lockscreen_delete = mine and ("python3 " .. quote(own) .. " lockscreen delete " .. quote(value)) or nil,
                    },
                })
            end
        end
        list:close()
    end
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

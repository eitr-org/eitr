local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "lockscreen"
NamePretty = i18n.tr("Lockscreen")
Parent = "style"
Icon = "󰌾"
FixedOrder = true

local root = paths.code("quickshell/lockscreen/scripts/")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local entries = {}
    local current = "hyprlock"
    local state = io.open(os.getenv("HOME") .. "/.config/lockscreen/selected", "r")
    if state then current = state:read("*a"):match("^%s*(.-)%s*$"); state:close() end
    local list = io.popen("python3 " .. quote(root .. "settings.py") .. " list")
    if list then
        for line in list:lines() do
            local value, label = line:match("^(.-)\t(.*)$")
            if value then
                local preview = paths.code("quickshell/lockscreen/themes/") .. value .. "/preview.png"
                if value == "theme-wallpaper" then
                    local reader = io.popen("python3 " .. quote(root .. "settings.py") .. " preview theme-wallpaper")
                    if reader then preview = reader:read("*l") or preview; reader:close() end
                end
                table.insert(entries, {
                    Text = label, Value = value,
                    Icon = value == current and "" or "󰌾",
                    State = value == current and {"current"} or {},
                    Preview = preview,
                    PreviewType = "file",
                    Actions = {
                        lockscreen_apply = "bash " .. quote(root .. "launch.sh") .. " select " .. quote(value),
                        lockscreen_preview = "bash " .. quote(root .. "preview.sh") .. " " .. quote(value),
                    },
                })
            end
        end
        list:close()
    end
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

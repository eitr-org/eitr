local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "wallpaper"
NamePretty = i18n.tr("Wallpaper")
Parent = "style"
Icon = "🖻"
FixedOrder = true

local home = os.getenv("HOME")
local background_dir = home .. "/.config/theme/current/backgrounds"
local own_dir = paths.own("wallpapers")

local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))
local own = paths.code("walker/scripts/actions/style/own.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")
local yours = i18n.mark("Yours")

local function pictures(directory)
    local cmd = "find " .. shell_quote(directory) .. " -maxdepth 1 -type f \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \\) -printf '%f\\n' 2>/dev/null | sort -V"
    local files = {}
    local handle = io.popen(cmd)
    if handle then
        for file in handle:lines() do table.insert(files, file) end
        handle:close()
    end
    return files
end

function GetEntries()
    local entries = {{
        Text = "Add My Own Wallpaper",
        Subtext = "A picture file or an https address, kept on this computer",
        Icon = "󰐕",
        Actions = {open = "kitty --class eitr-menu-terminal -e python3 " .. shell_quote(presenter) .. " python3 " .. shell_quote(own) .. " wallpaper add"},
    }}
    local current = ""
    local current_file = io.open(home .. "/.cache/current-wallpaper", "r")
    if current_file then
        current = current_file:read("*a"):match("^%s*(.-)%s*$")
        current_file:close()
    end
    local function add(directory, file, mine)
        local path = directory .. "/" .. file
        table.insert(entries, {
            Text = file,
            Subtext = mine and yours or nil,
            Value = path,
            Icon = path == current and "\239\128\140" or path,
            State = path == current and { "current" } or {},
            Preview = path,
            PreviewType = "file",
            Actions = {
                open = paths.code("walker/scripts/actions/wallpaper/apply.sh ") .. shell_quote(path),
                wallpaper_preview = "bash " .. shell_quote(paths.code("quickshell/desktop-bar/scripts/appearance-picker.sh")) .. " wallpaper",
                wallpaper_delete = mine and ("python3 " .. shell_quote(own) .. " wallpaper delete " .. shell_quote(path)) or nil,
            },
        })
    end
    for _, file in ipairs(pictures(background_dir)) do add(background_dir, file, false) end
    -- Own wallpapers the current theme already shows (a theme made from one keeps a copy) are left out.
    local handle = io.popen("python3 " .. shell_quote(own) .. " wallpaper list 2>/dev/null")
    if handle then
        for path in handle:lines() do add(own_dir, path:match("[^/]+$"), true) end
        handle:close()
    end
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

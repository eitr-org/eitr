local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "wallpaper"
NamePretty = i18n.tr("Wallpaper")
Parent = "style"
Icon = "🖻"
FixedOrder = true

local home = os.getenv("HOME")
local background_dir = home .. "/.config/theme/current/backgrounds"

local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local entries = {}
    local current = ""
    local current_file = io.open(home .. "/.cache/current-wallpaper", "r")
    if current_file then
        current = current_file:read("*a"):match("^%s*(.-)%s*$")
        current_file:close()
    end
    local cmd = "find '" .. background_dir .. "' -maxdepth 1 -type f \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \\) -printf '%f\\n' 2>/dev/null | sort -V"
    local handle = io.popen(cmd)

    if handle then
        for file in handle:lines() do
            local path = background_dir .. "/" .. file
            table.insert(entries, {
                Text = file,
                Value = path,
                Icon = path == current and "" or path,
                State = path == current and { "current" } or {},
                Preview = path,
                PreviewType = "file",
                Actions = {
                    open = paths.code("walker/scripts/actions/wallpaper/apply.sh ") .. shell_quote(path),
                    wallpaper_preview = "bash " .. shell_quote(paths.code("quickshell/desktop-bar/scripts/appearance-picker.sh")) .. " wallpaper",
                },
            })
        end
        handle:close()
    end

    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

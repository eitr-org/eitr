local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local home = os.getenv("HOME")

local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))
local i18n = dofile(paths.code("elephant/i18n.lua"))
local own = paths.code("walker/scripts/actions/style/own.py")
local own_dir = paths.own("themes") .. "/"
local presenter = paths.code("walker/scripts/actions/task-terminal.py")
local yours = i18n.mark("Yours")

local function current_theme()
    local file = io.open(home .. "/.cache/current-theme", "r")
    if not file then return "" end
    local name = file:read("*a"):match("^%s*(.-)%s*$")
    file:close()
    return name
end

local function display_name(name, directory)
    local file = io.open(directory .. "/display-name", "r")
    if file then
        local label = file:read("*a"):match("^%s*(.-)%s*$")
        file:close()
        if label ~= "" then return label end
    end
    return (name:gsub("[-_]", " "):gsub("(%a)([%w]*)", function(first, rest)
        return first:upper() .. rest
    end))
end

return function(category)
    return function()
        local entries = {}
        local current = current_theme()
        local themes = paths.themes()
        local names = {}
        for name, _ in pairs(themes) do table.insert(names, name) end
        table.sort(names)
        for _, theme in ipairs(names) do
            local theme_dir = themes[theme]
            local marker = io.open(theme_dir .. "/light.mode", "r")
            local is_light = marker ~= nil
            if marker then marker:close() end
            if (category == "light") == is_light then
                local mine = theme_dir:sub(1, #own_dir) == own_dir
                table.insert(entries, {
                    Text = display_name(theme, theme_dir),
                    Subtext = mine and yours or nil,
                    Value = theme,
                    Icon = theme == current and "" or "󰸌",
                    State = theme == current and { "current" } or {},
                    Preview = theme_dir .. "/preview.png",
                    PreviewType = "file",
                    Actions = {
                        theme_apply = paths.code("walker/scripts/actions/style/apply.sh ") .. shell_quote(theme),
                        theme_preview = paths.code("walker/scripts/actions/style/preview.sh ") .. shell_quote(theme),
                        theme_colors = mine and ("kitty --class eitr-menu-terminal -e python3 " .. shell_quote(presenter)
                            .. " python3 " .. shell_quote(own) .. " theme colors " .. shell_quote(theme)) or nil,
                        theme_delete = mine and ("python3 " .. shell_quote(own) .. " theme delete " .. shell_quote(theme)) or nil,
                    },
                })
            end
        end
        return entries
    end
end

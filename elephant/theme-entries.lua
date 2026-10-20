local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local home = os.getenv("HOME")

local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))

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
                table.insert(entries, {
                    Text = display_name(theme, theme_dir),
                    Value = theme,
                    Icon = theme == current and "" or "󰸌",
                    State = theme == current and { "current" } or {},
                    Preview = theme_dir .. "/preview.png",
                    PreviewType = "file",
                    Actions = {
                        theme_apply = paths.code("walker/scripts/actions/style/apply.sh ") .. shell_quote(theme),
                        theme_preview = paths.code("walker/scripts/actions/style/preview.sh ") .. shell_quote(theme),
                    },
                })
            end
        end
        return entries
    end
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "apps"
NamePretty = i18n.tr("Apps")
Parent = "main"
Icon = "󰣇"
FixedOrder = false
SearchName = true

local home = os.getenv("HOME")
local app_dirs = {
    home .. "/.local/share/applications",
    home .. "/.local/share/flatpak/exports/share/applications",
    "/var/lib/flatpak/exports/share/applications",
    "/usr/local/share/applications",
    "/usr/share/applications",
}

local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))

local function basename(path)
    return path:match("([^/]+)$") or path
end

local function desktop_id(path)
    return basename(path)
end

local function parse_desktop_file(path)
    local file = io.open(path, "r")
    if not file then
        return nil
    end

    local entry = {}
    local in_desktop_entry = false

    for line in file:lines() do
        if line == "[Desktop Entry]" then
            in_desktop_entry = true
        elseif line:match("^%[") then
            in_desktop_entry = false
        elseif in_desktop_entry then
            local key, value = line:match("^([%w%-]+)%s*=%s*(.*)$")
            if key and value then
                entry[key] = value
            end
        end
    end

    file:close()
    return entry
end

local function is_visible_app(entry)
    if not entry then
        return false
    end

    if entry.Type ~= "Application" then
        return false
    end

    if not entry.Name or entry.Name == "" then
        return false
    end

    if not entry.Exec or entry.Exec == "" then
        return false
    end

    if entry.NoDisplay == "true" or entry.Hidden == "true" then
        return false
    end

    return true
end

function GetEntries()
    local entries = {}
    local seen = {}

    local directories, priority = {}, {}
    for index, dir in ipairs(app_dirs) do
        table.insert(directories, shell_quote(dir))
        priority[dir] = index
    end
    local handle = io.popen("find -L " .. table.concat(directories, " ") .. " -maxdepth 1 -type f -name '*.desktop' 2>/dev/null")
    local files = {}
    if handle then
        for path in handle:lines() do table.insert(files, path) end
        handle:close()
    end
    table.sort(files, function(left, right)
        local left_priority = priority[left:match("^(.*)/")] or #app_dirs + 1
        local right_priority = priority[right:match("^(.*)/")] or #app_dirs + 1
        if left_priority ~= right_priority then return left_priority < right_priority end
        return left < right
    end)
    for _, path in ipairs(files) do
        local id = desktop_id(path)

        if not seen[id] then
            local app = parse_desktop_file(path)

            if is_visible_app(app) then
                seen[id] = true

                local keywords = {}
                if app.Keywords then
                    for keyword in app.Keywords:gmatch("[^;]+") do
                        table.insert(keywords, keyword)
                    end
                end

                if app.GenericName then
                    table.insert(keywords, app.GenericName)
                end

                table.insert(entries, {
                    Text = app.Name,
                    Subtext = app.GenericName or app.Comment or id,
                    Value = path,
                    Icon = app.Icon or "application-x-executable",
                    Keywords = keywords,
                    Actions = {
                        open = shell_quote(paths.code("walker/bin/app-launch")) .. " --desktop " .. shell_quote(id),
                        app_uninstall = "python3 " .. shell_quote(paths.code("walker/scripts/actions/install/software.py")) .. " uninstall " .. shell_quote(path),
                    },
                })
            end
        end
    end

    table.sort(entries, function(left, right)
        return left.Text:lower() < right.Text:lower()
    end)

    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), true)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

if rawget(_G, "EitrI18n") then return EitrI18n end
local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local translations = nil
local module = {}
local sort_keys = {}
local language = "English"

-- Resolve the session locale locally; provider startup must not launch processes.
local function locale_name()
    local requested = "en"
    for _, variable in ipairs({"LC_ALL", "LC_MESSAGES", "LANG"}) do
        local value = os.getenv(variable) or ""
        if value:match("%S") then requested = value; break end
    end
    requested = requested:match("^%s*(.-)%s*$"):gsub("[.@].*$", ""):gsub("-", "_")
    local base, region = requested:match("^([a-zA-Z][a-zA-Z][a-zA-Z]?)_([a-zA-Z][a-zA-Z])$")
    if not base then base, region = requested:match("^([a-zA-Z][a-zA-Z][a-zA-Z]?)_([0-9][0-9][0-9])$") end
    base = base or requested:match("^([a-zA-Z][a-zA-Z][a-zA-Z]?)$")
    if not base then return "en" end
    base = base:lower()
    local supported = dofile(paths.code("i18n/languages.lua"))
    local regional = region and (base .. "_" .. region:upper()) or base
    if supported[regional] then return regional end
    if base == "pt" then base = "pt_BR" end
    return supported[base] and base or "en"
end

local function catalog()
    if translations then return translations end
    translations = {}
    local loaded, result = pcall(dofile, paths.code("i18n/catalogs/" .. locale_name() .. "/menus.lua"))
    if loaded and type(result) == "table" then
        translations = result.messages or {}
        sort_keys = result.sortKeys or {}
        language = result.language or language
    end
    return translations
end

function module.language()
    catalog()
    return language
end

function module.mark(source)
    return source
end

function module.tr(source, values)
    if not source or source == ">" then return source end
    local translated = catalog()[source] or source
    return (translated:gsub("([%%{])([%w_]+)(}?)", function(marker, name, closing)
        local key = marker == "{" and closing == "}" and name or tonumber(name)
        local value = key and values and values[key]
        return value ~= nil and tostring(value) .. (marker == "%" and closing or "") or marker .. name .. closing
    end))
end

function module.entries(entries, preserve_order)
    for _, entry in ipairs(entries) do
        local english = entry.Text or ""
        local description = entry.Subtext or ""
        local keywords = {}
        for _, keyword in ipairs(entry.Keywords or {}) do table.insert(keywords, keyword) end
        table.insert(keywords, english)
        if description ~= ">" then table.insert(keywords, description) end
        entry.Text = module.tr(english)
        entry.Subtext = module.tr(entry.Subtext)
        table.insert(keywords, entry.Text)
        if entry.Subtext ~= ">" then table.insert(keywords, entry.Subtext or "") end
        entry.Keywords = keywords
    end
    if not preserve_order then
        table.sort(entries, function(left, right)
            local function folder(entry)
                if entry.SubMenu then return true end
                for _, state in ipairs(entry.State or {}) do if state == "submenu" then return true end end
                return false
            end
            if folder(left) ~= folder(right) then return folder(left) end
            local left_title = sort_keys[left.Text] or tostring(left.Text or ""):lower()
            local right_title = sort_keys[right.Text] or tostring(right.Text or ""):lower()
            if left_title == right_title then return tostring(left.Value or "") < tostring(right.Value or "") end
            return left_title < right_title
        end)
    end
    return entries
end

EitrI18n = module
return module

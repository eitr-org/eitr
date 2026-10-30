local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "fonts"
NamePretty = i18n.tr("Fonts")
Parent = "style"
Icon = "󰛖"
FixedOrder = true

local helper = paths.code("walker/scripts/actions/style/fonts.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
function GetEntries()
    local reader = io.popen("python3 " .. quote(helper) .. " list")
    if not reader then return {} end
    local raw = reader:read("*a")
    reader:close()
    local entries = {}
    for _, row in ipairs(jsonDecode(raw) or {}) do
        table.insert(entries, {Text = row.family, Subtext = i18n.mark("Use this font throughout the desktop"), Value = row.family,
            Icon = row.current and "\239\128\140" or "󰛖", State = row.current and {"current"} or {},
            Actions = {font_select = "python3 " .. quote(helper) .. " select " .. quote(row.family),
                font_delete = row.deletable and "python3 " .. quote(helper) .. " delete " .. quote(row.family) or nil}})
    end
    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

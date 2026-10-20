local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "ai-default"
NamePretty = i18n.tr("Default Assistant")
Parent = "ai-tools"
Icon = "󱜙"
FixedOrder = true
local script = paths.code("walker/scripts/actions/ai-assistant.py")
function GetEntries()
    local options = {}
    local reader = io.popen("python3 " .. quote(script) .. " installed")
    if reader then
        local ok, rows = pcall(jsonDecode, reader:read("*a"))
        reader:close()
        for _, row in ipairs(ok and rows or {}) do
            table.insert(options, {row.label, row.id, Icon, i18n.tr("Open with the assistant shortcut")})
        end
    end
    if #options == 0 then
        return i18n.entries({{Text = "Install an AI Assistant", Icon = Icon,
            Subtext = "Install an assistant before choosing a default",
            Actions = {open = quote(paths.code("walker/bin/walker")) .. " --provider menus:ai-install"}}}, false)
    end
    return i18n.entries(choices(script, "assistant", options), false)
end

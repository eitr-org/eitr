local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "language"
NamePretty = i18n.tr("Language")
Parent = "settings"
Icon = "󰗊"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    local label = i18n.tr("System default")
    local system_name = nil
    local quote = dofile(paths.code("elephant/shell-quote.lua"))
    local reader = io.popen("python3 " .. quote((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/eitr_language.py") .. " system-name 2>/dev/null")
    if reader then
        local name = reader:read("*l")
        local ok = reader:close()
        if ok and name and name:match("%S") then
            system_name = name
            label = i18n.tr("System default ({language})", {language = name})
        end
    end
    local entries = choices((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/eitr_language.py", "locale", {
        {label, "system", "󰗊", i18n.mark("Follow the system language; sign out and back in to apply")},
        {"English", "en", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Português (Brasil)", "pt_BR", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Español", "es", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Deutsch", "de", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Français", "fr", "󰗊", i18n.mark("Sign out and back in to apply")}
    })
    local visible = {}
    for _, entry in ipairs(entries) do
        if entry.Value == "system" or entry.Text ~= system_name or #entry.State > 0 then
            table.insert(visible, entry)
        end
    end
    return i18n.entries(visible, false)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

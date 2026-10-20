local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "language"
NamePretty = i18n.tr("Language")
Parent = "system"
Icon = "󰗊"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
function GetEntries()
    return i18n.entries(choices((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/eitr_language.py", "locale", {
        {i18n.mark("System default"), "system", "󰗊", i18n.mark("Follow the system language; sign out and back in to apply")},
        {"English", "en", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Português (Brasil)", "pt_BR", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Español", "es", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Deutsch", "de", "󰗊", i18n.mark("Sign out and back in to apply")},
        {"Français", "fr", "󰗊", i18n.mark("Sign out and back in to apply")}
    }), false)
end

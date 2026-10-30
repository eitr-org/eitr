local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "terminal"
NamePretty = i18n.tr("Terminal")
Parent = "style"
Icon = "󰆍"
FixedOrder = true
local choices = dofile(paths.code("elephant/choice-entries.lua"))
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("terminal", function(entries)
    for _, entry in ipairs(choices(paths.code("walker/scripts/actions/style/terminal.py"), "terminal", {
        {i18n.mark("Ghostty"), "ghostty", "󰆍", i18n.mark("Use Ghostty for your terminal")},
        {i18n.mark("Kitty"), "kitty", "󰆍", i18n.mark("Use Kitty for your terminal (default)")},
    })) do
        table.insert(entries, entry)
    end
    return entries
end)

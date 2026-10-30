local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "projects-nvim"
NamePretty = i18n.tr("LazyVim Projects")
Parent = "development"
Icon = ""
FixedOrder = true

local project_entries = dofile(paths.code("elephant/project-entries.lua"))

GetEntries = project_entries({ root = "", project = "" }, function(path)
    return "EITR_TERMINAL_STYLE=window kitty --directory " .. path .. " -e nvim ."
end)

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

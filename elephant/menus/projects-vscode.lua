local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "projects-vscode"
NamePretty = i18n.tr("VS Code Projects")
Parent = "development"
Icon = ""
FixedOrder = true

local quote = dofile(paths.code("elephant/shell-quote.lua"))
local project_entries = dofile(paths.code("elephant/project-entries.lua"))

GetEntries = project_entries({ root = "", project = "" }, function(path)
    return quote(paths.code("walker/bin/app-launch")) .. " code " .. path
end)

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

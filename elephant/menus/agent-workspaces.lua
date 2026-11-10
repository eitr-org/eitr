local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Rows: elephant/menu-rows/agent-workspaces.json. Typing also searches the menus below this one.
Name = "agent-workspaces"
NamePretty = i18n.tr("Agent Workspaces")
Parent = "development"
Icon = "󱚝"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/scoped-menu.lua"))("agent-workspaces")

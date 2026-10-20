local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "aws-ecs-deployments-1"
NamePretty = i18n.tr("Deployments")
Parent = "aws-ecs"
Icon = "󰐱"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/cloud-navigation-entries.lua"))(Name)
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

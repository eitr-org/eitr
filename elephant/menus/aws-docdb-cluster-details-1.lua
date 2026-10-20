local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "aws-docdb-cluster-details-1"
NamePretty = i18n.tr("Cluster details")
Parent = "aws-docdb"
Icon = "󰅟"
FixedOrder = true
GetEntries = dofile(paths.code("elephant/cloud-navigation-entries.lua"))(Name)
dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

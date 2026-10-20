local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "keyboard"
NamePretty = i18n.tr("Keyboard")
Parent = "system-devices"
Icon = "󰌌"
FixedOrder = true

local script = paths.code("quickshell/desktop-bar/scripts/keyboard-layout.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local entries = {}
    local reader = io.popen("python3 " .. quote(script) .. " list")
    if reader then
        for line in reader:lines() do
            local index, label, active = line:match("^(%d+)\t(.-)\t([01])$")
            if index then
                table.insert(entries, {
                    Text = label, Value = index,
                    Icon = active == "1" and "" or "󰌌",
                    State = active == "1" and {"current"} or {},
                    Actions = {open = "python3 " .. quote(script) .. " select " .. index,
                        keyboard_delete = "python3 " .. quote(script) .. " remove " .. index},
                })
            end
        end
        reader:close()
    end
    if #entries == 1 then entries[1].Actions.keyboard_delete = nil end
    return entries
end

dofile(paths.code("walker/scripts/menus/alphabetical.lua"))

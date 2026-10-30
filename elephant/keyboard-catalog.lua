local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- Every XKB layout and variant; type to search. Added ones carry the check mark.
local script = paths.code("quickshell/desktop-bar/scripts/keyboard-layout.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

return function()
    local entries = {}
    local reader = io.popen("python3 " .. quote(script) .. " catalog-rows")
    if reader then
        for line in reader:lines() do
            local layout, variant, label, added = line:match("^([^\t]*)\t([^\t]*)\t(.-)\t([01])$")
            if layout then
                local entry = {Text = label, Value = layout .. ":" .. variant,
                    Keywords = {layout, variant}}
                if added == "1" then
                    entry.Subtext = "Already added"
                    entry.Icon = "\239\128\140"
                    entry.State = {"current"}
                else
                    entry.Subtext = "Add this layout; Alt + Shift switches layouts"
                    entry.Icon = "󰌌"
                    entry.Actions = {open = "python3 " .. quote(script) .. " --notify add "
                        .. quote(layout) .. " " .. quote(variant)}
                end
                table.insert(entries, entry)
            end
        end
        reader:close()
    end
    return entries
end


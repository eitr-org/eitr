local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

-- Rows for a setting with a few choices, the current one checked. SCRIPT answers
-- "get KEY" with the current value and applies "set KEY VALUE".
return function(script, key, choices)
    local current = ""
    local reader = io.popen("python3 " .. quote(script) .. " get " .. key)
    if reader then current = reader:read("*l") or ""; reader:close() end
    local entries = {}
    for _, choice in ipairs(choices) do
        local selected = current == choice[2]
        table.insert(entries, {
            Text = choice[1], Value = choice[2], Subtext = choice[4],
            Icon = selected and "\239\128\140" --[[U+F00C]] or choice[3],
            State = selected and {"current"} or {},
            Actions = {open = "python3 " .. quote(script) .. " set " .. key .. " " .. choice[2]},
        })
    end
    return entries
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- Typed queries may reuse a snapshot only while its choices and assignment hold.
return function()
    local contents = {}
    for _, relative in ipairs({"eitr/style.json", "eitr/workspaces.lua", "quickshell/desktop-bar/workspace-style.json"}) do
        local reader = io.open(paths.config .. "/" .. relative, "r")
        table.insert(contents, reader and reader:read("*a") or "")
        if reader then reader:close() end
    end
    return table.concat(contents, "\n")
end

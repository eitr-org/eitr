local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local live = dofile(paths.code("elephant/live-menu.lua"))
return function(name)
    return live(name, function()
        local command = "python3 " .. quote(paths.code("walker/scripts/menus/cloud/navigation.py"))
            .. " snapshot " .. quote(name)
        local handle = io.popen(command)
        if not handle then return {} end
        local raw = handle:read("*a")
        handle:close()
        local valid, snapshot = pcall(jsonDecode, raw)
        if not valid then return {} end
        return snapshot.entries or {}, snapshot.descendants or {}
    end, function()
        -- A changed selection invalidates rows bound to the previous account.
        local handle = io.open(paths.config .. "/eitr/cloud-navigation.json", "r")
        if not handle then return "" end
        local raw = handle:read("*a")
        handle:close()
        return raw
    end)
end

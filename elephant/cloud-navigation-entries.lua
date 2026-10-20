local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
return function(name)
    return function(query)
        local command = "python3 " .. quote(paths.code("walker/scripts/menus/cloud/navigation.py"))
            .. " entries " .. quote(name) .. " " .. quote(query or "")
        local handle = io.popen(command)
        if not handle then return {} end
        local raw = handle:read("*a")
        handle:close()
        local valid, entries = pcall(jsonDecode, raw)
        return valid and entries or {}
    end
end

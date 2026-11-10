local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
-- Calling this module reads the battery state. Its menus are shown, browsed and
-- searched only on PCs with a system battery; search-index.py keeps the same list.
return setmetatable({menus = {["battery-limit"] = true, ["sound-charger"] = true}}, {__call = function()
    local handle = io.popen("python3 " .. quote(paths.code("walker/scripts/actions/system/battery-limit.py")) .. " menu-state")
    if not handle then return {} end
    local ok, state = pcall(jsonDecode, handle:read("*a"))
    handle:close()
    return ok and state or {}
end})

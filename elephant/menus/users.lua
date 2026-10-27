local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/system/users.py")
local own_rows = dofile(paths.code("elephant/scoped-menu.lua"))("users")
Name = "users"
NamePretty = i18n.tr("Users")
Parent = "security"
Icon = "󰀄"
FixedOrder = true

-- Create User… comes from menu-rows/users.json; the accounts on this PC follow,
-- read-only, sorted by name.
function GetEntries()
    local entries = own_rows("")
    local handle = io.popen("python3 " .. quote(helper) .. " --entries")
    if handle then
        local output = handle:read("*a"); handle:close()
        local ok, users = pcall(jsonDecode, output)
        for _, user in ipairs(ok and users or {}) do table.insert(entries, user) end
    end
    return entries
end

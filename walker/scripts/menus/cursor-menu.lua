local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local helper = paths.code("walker/scripts/actions/style/cursor.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
function GetEntries()
    local handle = io.popen("python3 " .. quote(helper) .. " entries " .. quote(CursorGroup))
    if not handle then return {} end
    local output = handle:read("*a")
    handle:close()
    local entries = {}
    for _, row in ipairs(jsonDecode(output)) do
        table.insert(entries, {Text = row.label, Subtext = row.detail,
            Icon = row.icon ~= "" and row.icon or Icon,
            State = row.selected and { "current" } or {},
            Actions = {open = "python3 " .. quote(helper) .. " set " .. quote(CursorGroup) .. " " .. quote(row.id)}})
    end
    return entries
end

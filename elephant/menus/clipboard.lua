local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
Name = "clipboard"
NamePretty = i18n.tr("Clipboard History")
Icon = "edit-paste"
FixedOrder = true

local helper = paths.code("walker/scripts/menus/clipboard.py")
local quote = dofile(paths.code("elephant/shell-quote.lua"))

function GetEntries()
    local handle = io.popen("python3 " .. quote(helper))
    if not handle then return {} end
    local output = handle:read("*a")
    handle:close()
    local entries = {}
    for _, row in ipairs(jsonDecode(output)) do
        table.insert(entries, {
            Text = row.label,
            Value = row.id,
            Icon = row.preview ~= "" and "image-x-generic" or "edit-paste",
            Preview = row.preview,
            PreviewType = row.preview ~= "" and "file" or "",
            Actions = {
                clipboard_paste = "python3 " .. quote(helper) .. " paste " .. quote(row.id),
                clipboard_delete = "python3 " .. quote(helper) .. " delete " .. quote(row.id),
            },
        })
    end
    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), true)
end

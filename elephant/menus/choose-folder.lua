local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local shell_quote = dofile(paths.code("elephant/shell-quote.lua"))
Name = "choose-folder"
NamePretty = i18n.tr("Folder")
Icon = "󰉋"
FixedOrder = true

-- The folder step of the AI and project menus. walker/scripts/menus/choose-folder.py saves
-- the request this reads. Browsing lists the folders here; typing searches every folder
-- below them (six levels, without hidden, dependency and build folders), named by the
-- folder with its location underneath, so a folder's own name ranks first.
local DEPTH = 6
local LIMIT = 5000
local PRUNED = {"node_modules", "target", "build", "dist", "venv", "__pycache__"}
-- Elephant scores every folder whose name starts with the typed text alike and orders ties
-- arbitrarily. While typing, a title starts with invisible zero-width spaces, each moving
-- the match one character later: none for an exact name, then one per level below, after
-- NOT_EXACT more for any other match. So the exact name ranks first, nearest first.
local DEPTH_MARK = "\226\128\139"
local NOT_EXACT = 6

local function request_path()
    local runtime = os.getenv("XDG_RUNTIME_DIR") or ""
    return runtime .. "/eitr/choose-folder.json"
end

local function read_request()
    local handle = io.open(request_path(), "r")
    if not handle then return nil, "" end
    local raw = handle:read("*a")
    handle:close()
    local valid, request = pcall(jsonDecode, raw)
    if not valid or type(request) ~= "table" or not request.root or not request.current then return nil, raw end
    return request, raw
end

local function hex(text)
    return (text:gsub(".", function(character) return string.format("%02x", character:byte()) end))
end

local function helper(command, folder)
    local script = shell_quote(paths.code("walker/scripts/menus/choose-folder.py"))
    return "python3 " .. script .. " " .. command .. (folder and (" " .. hex(folder)) or "")
end

local function folders(current)
    local pruned = {}
    for _, name in ipairs(PRUNED) do table.insert(pruned, "-name " .. shell_quote(name)) end
    local command = "find " .. shell_quote(current) .. " -mindepth 1 -maxdepth " .. DEPTH
        .. " \\( -name '.*' -o " .. table.concat(pruned, " -o ") .. " \\) -prune -o -type d -printf '%P\\n' 2>/dev/null"
        .. " | head -n " .. LIMIT
    local handle = io.popen(command)
    if not handle then return {} end
    local found = {}
    for relative in handle:lines() do table.insert(found, relative) end
    handle:close()
    table.sort(found, function(left, right)
        local folded_left, folded_right = left:lower(), right:lower()
        if folded_left == folded_right then return left < right end
        return folded_left < folded_right
    end)
    return found
end

local function load()
    local request = read_request()
    if not request then return {} end
    local root, current = request.root, request.current
    local relative = current == root and "" or current:sub(#root + 2)
    local home = root == os.getenv("HOME")
    local open_text = relative ~= "" and i18n.tr("Open {folder}", {folder = relative})
        or (home and i18n.tr("Open Home") or i18n.tr("Open {folder}", {folder = root:match("([^/]+)$") or root}))
    local entries = {
        {Text = open_text, Subtext = i18n.tr("Use this folder"), Icon = request.icon ~= "" and request.icon or "󰉋",
            Actions = {open = helper("pick", current)}},
        {Text = i18n.tr("Back"), Subtext = relative == "" and i18n.tr("Return to the menu") or i18n.tr("Go up one folder"),
            Icon = "󰁍", Actions = {open = helper("up")}},
    }
    local groups, order = {}, {}
    for _, path in ipairs(folders(current)) do
        local parent, name = path:match("^(.*)/([^/]+)$")
        local _, slashes = path:gsub("/", "")
        local row = {Text = name or path, Value = tostring(slashes), Icon = "󰉋",
            Actions = {open = helper("enter", current .. "/" .. path)}}
        if not parent then
            row.State = {"submenu"}
            table.insert(entries, row)
        else
            if not groups[parent] then groups[parent] = {}; table.insert(order, parent) end
            table.insert(groups[parent], row)
        end
    end
    local descendants = {}
    for _, parent in ipairs(order) do table.insert(descendants, {parent = parent, entries = groups[parent]}) end
    return entries, descendants
end

local live = dofile(paths.code("elephant/live-menu.lua"))(Name, load, function()
    local _, raw = read_request()
    return raw
end)

function GetEntries(query)
    local entries = live(query)
    if not query or query == "" then return entries end
    local typed = query:lower()
    for _, entry in ipairs(entries) do
        local depth = tonumber(entry.Value or "")
        if depth then
            local marks = entry.Text:lower() == typed and depth or NOT_EXACT + depth
            entry.Text = string.rep(DEPTH_MARK, marks) .. entry.Text
        end
    end
    return entries
end

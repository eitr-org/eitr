local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local i18n = dofile(paths.code("elephant/i18n.lua"))
local helper = paths.code("walker/scripts/actions/install/plugins.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")

local function read(action)
    local handle = io.popen("python3 " .. quote(helper) .. " " .. action)
    if not handle then return {} end
    local raw = handle:read("*a")
    handle:close()
    local ok, rows = pcall(jsonDecode, raw)
    return ok and rows or {}
end

local function task(action, id)
    return "kitty --class eitr-plugins -e python3 " .. quote(presenter) .. " python3 " .. quote(helper) .. " " .. action .. " " .. quote(id or "")
end

return function(kind)
    local entries = {}
    if kind == "plugins" then
        for _, row in ipairs(read("rows")) do
            table.insert(entries, {Text = row.title, Subtext = row.description, Icon = row.icon,
                Value = row.id .. ":" .. row.index,
                Actions = {open = "python3 " .. quote(helper) .. " launch " .. quote(row.id) .. " " .. row.index}})
        end
        if #entries == 0 then
            table.insert(entries, {Text = i18n.tr("No plugins installed"), Subtext = i18n.tr("Add a plugin from Install > Plugins"), Icon = "󰏖"})
        end
    elseif kind == "plugins-install" then
        for _, row in ipairs(read("installed")) do
            table.insert(entries, {Text = row.name, State = {"submenu"}, Value = row.id,
                Icon = "󰏖", SubMenu = "plugin-actions"})
        end
        table.insert(entries, {Text = i18n.tr("Add Plugin…"), Subtext = i18n.tr("Review a Git repository before installing"), Icon = "󰐕",
            Actions = {open = task("add")}})
    else
        local id = lastMenuValue("plugins-install") or ""
        if id ~= "" then
            table.insert(entries, {Text = "Remove", Subtext = "Remove this plugin and its service", Icon = "󰆴",
                Actions = {open = task("remove", id)}})
            table.insert(entries, {Text = "Update", Subtext = "Review a new plugin commit", Icon = "󰚰",
                Actions = {open = task("update", id)}})
        end
    end
    -- Plugin labels belong to their authors; only Eitr's management UI is translated.
    return kind ~= "plugin-actions" and entries or i18n.entries(entries, false)
end

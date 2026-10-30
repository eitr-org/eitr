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

local function action_group(row, launch_rows)
    local actions = {{Text = i18n.tr("Remove"), Value = row.id .. ":remove", Icon = "󰆴", Actions = {open = task("remove", row.id)}}}
    if (tonumber(row.updateCount) or 0) > 0 then
        table.insert(actions, {Text = i18n.tr("Update"), Value = row.id .. ":update", Icon = "󰚰", Actions = {open = task("update", row.id)}})
    end
    for _, launch in ipairs(launch_rows) do
        if launch.id == row.id then
            table.insert(actions, {Text = launch.title, Translate = false, Icon = launch.icon, Value = row.id .. ":launch:" .. launch.index,
                Keywords = {launch.description}, Actions = {open = "python3 " .. quote(helper)
                    .. " launch " .. quote(row.id) .. " " .. launch.index}})
        end
    end
    return {parent = row.name, entries = actions}
end

return function(kind)
    local entries, descendants = {}, {}
    if kind == "plugins" then
        local updates = 0
        local launch_rows = read("rows")
        for _, row in ipairs(read("installed")) do
            if (tonumber(row.updateCount) or 0) > 0 then updates = updates + 1 end
            if row.blocked ~= "policy" and row.blocked ~= "blocklist" then
                table.insert(descendants, action_group(row, launch_rows))
            end
        end
        table.insert(entries, {Text = i18n.tr("Add Plugins"),
            Subtext = i18n.tr("Review a repository and select one or more plugins to install"), Icon = "󰐕",
            Actions = {open = task("add")}})
        if updates > 0 then
            table.insert(entries, {Text = i18n.tr("Update Plugins"), Subtext = i18n.tr("Review and update installed plugins"), Icon = "󰚰",
                Actions = {open = task("update")}})
        end
    elseif kind == "plugins-install" then
        local launch_rows = read("rows")
        for _, row in ipairs(read("installed")) do
            if row.blocked == "policy" or row.blocked == "blocklist" then
                -- Blocked plugins keep their files; the only action left is removing them.
                table.insert(entries, {Text = row.name, Icon = "󰀦", Value = row.id,
                    Subtext = row.blocked == "policy" and i18n.tr("Not allowed by your organization · select to remove")
                        or i18n.tr("Blocked by Eitr for your safety · select to remove"),
                    Actions = {open = task("remove", row.id)}})
            else
                table.insert(entries, {Text = row.name, State = {"submenu", "current"}, Value = row.id, Icon = "\239\128\140",
                    SubMenu = "plugin-actions"})
                table.insert(descendants, action_group(row, launch_rows))
            end
        end
        if #entries == 0 then
            table.insert(entries, {Text = i18n.tr("No plugins installed"),
                Subtext = i18n.tr("Add plugins from Main > Plugins"), Icon = "󰏖"})
        end
        table.sort(entries, function(first, second)
            local firstMenu = first.SubMenu ~= nil
            local secondMenu = second.SubMenu ~= nil
            if firstMenu ~= secondMenu then return firstMenu end
            return first.Text:lower() < second.Text:lower()
        end)
    elseif kind == "plugin-visuals" then
        local id = lastMenuValue("plugins-install") or ""
        if id ~= "" then
            for _, row in ipairs(read("visual-rows " .. quote(id))) do
                table.insert(entries, {Text = row.text, Subtext = row.subtext, Actions = row.actions})
            end
        end
    else
        local id = lastMenuValue("plugins-install") or ""
        if id ~= "" then
            table.insert(entries, {Text = "Visuals", State = {"submenu"}, SubMenu = "plugin-visuals"})
            table.insert(entries, {Text = "Remove", Subtext = "Remove this plugin and its service", Icon = "󰆴",
                Actions = {open = task("remove", id)}})
            table.insert(entries, {Text = "Update", Subtext = "Review a new plugin commit", Icon = "󰚰",
                Actions = {open = task("update", id)}})
        end
    end
    -- Plugin labels belong to their authors; only Eitr's management UI is translated.
    return kind ~= "plugin-actions" and entries or i18n.entries(entries, false), descendants
end

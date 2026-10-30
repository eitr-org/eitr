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

-- Only Eitr's own repository (checked by address in eitr_plugins.official) is called official.
local function origin(row)
    if row.official == true then return i18n.tr("Official Eitr plugin") end
    return i18n.tr("Plugin by {author} · not reviewed by Eitr", {author = row.author})
end

return function(kind)
    local entries = {}
    if kind == "plugins" then
        for _, row in ipairs(read("rows")) do
            -- The code is its author's: every row says whose it is and that Eitr did not review it.
            table.insert(entries, {Text = row.title, Subtext = origin(row),
                Keywords = {row.description}, Icon = row.icon,
                Value = row.id .. ":" .. row.index,
                Actions = {open = "python3 " .. quote(helper) .. " launch " .. quote(row.id) .. " " .. row.index}})
        end
        if #entries == 0 then
            table.insert(entries, {Text = i18n.tr("No plugins installed"), Subtext = i18n.tr("Add a plugin from Install > Plugins"), Icon = "󰏖"})
        end
    elseif kind == "plugins-install" then
        local updates = 0
        for _, row in ipairs(read("installed")) do
            if (tonumber(row.updateCount) or 0) > 0 then updates = updates + 1 end
            if row.blocked == "policy" or row.blocked == "blocklist" then
                -- Blocked plugins keep their files; the only action left is removing them.
                table.insert(entries, {Text = row.name, Icon = "󰀦", Value = row.id,
                    Subtext = row.blocked == "policy" and i18n.tr("Not allowed by your organization · select to remove")
                        or i18n.tr("Blocked by Eitr for your safety · select to remove"),
                    Actions = {open = task("remove", row.id)}})
            else
                table.insert(entries, {Text = row.name, State = {"submenu"}, Value = row.id, Icon = "󰏖",
                    Subtext = origin(row),
                    SubMenu = "plugin-actions"})
            end
        end
        table.insert(entries, {Text = i18n.tr("Add Plugin…"), Subtext = i18n.tr("Review a Git repository before installing"), Icon = "󰐕",
            Actions = {open = task("add")}})
        -- Offered only when the last check found a new commit for an installed plugin.
        if updates > 0 then
            table.insert(entries, {Text = i18n.tr("Update Plugins"), Subtext = i18n.tr("Review and update installed plugins"), Icon = "󰚰",
                Actions = {open = task("update")}})
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
    return kind ~= "plugin-actions" and entries or i18n.entries(entries, false)
end

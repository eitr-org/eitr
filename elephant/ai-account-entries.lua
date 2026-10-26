local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local script = paths.code("walker/scripts/actions/ai-accounts.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")

return function(identifier)
    return function()
        local command = "python3 " .. quote(script)
        local reader = io.popen(command .. " list " .. quote(identifier))
        if not reader then return {} end
        local ok, data = pcall(jsonDecode, reader:read("*a"))
        reader:close()
        if not ok then return {} end
        local function task(action, account)
            return "kitty --class eitr-software -e python3 " .. quote(presenter) .. " " .. command .. " " .. action .. " " .. quote(identifier) .. " " .. quote(account or "")
        end
        local entries = {}
        for _, account in ipairs(data.accounts or {}) do
            local entry = {
                Text = account.label, Subtext = i18n.tr("Select this account"),
                Icon = account.current and "\239\128\140" or "󰀄",
                State = account.current and {"current"} or {},
                Actions = {open = command .. " switch " .. quote(identifier) .. " " .. quote(account.id)},
            }
            if account.id ~= "default" then entry.Actions.ai_account_delete = task("delete", account.id) end
            table.insert(entries, entry)
        end
        if data.supported then
            table.insert(entries, {Text = i18n.tr("Add Account…"), Subtext = i18n.tr("Sign in to a separate account"),
                Icon = "󰀔", Actions = {open = task("add")}})
        else
            table.insert(entries, {Text = i18n.tr("Separate accounts unavailable"),
                Subtext = i18n.tr("This CLI has no supported isolated account folder"), Icon = "󰋽", Actions = {}})
        end
        return entries
    end
end

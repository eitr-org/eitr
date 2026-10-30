local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/development/git-accounts.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")
Name = "git-accounts"
NamePretty = i18n.tr("Git Accounts")
Parent = "development"
Icon = "󰊢"
FixedOrder = true

local function form(action)
    return "kitty --class eitr-git-accounts -e python3 " .. quote(presenter) .. " python3 " .. quote(helper) .. " " .. action
end

function GetEntries()
    local descendants = {}
    local entries = {
        {Text = "Add Account", Subtext = "Name, email and SSH key", Icon = "󰐕", Actions = {open = form("add")}},
        {Text = "Import Existing Setup", Subtext = "Identities configured outside EITR", Icon = "󰋺",
            Actions = {open = form("import")}},
    }
    local handle = io.popen("python3 " .. quote(helper) .. " rows")
    if handle then
        local output = handle:read("*a"); handle:close()
        for _, account in ipairs(jsonDecode(output) or {}) do
            local actions = {}
            for _, action in ipairs(account.searchActions or {}) do
                table.insert(actions, {Text = action.label, Subtext = action.hint, Icon = action.icon,
                    Value = account.id .. ":" .. action.label,
                    Actions = {open = "python3 " .. quote(helper) .. " do " .. quote(account.id) .. " " .. quote(action.label)}})
            end
            table.insert(descendants, {parent = account.label, entries = i18n.entries(actions, false)})
            -- git-account reads this row's Value through lastMenuValue("git-accounts").
            table.insert(entries, {Text = account.label, Subtext = account.isDefault and (#(account.folders or {}) > 0 and i18n.tr("Default · {folders}", {folders = table.concat(account.folders, ", ")}) or i18n.tr("Default")) or (#(account.folders or {}) > 0 and i18n.tr("Folders: {folders}", {folders = table.concat(account.folders, ", ")}) or i18n.tr("Not used yet")), State = {"submenu"}, Value = account.id,
                Icon = account.provider == "gitlab" and "\239\138\150" --[[U+F296]] or "\239\130\155" --[[U+F09B]], SubMenu = "git-account"})
        end
    end
    return entries, descendants
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    local entries, descendants = untranslatedGetEntries(...)
    return i18n.entries(entries, false), descendants
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

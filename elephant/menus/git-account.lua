local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/development/git-accounts.py")
Name = "git-account"
NamePretty = i18n.tr("Git Account")
Parent = "git-accounts"
Icon = "󰊢"
FixedOrder = true
HideFromProviderlist = true

-- Actions for the account chosen in Git Accounts; Shift+Backspace returns there.
function GetEntries()
    local account = lastMenuValue("git-accounts") or ""
    local entries = {}
    if account == "" then return entries end
    local handle = io.popen("python3 " .. quote(helper) .. " actions " .. quote(account))
    if not handle then return entries end
    local output = handle:read("*a"); handle:close()
    for _, action in ipairs(jsonDecode(output) or {}) do
        table.insert(entries, {Text = action.label, Subtext = action.hint, Icon = action.icon,
            Actions = {open = "python3 " .. quote(helper) .. " do " .. quote(account) .. " " .. quote(action.label)}})
    end
    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Only the assistants installed for this user (distro/software.json "ai" recipes,
-- checked by software.py), each opening its own menu; none installed offers the
-- AI CLIs install menu instead.
Name = "ai-tools"
NamePretty = i18n.tr("AI")
Parent = "development"
Icon = "󱜙"
FixedOrder = true

local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/install/software.py")
local assistants = {
    {id = "claude", text = "Claude", icon = "󰙴", submenu = "ai-claude"},
    {id = "codex", text = "Codex", icon = "󰆍", submenu = "ai-codex"},
    {id = "copilot", text = "GitHub Copilot CLI", icon = "󰆍", submenu = "ai-copilot"},
    {id = "gemini", text = "Gemini", icon = "󰊭", submenu = "ai-gemini"},
    {id = "grok", text = "Grok", icon = "󱙺", submenu = "ai-grok"},
}

function GetEntries()
    local installed = {}
    local handle = io.popen("python3 " .. quote(helper) .. " recipes ai")
    if handle then
        local ok, rows = pcall(jsonDecode, handle:read("*a"))
        handle:close()
        for _, row in ipairs(ok and rows or {}) do
            if row.installed then installed[row.id] = true end
        end
    end
    local entries = {{Text = "Default Assistant", Icon = Icon, State = {"submenu"}, SubMenu = "ai-default"}}
    for _, assistant in ipairs(assistants) do
        if installed[assistant.id] then
            table.insert(entries, {Text = assistant.text, Icon = assistant.icon, State = {"submenu"},
                SubMenu = assistant.submenu})
        end
    end
    if next(installed) == nil then
        table.insert(entries, {Text = "Install an AI Assistant", Icon = Icon,
            Subtext = "Claude Code, Codex, Gemini CLI, GitHub Copilot CLI or Grok Build",
            Actions = {open = quote(paths.code("walker/bin/walker")) .. " --provider menus:ai-install"}})
    end
    return entries
end

local untranslatedGetEntries = GetEntries
function GetEntries(...)
    return i18n.entries(untranslatedGetEntries(...), false)
end

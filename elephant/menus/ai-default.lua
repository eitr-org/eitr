local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local quote = dofile(paths.code("elephant/shell-quote.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "ai-default"
NamePretty = i18n.tr("Default Assistant")
Parent = "development"
Icon = "󱜙"
FixedOrder = true
local script = paths.code("walker/scripts/actions/ai-assistant.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")

local function task(action)
    return "kitty --class eitr-software -e python3 " .. quote(presenter) .. " python3 " .. quote(script) .. " " .. action
end

-- The offline assistant is always offered: a choice once set up, otherwise its setup.
function GetEntries()
    local options = {}
    local reader = io.popen("python3 " .. quote(script) .. " installed")
    if reader then
        local ok, rows = pcall(jsonDecode, reader:read("*a"))
        reader:close()
        for _, row in ipairs(ok and rows or {}) do
            table.insert(options, {row.label, row.id, Icon, i18n.tr("Open with the assistant shortcut")})
        end
    end
    local localState = "none"
    local status = io.popen("python3 " .. quote(script) .. " local-state")
    if status then localState = status:read("*l") or "none"; status:close() end
    local entries = {}
    if #options == 0 then
        table.insert(entries, {Text = "Install an AI Assistant", Icon = Icon,
            Subtext = "Install an assistant before choosing a default",
            Actions = {open = quote(paths.code("walker/bin/walker")) .. " --provider menus:ai-install"}})
    end
    if localState == "ready" then
        table.insert(options, {i18n.mark("Ratatoskr (local, experimental)"), "local", "󰒋",
            i18n.mark("Runs only on this PC; less reliable than cloud assistants")})
    else
        table.insert(entries, {Text = "Ratatoskr (local, experimental)", Icon = "󰒋",
            Subtext = "Set up an assistant that runs only on this PC",
            Actions = {open = task("setup-local")}})
    end
    for _, entry in ipairs(choices(script, "assistant", options)) do table.insert(entries, entry) end
    if localState ~= "none" then
        for _, entry in ipairs(entries) do
            if entry.Value == "local" or entry.Text == "Ratatoskr (local, experimental)" then
                entry.Actions.ai_local_delete = task("remove-local")
            end
        end
    end
    return i18n.entries(entries, false)
end

GetEntries = dofile(paths.code("elephant/live-menu.lua"))(Name, GetEntries)

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
local choices = dofile(paths.code("elephant/choice-entries.lua"))
Name = "assistant-access"
NamePretty = i18n.tr("Assistant Access")
Parent = "security"
Icon = "󰒃"
FixedOrder = true
function GetEntries()
    return i18n.entries(choices(paths.code("walker/scripts/actions/ai-assistant.py"), "access", {
        {i18n.mark("Full access (default)"), "full", Icon, i18n.mark("Allow file changes and commands without asking")},
        {i18n.mark("Ask before changes"), "ask", Icon, i18n.mark("Use the assistant's normal permission prompts")},
    }), false)
end

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local i18n = dofile(paths.code("elephant/i18n.lua"))
-- Saved dashboards come from walker/scripts/actions/development/monitoring.py
-- (machine-local); Delete removes one. Amazon Managed Grafana is in
-- Cloud > AWS > an account, beside the other AWS tools.
Name = "monitoring"
NamePretty = i18n.tr("Monitoring")
Parent = "development"
Icon = "\243\176\168\135"
FixedOrder = true

local quote = dofile(paths.code("elephant/shell-quote.lua"))
local helper = paths.code("walker/scripts/actions/development/monitoring.py")
local presenter = paths.code("walker/scripts/actions/task-terminal.py")

function GetEntries()
    local entries = {
        {Text = "Monitoring Tools", Icon = "\239\144\165", State = {"submenu"}, SubMenu = "monitoring-tools"},
        {Text = "Add Dashboard", Subtext = "Grafana, Datadog, Sentry, New Relic, Prometheus or any address",
            Icon = "\243\176\144\149",
            Actions = {open = "kitty --class eitr-software -e python3 " .. quote(presenter) .. " python3 " .. quote(helper) .. " add"}},
    }
    local handle = io.popen("python3 " .. quote(helper) .. " list")
    if not handle then return entries end
    local ok, rows = pcall(jsonDecode, handle:read("*a"))
    handle:close()
    for _, row in ipairs(ok and rows or {}) do
        table.insert(entries, {Text = row.name, Subtext = i18n.tr("{service} · {url}", {service = row.label, url = row.url}), Value = row.id, Icon = row.icon,
            Actions = {open = "python3 " .. quote(helper) .. " open " .. quote(row.id),
                dashboard_remove = "python3 " .. quote(helper) .. " remove " .. quote(row.id)}})
    end
    return entries
end

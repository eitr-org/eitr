-- Common row presentation for browsing and prepared search results. Actions and
-- navigation belong to the caller: search activates a provider, browsing its row.
return function(row)
    local submenu = row.subtext == ">"
    return {Text = row.text, Subtext = not submenu and row.subtext or nil,
        State = submenu and {"submenu"} or nil, Keywords = row.keywords,
        Icon = row.icon}
end

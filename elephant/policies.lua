if rawget(_G, "EitrPolicies") then return EitrPolicies end
local module = {}
local plugin_menus = {plugins = true, ['plugins-install'] = true, ['plugin-actions'] = true, ['plugin-visuals'] = true}
local software_groups = {'gaming', 'media', 'development', 'sharing', 'accessories'}

local loaded, policies = false, nil
local function load()
    if loaded then return end
    loaded = true
    local handle = io.open('/etc/eitr/policies.json', 'r')
    if not handle then policies = {}; return end
    local raw = handle:read('*a')
    handle:close()
    local ok, result = pcall(jsonDecode, raw)
    if ok and type(result) == 'table' then policies = result end
end

function module.allowed(feature)
    load()
    if not policies then return false end
    return policies[feature] ~= false and not (feature == 'update_channel' and policies[feature] == 'stable')
end

function module.row(entry, menu)
    local scope = (entry.SubMenu or '') .. ' ' .. (menu or '') .. ' ' .. (entry.Provider or '')
    for _, command in pairs(entry.Actions or {}) do scope = scope .. ' ' .. command end
    if not module.allowed('sharing') and (entry.SubMenu == 'share' or menu == 'share' or scope:find('localsend') or scope:find('kdeconnect')) then return false end
    if not module.allowed('gaming') and scope:find('game%-mode') then return false end
    if not module.allowed('remote_access') and (scope:find('remote%-') or scope:find('gaming moonlight')) then return false end
    if not module.allowed('assistants_together') and (scope:find('assistant%-collaboration.py') or entry.Text == 'Let assistants work together') then return false end
    if not module.allowed('update_channel') and (scope:find('update%-channel') or scope:find('channel%-set')) then return false end
    if not module.allowed('plugins') and (plugin_menus[entry.SubMenu or ''] or plugin_menus[menu or ''] or scope:find('install/plugins.py', 1, true)) then return false end
    for _, group in ipairs(software_groups) do
        if not module.allowed(group) and (entry.SubMenu == group or menu == group or scope:find('software.py ' .. group, 1, true)) then return false end
    end
    return true
end

function module.filter(entries, menu)
    local filtered = {}
    for _, entry in ipairs(entries) do
        if module.row(entry, menu) then table.insert(filtered, entry) end
    end
    return filtered
end

EitrPolicies = module
return module

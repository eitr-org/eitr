-- Numbered workspaces follow the Monitors preference (Shared numbers or Split across monitors).
-- workspaces.py writes eitr/workspaces.lua: the monitor rules and the plan these keys read,
-- so a key press dispatches directly. It reconciles the plan at start, on reload and on
-- monitor changes.
return function(paths, quote)
    local helper = "python3 " .. quote(paths.code("quickshell/desktop-bar/scripts/workspaces.py"))
    local plan = {rows = {}}
    local generated = loadfile(paths.config .. "/eitr/workspaces.lua")
    if generated then
        local valid, loaded = pcall(generated)
        if valid and type(loaded) == "table" and type(loaded.rows) == "table" then plan = loaded end
    end
    local function reconcile() hl.exec_cmd(helper .. " reconcile") end
    hl.on("monitor.added", reconcile)
    hl.on("monitor.removed", reconcile)
    hl.on("config.reloaded", reconcile)
    reconcile()

    -- Focus mode arranges its own tabs; numbered workspace keys do nothing there.
    local function focus_mode()
        local handle = io.open(paths.config .. "/eitr/focus.json", "r")
        if not handle then return false end
        local text = handle:read("*a") or ""
        handle:close()
        return text:match('"enabled"%s*:%s*true') ~= nil
    end

    local function monitor_name(monitor) return monitor and monitor.name or "" end

    local function rows_on(name)
        local found = {}
        for _, row in ipairs(plan.rows) do
            if row.monitor == name then table.insert(found, row) end
        end
        return found
    end

    local function focus(number)
        if #plan.rows == 0 then return hl.dispatch(hl.dsp.focus({workspace = number})) end
        if number > (plan.count or 10) then return end
        local current = monitor_name(hl.get_active_monitor())
        local targets = {}
        for _, row in ipairs(plan.rows) do
            if row.number == number then table.insert(targets, row) end
        end
        -- In Shared numbers every monitor switches; the starting monitor goes last so it keeps focus.
        table.sort(targets, function(left, right)
            return (left.monitor ~= current and 0 or 1) < (right.monitor ~= current and 0 or 1)
        end)
        for _, target in ipairs(targets) do
            hl.dispatch(hl.dsp.focus({monitor = target.monitor}))
            hl.dispatch(hl.dsp.focus({workspace = target.id}))
        end
    end

    local function move(number)
        if #plan.rows == 0 then return hl.dispatch(hl.dsp.window.move({workspace = number})) end
        if number > (plan.count or 10) then return end
        local window = hl.get_active_window()
        local name = monitor_name(window and window.monitor or hl.get_active_monitor())
        local candidates = plan.mode == "shared" and rows_on(name) or plan.rows
        for _, row in ipairs(candidates) do
            if row.number == number then
                hl.dispatch(hl.dsp.window.move({workspace = row.id}))
                -- In Shared numbers the other monitors follow to the same number too.
                if plan.mode == "shared" then focus(number) end
                return
            end
        end
    end

    local function step(offset)
        local monitor = hl.get_active_monitor()
        local local_rows = rows_on(monitor_name(monitor))
        if #local_rows == 0 then return hl.dispatch(hl.dsp.focus({workspace = offset > 0 and "e+1" or "e-1"})) end
        local existing = {}
        for _, workspace in ipairs(hl.get_workspaces()) do existing[workspace.id] = true end
        local open = {}
        for _, row in ipairs(local_rows) do
            if existing[row.id] then table.insert(open, row) end
        end
        if #open == 0 then return end
        local active = monitor and monitor.active_workspace and monitor.active_workspace.id
        local position = 1
        for index, row in ipairs(open) do
            if row.id == active then position = index end
        end
        local target = open[((position - 1 + offset) % #open) + 1]
        hl.dispatch(hl.dsp.focus({workspace = target.id}))
    end

    local actions = {focus = focus, move = move, step = step}
    return function(action, value)
        return function()
            if focus_mode() then return end
            actions[action](value)
        end
    end
end

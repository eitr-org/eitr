-- Native groups are the pane targets; this layout keeps them in a bounded grid.
return function(paths, quote)
    local helper = "python3 " .. quote(paths.code("quickshell/desktop-bar/scripts/focus-mode.py"))
    local reader = io.popen(helper .. " status")
    local enabled = reader and reader:read("*l") == "on"
    if reader then reader:close() end
    if not enabled then return false end

    local layouts = {}
    local function settings(ctx)
        local window = ctx.targets[1] and ctx.targets[1].window
        local key = window and window.workspace and window.workspace.name or ""
        if not layouts[key] then layouts[key] = {vertical = false, x = 0.5, y = 0.5} end
        return layouts[key]
    end
    hl.layout.register("eitr-focus", {
        recalculate = function(ctx)
            local count = #ctx.targets
            local style = settings(ctx)
            local area = ctx.area
            for index, target in ipairs(ctx.targets) do
                local box = {x = area.x, y = area.y, w = area.w, h = area.h}
                if count == 2 then
                    if style.vertical then
                        box.y = area.y + (index == 1 and 0 or area.h * style.y)
                        box.h = area.h * (index == 1 and style.y or 1 - style.y)
                    else
                        box.x = area.x + (index == 1 and 0 or area.w * style.x)
                        box.w = area.w * (index == 1 and style.x or 1 - style.x)
                    end
                elseif count > 2 then
                    local right = index % 2 == 0
                    local bottom = index > 2
                    box.x = area.x + (right and area.w * style.x or 0)
                    box.y = area.y + (bottom and area.h * style.y or 0)
                    box.w = area.w * (right and 1 - style.x or style.x)
                    box.h = area.h * (bottom and 1 - style.y or style.y)
                    if count == 3 and index == 3 then box.w = area.w end
                end
                target:place(box)
            end
        end,
        layout_msg = function(ctx, message)
            local style = settings(ctx)
            local active = hl.get_active_window()
            local index = 1
            for position, target in ipairs(ctx.targets) do
                if target.window and active and target.window.address == active.address then index = position end
            end
            local horizontal = index % 2 == 0 and -1 or 1
            local vertical = (#ctx.targets == 2 and index == 2 or #ctx.targets > 2 and index > 2) and -1 or 1
            if message == "horizontal" or message == "vertical" then
                style.vertical = message == "vertical"
            elseif message == "narrower" then style.x = math.max(0.2, math.min(0.8, style.x - 0.03 * horizontal))
            elseif message == "wider" then style.x = math.max(0.2, math.min(0.8, style.x + 0.03 * horizontal))
            elseif message == "shorter" then style.y = math.max(0.2, math.min(0.8, style.y - 0.03 * vertical))
            elseif message == "taller" then style.y = math.max(0.2, math.min(0.8, style.y + 0.03 * vertical))
            end
        end,
    })
    local install_bindings
    local function apply_options()
        hl.config({
            general = {gaps_in = 0, gaps_out = 0, border_size = 0, layout = "lua:eitr-focus"},
            decoration = {rounding = 0, blur = {enabled = false}, shadow = {enabled = false}},
            animations = {enabled = false},
            group = {auto_group = true, group_on_movetoworkspace = false, groupbar = {enabled = false}},
        })
    end
    apply_options()
    hl.window_rule({name = "eitr-focus-windows", match = {class = ".*"}, float = false,
        rounding = 0, no_blur = true, no_shadow = true, suppress_event = "fullscreen"})
    -- This watcher belongs to Hyprland, so strip crashes cannot stop conversion.
    hl.on("config.reloaded", function()
        apply_options()
        install_bindings()
        hl.exec_cmd(helper .. " reconcile")
    end)
    hl.on("window.destroy", function() hl.exec_cmd(helper .. " reconcile") end)
    hl.on("window.open", function() hl.exec_cmd(helper .. " reconcile") end)
    hl.on("workspace.special_active", function(workspace)
        if workspace then hl.exec_cmd(helper .. " reconcile") end
    end)
    hl.on("monitor.added", function() hl.exec_cmd(helper .. " reconcile") end)
    hl.on("monitor.removed", function() hl.exec_cmd(helper .. " reconcile") end)
    hl.on("window.move_to_workspace", function(window, workspace)
        if workspace and not workspace.name:match("^eitr%-focus%-") then hl.exec_cmd(helper .. " reconcile") end
    end)
    hl.on("workspace.active", function(workspace)
        if workspace and not workspace.name:match("^eitr%-focus%-") then hl.exec_cmd(helper .. " reconcile") end
    end)
    install_bindings = function()
        local disabled = {"SUPER + T", "SUPER + CTRL + F", "SUPER + SHIFT + P", "SUPER + R", "SUPER + SHIFT + R",
            "SUPER + CTRL + u", "SUPER + CTRL + h", "SUPER + CTRL + j", "SUPER + CTRL + k", "SUPER + CTRL + l",
            "SUPER + S", "SUPER + SHIFT + S", "SUPER + CTRL + S", "SUPER + mouse_down", "SUPER + mouse_up",
            "SUPER + ALT + h", "SUPER + ALT + l", "SUPER + SHIFT + space", "SUPER + mouse:272", "SUPER + mouse:273", "SUPER + 0"}
        for _, key in ipairs(disabled) do hl.unbind(key) end
        for number = 0, 9 do hl.unbind("SUPER + SHIFT + " .. number) end
        local generated = io.popen(helper .. " bindings")
        if not generated then error("Cannot generate Focus bindings") end
        local source = generated:read("*a")
        local success = generated:close()
        if not success then error("Cannot read Focus bindings") end
        assert(load(source, "Focus bindings"))()
    end
    return install_bindings
end

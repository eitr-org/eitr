-- Cleaning mode: an empty submap keeps all compositor shortcuts disabled,
-- leaving only a 3-second Escape hold and a 5-minute safety timeout to exit.
return function(paths, quote)
	local stop_command = "python3 " .. quote(paths.code("quickshell/desktop-bar/scripts/clean-mode.py")) .. " stop"
	local exit_hold_ms = 3000
	local safety_limit_ms = 300000

	local hold_timer
	local safety_timer

	local function set_timer(timer, enabled, timeout_ms)
		if not timer then
			return
		end
		if timeout_ms and timer.set_timeout then
			timer:set_timeout(timeout_ms)
		end
		timer:set_enabled(enabled)
	end

	local function exit_clean_mode()
		set_timer(hold_timer, false)
		set_timer(safety_timer, false)
		if hl.get_current_submap() == "clean" then
			hl.dispatch(hl.dsp.submap("reset"))
		end
		hl.exec_cmd(stop_command)
	end

	hold_timer = hl.timer(exit_clean_mode, { timeout = exit_hold_ms, type = "oneshot" })
	set_timer(hold_timer, false)

	safety_timer = hl.timer(exit_clean_mode, { timeout = safety_limit_ms, type = "oneshot" })
	set_timer(safety_timer, false)

	hl.on("keybinds.submap", function(submap)
		set_timer(hold_timer, false)
		if submap == "clean" then
			set_timer(safety_timer, true, safety_limit_ms)
		else
			set_timer(safety_timer, false)
		end
	end)

	hl.define_submap("clean", function()
		hl.bind("Escape", function()
			if hl.get_current_submap() == "clean" and hold_timer and not hold_timer:is_enabled() then
				set_timer(hold_timer, true, exit_hold_ms)
			end
		end, { locked = true, ignore_mods = true, non_consuming = true })

		hl.bind("Escape", function()
			set_timer(hold_timer, false)
		end, { release = true, locked = true, ignore_mods = true, non_consuming = true })
	end)

	hl.layer_rule({ match = { namespace = "desktop-clean" }, blur = true })
	hl.layer_rule({ match = { namespace = "desktop-clean" }, ignore_alpha = 0.2 })
end

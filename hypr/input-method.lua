-- Optional CJK input method (fcitx5): set session environment and autostart
-- in a uwsm app scope only when fcitx5 is installed.
-- GTK apps use the Wayland text-input protocol; GTK_IM_MODULE stays unset.
return function(paths, quote)
	local function find_binary(name)
		local path = os.getenv("PATH") or "/usr/local/bin:/usr/bin:/bin"
		for dir in path:gmatch("[^:]+") do
			if dir ~= "" then
				local candidate = dir .. "/" .. name
				local handle = io.open(candidate, "rb")
				if handle then
					local byte = handle:read(1)
					handle:close()
					if byte ~= nil then
						return candidate
					end
				end
			end
		end
		return nil
	end

	if not find_binary("fcitx5") then
		return false
	end

	hl.env("XMODIFIERS", "@im=fcitx")
	hl.env("QT_IM_MODULE", "fcitx")
	hl.on("hyprland.start", function()
		hl.exec_cmd(quote(paths.code("walker/bin/app-launch")) .. " fcitx5 -d")
	end)
	return true
end

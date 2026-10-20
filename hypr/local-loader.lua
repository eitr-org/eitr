local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
-- ~/.config/hypr/local.lua is an optional, uncommitted Lua chunk for one machine.
-- It runs after the shared config and uses the same hl.* calls (hl.monitor,
-- hl.workspace_rule, hl.device, hl.env, hl.config, ...), so its settings win.
-- Its hl.* calls are queued and applied only after the whole file succeeds; on
-- any error the generic layout above stays in effect and the error is reported.
-- See hypr/local.lua.example in the Eitr repository.

local function report_config_error(message)
	io.stderr:write("eitr: " .. message .. "\n")
	local function quote(value)
		return "'" .. value:gsub("'", "'\\''") .. "'"
	end
	local notifier = paths.code("hypr/scripts/notify-config-error.sh")
	os.execute(quote(notifier) .. " " .. quote(message) .. " >/dev/null 2>&1 &")
end

local function load_local_config(path)
	local label = path:match("[^/]+$") or path
	local file = io.open(path, "r")
	if not file then
		return
	end
	file:close()

	local queued = {}
	local queued_hl = setmetatable({}, {
		__index = function(_, key)
			local value = hl[key]
			if type(value) ~= "function" then
				return value
			end
			return function(...)
				table.insert(queued, { name = key, count = select("#", ...), args = { ... } })
			end
		end,
	})
	local environment = setmetatable({ hl = queued_hl }, { __index = _G })

	local chunk, load_error = loadfile(path, "t", environment)
	if not chunk then
		report_config_error(label .. " was not applied: " .. tostring(load_error))
		return
	end
	local ok, run_error = pcall(chunk)
	if not ok then
		report_config_error(label .. " was not applied: " .. tostring(run_error))
		return
	end

	local unpack_args = table.unpack or unpack
	for _, call in ipairs(queued) do
		local applied, apply_error = pcall(hl[call.name], unpack_args(call.args, 1, call.count))
		if not applied then
			report_config_error(label .. " hl." .. call.name .. " failed: " .. tostring(apply_error))
		end
	end
end

-- displays.lua is written by the Display panel's settings (display-settings.py);
-- local.lua comes after it, so hand-written monitors win.
load_local_config(paths.config .. "/hypr/displays.lua")
load_local_config(paths.config .. "/hypr/local.lua")

local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local keybinds = dofile(paths.code("hypr/keybind-overrides.lua"))(paths)
local bind_key = keybinds.bind
-------------
-- Themes --
-------------

local function trim(value)
	return value:gsub("^%s+", ""):gsub("%s+$", "")
end

local function load_theme_env(path)
	local file = io.open(path, "r")
	if not file then
		return
	end

	for line in file:lines() do
		local cleaned = trim(line:gsub("#.*$", ""))

		local key, value = cleaned:match("^env%s*=%s*([^,]+)%s*,%s*(.+)$")

		if key and value then
			hl.env(trim(key), trim(value))
		end
	end

	file:close()
end

load_theme_env(paths.code("hypr/theme-env.conf"))
load_theme_env(paths.config .. "/hypr/theme-env.conf")

-- Window rounding for the chosen corner style, defined in corner-styles.json.
local function read_file(path)
	local file = io.open(path, "r")
	if not file then
		return nil
	end
	local text = file:read("*a")
	file:close()
	return text
end

local gaps_inner, gaps_outer = 6, 12
local gaps_loader = loadfile(paths.config .. "/eitr/window-gaps.lua")
if gaps_loader then
	local valid, gaps = pcall(gaps_loader)
	if valid and type(gaps) == "table" and type(gaps.inner) == "number" and type(gaps.outer) == "number"
		and gaps.inner >= 0 and gaps.outer >= 0 then
		gaps_inner, gaps_outer = gaps.inner, gaps.outer
	end
end

local window_layout = {layout = "dwindle", direction = "right", column_width = 0.5,
	focus_fit_method = 1, follow_focus = 1, fullscreen_on_one_column = true,
	explicit_column_widths = "0.333, 0.5, 0.667, 1.0"}
local layout_loader = loadfile(paths.config .. "/eitr/window-layout.lua")
if layout_loader then
	local valid, saved = pcall(layout_loader)
	if valid and type(saved) == "table" then
		for key, default in pairs(window_layout) do
			if type(saved[key]) == type(default) then window_layout[key] = saved[key] end
		end
	end
end
if window_layout.layout ~= "scrolling" then window_layout.layout = "dwindle" end

local window_rounding = nil
local corner_styles = read_file(paths.code("quickshell/desktop-bar/corner-styles.json"))
if corner_styles then
	local preference = read_file(os.getenv("HOME") .. "/.config/eitr/style.json") or ""
	local function rounding(style)
		return style and corner_styles:match('"' .. style:gsub("%-", "%%-") .. '"%s*:%s*{[^}]-"windowRounding"%s*:%s*(%d+)')
	end
	local chosen = rounding(preference:match('"corners"%s*:%s*"([%w-]+)"'))
		or rounding(corner_styles:match('"default"%s*:%s*"([%w-]+)"'))
	window_rounding = tonumber(chosen)
end

local active_border_color = "rgba(33ccffee)"
local palette_file = io.open(os.getenv("HOME") .. "/.config/theme/current/colors.toml", "r")
if palette_file then
	for line in palette_file:lines() do
		local accent = line:match('^%s*accent%s*=%s*"#(%x%x%x%x%x%x)"')
		if accent then
			active_border_color = "rgba(" .. accent .. "ee)"
			break
		end
	end
	palette_file:close()
end

--------------
-- Monitors --
--------------

-- Generic layout: every display uses its preferred EDID mode and is positioned
-- automatically. Machine-specific outputs belong in ~/.config/hypr/local.lua.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

--------------
-- Commands --
--------------

local shellQuote = dofile(paths.code("elephant/shell-quote.lua"))
local appLaunch = shellQuote(paths.code("walker/bin/app-launch")) .. " "
local terminal = appLaunch .. "--terminal"
local fileManager = appLaunch .. "dolphin"
local mainMod = "SUPER"
local workspace_action = dofile(paths.code("hypr/workspaces.lua"))(paths, shellQuote)

local scriptsDir = paths.code("walker/scripts")
local menusDir = scriptsDir .. "/menus"
local actionsDir = scriptsDir .. "/actions"
local hyprScriptsDir = paths.code("hypr/scripts")

---------------
-- Autostart --
---------------

hl.on("hyprland.start", function()
	hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")
	-- The bar is the polkit agent; session-start.sh falls back to KDE's when it is not.
	hl.exec_cmd("bash " .. hyprScriptsDir .. "/session-start.sh")
	hl.exec_cmd("eitr-hypridle")
end)

-----------------
-- Environment --
-----------------

hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
load_theme_env(os.getenv("HOME") .. "/.config/hypr/cursor-env.conf")
hl.env("XDG_MENU_PREFIX", "arch-")
hl.env("_JAVA_AWT_WM_NONREPARENTING", "1")

-------------------
-- Look And Feel --
-------------------

hl.config({
	ecosystem = {
		no_update_news = true,
	},
	render = {
		cm_enabled = true,
		send_content_type = true,
		cm_auto_hdr = 2,
		direct_scanout = 2,
		use_fp16 = 2,
	},
	quirks = {
		prefer_hdr = 2,
	},
	general = {
		gaps_in = gaps_inner,
		gaps_out = gaps_outer,
		border_size = 2,
		col = {
			active_border = {
				colors = {
					active_border_color,
				},
				angle = 45,
			},
			inactive_border = "rgba(595959aa)",
		},
		resize_on_border = false,
		allow_tearing = false,
		layout = window_layout.layout,
	},
	scrolling = {
		direction = window_layout.direction,
		column_width = window_layout.column_width,
		focus_fit_method = window_layout.focus_fit_method,
		follow_focus = window_layout.follow_focus,
		fullscreen_on_one_column = window_layout.fullscreen_on_one_column,
		explicit_column_widths = window_layout.explicit_column_widths,
	},
	decoration = {
		rounding = window_rounding,
		rounding_power = 4,
		active_opacity = 1.0,
		inactive_opacity = 1.0,
		shadow = {
			enabled = true,
			range = 4,
			render_power = 3,
			color = "rgba(1a1a1aee)",
		},
		blur = {
			enabled = true,
			size = 3,
			passes = 2,
			vibrancy = 0.2,
		},
	},
	animations = {
		enabled = true,
	},
})

hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
hl.curve("easeInOutCubic", { type = "bezier", points = { { 0.65, 0.05 }, { 0.36, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("almostLinear", { type = "bezier", points = { { 0.5, 0.5 }, { 0.75, 1 } } })
hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

hl.animation({ leaf = "global", enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "border", enabled = true, speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows", enabled = true, speed = 4.79, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.1, bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.49, bezier = "linear", style = "popin 87%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade", enabled = true, speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers", enabled = true, speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.5, bezier = "linear", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces", enabled = false, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesIn", enabled = false, speed = 1.21, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesOut", enabled = false, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "zoomFactor", enabled = true, speed = 7, bezier = "quick" })

hl.config({
	dwindle = {
		preserve_split = true,
	},
	master = {
		new_status = "master",
	},
	scrolling = {
		fullscreen_on_one_column = true,
	},
	misc = {
		focus_on_activate = true,
		disable_hyprland_logo = true,
		disable_splash_rendering = true,
		force_default_wallpaper = -1,
		-- Lets launch.sh hand a crashed Quickshell lock over to Hyprlock.
		allow_session_lock_restore = true,
	},
})

local focus_bindings = dofile(paths.code("hypr/focus.lua"))(paths, shellQuote, keybinds)

-----------
-- Input --
-----------

local keyboard_ok, keyboard_layouts = pcall(dofile, os.getenv("HOME") .. "/.config/hypr/keyboard-layouts.lua")
if not keyboard_ok or type(keyboard_layouts) ~= "table" then
	keyboard_layouts = { layout = "us,us", variant = ",intl" }
end

-- Mouse and touchpad choices from Settings > Input; a missing file keeps these defaults.
local pointer_ok, pointer = pcall(dofile, os.getenv("HOME") .. "/.config/hypr/pointer.lua")
if not pointer_ok or type(pointer) ~= "table" then
	pointer = {}
end
local function pointer_setting(name, default)
	local value = pointer[name]
	if type(value) == type(default) then
		return value
	end
	return default
end

-- Acceleration on leaves the device's own profile (Hyprland refuses an empty one).
local accel_profile = nil
if not pointer_setting("acceleration", true) then
	accel_profile = "flat"
end

hl.config({
	input = {
		sensitivity = math.max(-1, math.min(1, pointer_setting("sensitivity", 0))),
		accel_profile = accel_profile,
		natural_scroll = pointer_setting("natural_scroll", false),
		left_handed = pointer_setting("left_handed", false),
		follow_mouse = 1,
		kb_model = "",
		kb_rules = "",
		kb_layout = keyboard_layouts.layout,
		kb_variant = keyboard_layouts.variant,
		kb_options = "grp:alt_shift_toggle",
		touchpad = {
			natural_scroll = pointer_setting("touchpad_natural_scroll", false),
			tap_to_click = pointer_setting("tap_to_click", true),
			disable_while_typing = pointer_setting("disable_while_typing", true),
		},
	},
})

-- Focus mode has tabs instead of workspace gestures.
if not focus_bindings then
    for _, swipe in ipairs({{direction = "left", step = 1}, {direction = "right", step = -1}}) do
        hl.gesture({fingers = 3, direction = swipe.direction,
            action = function() hl.dispatch(workspace_action("step", swipe.step)) end})
    end
end

-- hl.gesture({
--   fingers = 4,
--   direction = "horizontal",
--   action = "scroll_move",
--   scale = 1.0,
-- })

-----------------
-- Keybindings --
-----------------

-- Launchers and app helpers
bind_key(mainMod .. " + return", hl.dsp.exec_cmd(terminal))
bind_key(mainMod .. " + CTRL + return", hl.dsp.exec_cmd(appLaunch .. "--terminal -e tmux new-session -A -s main"))
bind_key(mainMod .. " + E", hl.dsp.exec_cmd(fileManager .. " --new-window"))
bind_key(
	mainMod .. " + P",
	hl.dsp.exec_cmd(appLaunch .. [[kitty --class fif-terminal -e python3 "/usr/share/eitr/walker/scripts/actions/task-terminal.py" zsh -c 'source ~/.zshrc; fif']])
)
bind_key(
	mainMod .. " + CTRL + P",
	hl.dsp.exec_cmd(appLaunch .. [[kitty --class fifs-terminal -e python3 "/usr/share/eitr/walker/scripts/actions/task-terminal.py" zsh -c 'source ~/.zshrc; fifs; exit 0']])
)
bind_key(mainMod .. " + C", hl.dsp.exec_cmd("sleep 0.08; wtype -M ctrl c -m ctrl"))
bind_key(mainMod .. " + X", hl.dsp.exec_cmd("sleep 0.08; wtype -M ctrl x -m ctrl"))
bind_key(mainMod .. " + V", hl.dsp.exec_cmd("sleep 0.08; wtype -M ctrl v -m ctrl"))
bind_key(
	mainMod .. " + CTRL + V",
	hl.dsp.exec_cmd(
		"/usr/share/eitr/walker/bin/walker --provider menus:clipboard --width 850"
	)
)

-- Window state and layout
bind_key(mainMod .. " + W", hl.dsp.window.close())
-- Intentional pair: SUPER+T toggles floating and pin together (see Learn > Shortcuts).
bind_key(mainMod .. " + T", hl.dsp.window.float({ action = "toggle" }))
bind_key(mainMod .. " + T", hl.dsp.window.pin())
bind_key(mainMod .. " + CTRL + F", hl.dsp.window.fullscreen())
bind_key(mainMod .. " + SHIFT + P", hl.dsp.window.pseudo())
bind_key(mainMod .. " + A", hl.dsp.exec_cmd("python3 /usr/share/eitr/walker/scripts/actions/ai-assistant.py open"))
bind_key(mainMod .. " + R", hl.dsp.layout("togglesplit"))
bind_key(mainMod .. " + SHIFT + R", hl.dsp.layout("rotatesplit"))

-- Focus with vim-style keys
bind_key(mainMod .. " + h", hl.dsp.focus({ direction = "l" }))
bind_key(mainMod .. " + j", hl.dsp.focus({ direction = "d" }))
bind_key(mainMod .. " + k", hl.dsp.focus({ direction = "u" }))
bind_key(mainMod .. " + l", hl.dsp.focus({ direction = "r" }))

-- Scrolling-only actions, registered only while the scrolling layout is chosen.
if window_layout.layout == "scrolling" then
	bind_key(mainMod .. " + ALT + Left", hl.dsp.layout("focus l"))
	bind_key(mainMod .. " + ALT + Right", hl.dsp.layout("focus r"))
	bind_key(mainMod .. " + ALT + Up", hl.dsp.layout("focus u"))
	bind_key(mainMod .. " + ALT + Down", hl.dsp.layout("focus d"))
	bind_key(mainMod .. " + ALT + SHIFT + Left", hl.dsp.layout("swapcol l"))
	bind_key(mainMod .. " + ALT + SHIFT + Right", hl.dsp.layout("swapcol r"))
	bind_key(mainMod .. " + ALT + equal", hl.dsp.layout("colresize +conf"))
	bind_key(mainMod .. " + ALT + minus", hl.dsp.layout("colresize -conf"))
end

-- Resize active window
bind_key(mainMod .. " + SHIFT + h", hl.dsp.window.resize({ x = -15, y = 0, relative = true }), { repeating = true })
bind_key(mainMod .. " + SHIFT + j", hl.dsp.window.resize({ x = 0, y = 15, relative = true }), { repeating = true })
bind_key(mainMod .. " + SHIFT + k", hl.dsp.window.resize({ x = 0, y = -15, relative = true }), { repeating = true })
bind_key(mainMod .. " + SHIFT + l", hl.dsp.window.resize({ x = 15, y = 0, relative = true }), { repeating = true })
bind_key(mainMod .. " + CTRL + u", hl.dsp.exec_cmd(hyprScriptsDir .. "/window-size-cycle.sh"))

-- Move active window
bind_key(mainMod .. " + CTRL + h", hl.dsp.window.move({ direction = "l" }))
bind_key(mainMod .. " + CTRL + j", hl.dsp.window.move({ direction = "d" }))
bind_key(mainMod .. " + CTRL + k", hl.dsp.window.move({ direction = "u" }))
bind_key(mainMod .. " + CTRL + l", hl.dsp.window.move({ direction = "r" }))

-- Desktop panels and Focus
bind_key(mainMod .. " + TAB", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- panels show overview"))
bind_key(mainMod .. " + SHIFT + F", hl.dsp.exec_cmd("eitr focus toggle"))
bind_key(mainMod .. " + SHIFT + A", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- panels show volume"))
bind_key(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- panels show bluetooth"))
bind_key(mainMod .. " + SHIFT + C", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- panels show calendar"))
bind_key(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- panels show wifi"))
bind_key(mainMod .. " + SHIFT + M", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- panels show display"))
-- Numbered navigation uses the saved monitor mode, count and marker floor.
for i = 1, 10 do
	local key = tostring(i % 10)
	bind_key(mainMod .. " + " .. key, workspace_action("focus", i))
	bind_key(mainMod .. " + SHIFT + " .. key, workspace_action("move", i))
end

-- Special workspace
bind_key(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
bind_key(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))
bind_key(mainMod .. " + CTRL + S", workspace_action("move", 1))

-- Scroll through existing workspaces
hl.bind(mainMod .. " + mouse_down", workspace_action("step", 1))
hl.bind(mainMod .. " + mouse_up", workspace_action("step", -1))
bind_key(mainMod .. " + ALT + h", workspace_action("step", -1))
bind_key(mainMod .. " + ALT + l", workspace_action("step", 1))

-- Walker menus and scripts
bind_key(mainMod .. " + space", hl.dsp.exec_cmd(menusDir .. "/search.sh"))
bind_key(mainMod .. " + slash", hl.dsp.exec_cmd(menusDir .. "/shortcuts.sh"))
bind_key(mainMod .. " + SHIFT + slash", hl.dsp.exec_cmd(menusDir .. "/vim.sh"))
bind_key(mainMod .. " + F", hl.dsp.exec_cmd("/usr/share/eitr/walker/bin/walker --provider menus:main"))
bind_key(mainMod .. " + CTRL + N", hl.dsp.exec_cmd("bash /usr/share/eitr/quickshell/desktop-bar/scripts/appearance-picker.sh wallpaper"))
bind_key(mainMod .. " + CTRL + SHIFT + N", hl.dsp.exec_cmd("bash /usr/share/eitr/quickshell/desktop-bar/scripts/appearance-picker.sh theme"))
bind_key(mainMod .. " + G", hl.dsp.exec_cmd(actionsDir .. "/search/google.sh"))

bind_key("PRINT", hl.dsp.exec_cmd(actionsDir .. "/capture/screenshot-full.sh"))
bind_key(mainMod .. " + PRINT", hl.dsp.exec_cmd(actionsDir .. "/capture/screenshot-selection.sh"))
bind_key(mainMod .. " + SHIFT + PRINT", hl.dsp.exec_cmd(actionsDir .. "/capture/screenshot.sh window edit"))
bind_key(mainMod .. " + CTRL + PRINT", hl.dsp.exec_cmd(actionsDir .. "/capture/text.sh"))
bind_key(mainMod .. " + ALT + PRINT", hl.dsp.exec_cmd(actionsDir .. "/capture/qr.sh"))
bind_key(mainMod .. " + SHIFT + N", hl.dsp.exec_cmd(actionsDir .. "/wallpaper/next.sh"))
bind_key(mainMod .. " + SHIFT + space", hl.dsp.exec_cmd(actionsDir .. "/toggle/desktop-bar.sh autohide"))

-- Desktop utilities
bind_key(mainMod .. " + F1", hl.dsp.exec_cmd("bash /usr/share/eitr/quickshell/desktop-bar/scripts/handbook.sh toggle"))
bind_key(mainMod .. " + F2", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- catalog toggle"))
bind_key(mainMod .. " + comma", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- settings toggle"))
bind_key(mainMod .. " + I", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- controlCenter toggle"))
bind_key(mainMod .. " + N", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- notifications toggle"))
bind_key(mainMod .. " + ALT + N", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- notifications act"))
bind_key(mainMod .. " + ALT + SHIFT + N", hl.dsp.exec_cmd("eitr-shell desktop-bar ipc call -- notifications dismissNewest"))
bind_key(mainMod .. " + equal", hl.dsp.exec_cmd("hyprpicker -a"))
bind_key(mainMod .. " + m", hl.dsp.exec_cmd(hyprScriptsDir .. "/manual-lock.sh"))
bind_key(mainMod .. " + SEMICOLON", hl.dsp.exec_cmd(actionsDir .. "/emoji-picker.sh"))

-- Media keys
bind_key("F8", hl.dsp.exec_cmd("playerctl play-pause"))
bind_key("F9", hl.dsp.exec_cmd("playerctl next"))

-- Hardware keys
bind_key(
	"XF86AudioRaiseVolume",
	hl.dsp.exec_cmd("swayosd-client --output-volume=2 --max-volume=100"),
	{ locked = true, repeating = true }
)
bind_key(
	"XF86AudioLowerVolume",
	hl.dsp.exec_cmd("swayosd-client --output-volume=-2 --max-volume=100"),
	{ locked = true, repeating = true }
)
bind_key(
	"XF86AudioMute",
	hl.dsp.exec_cmd("swayosd-client --output-volume=mute-toggle --max-volume=100"),
	{ locked = true }
)
bind_key(
	"XF86AudioMicMute",
	hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),
	{ locked = true }
)
bind_key("XF86Calculator", hl.dsp.exec_cmd(paths.code("walker/scripts/actions/tools/calculator.sh")))
-- Offline dictation: hold to speak, release to type (whisper-cpp ships with every installation).
bind_key(mainMod .. " + D", hl.dsp.exec_cmd(paths.code("walker/scripts/actions/tools/dictate.sh") .. " start"))
bind_key(mainMod .. " + SHIFT + D", hl.dsp.exec_cmd("python3 " .. paths.code("walker/scripts/actions/tools/voice-command.py") .. " start"))
-- D release stops either mode even after SUPER/SHIFT is released; ordinary D input passes through.
bind_key("D", hl.dsp.exec_cmd(paths.code("walker/scripts/actions/tools/dictate.sh") .. " stop; " .. paths.code("walker/scripts/actions/tools/dictate.sh") .. " stop voice"), { release = true, ignore_mods = true, non_consuming = true })
-- Keyboard backlight keys do nothing on keyboards without a light.
bind_key("XF86KbdBrightnessUp", hl.dsp.exec_cmd("brightnessctl --device='*::kbd_backlight' set +33%"), { locked = true })
bind_key("XF86KbdBrightnessDown", hl.dsp.exec_cmd("brightnessctl --device='*::kbd_backlight' set 33%-"), { locked = true })
-- Lid with an external monitor: the laptop screen turns off (hypr/scripts/lid.sh; experimental).
hl.bind("switch:on:Lid Switch", hl.dsp.exec_cmd(paths.code("hypr/scripts/lid.sh") .. " close"), { locked = true })
hl.bind("switch:off:Lid Switch", hl.dsp.exec_cmd(paths.code("hypr/scripts/lid.sh") .. " open"), { locked = true })
bind_key("XF86MonBrightnessUp", hl.dsp.exec_cmd("swayosd-client --brightness +2"), { locked = true, repeating = true })
bind_key("XF86MonBrightnessDown", hl.dsp.exec_cmd("swayosd-client --brightness -2"), { locked = true, repeating = true })

bind_key("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
bind_key("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
bind_key("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
bind_key("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

-- Mouse window manipulation
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

----------------------------
-- Windows And Workspaces --
----------------------------

local function floating_window_rule(name, class, size, move)
	local rule = {
		name = name,
		match = { class = class },
		float = true,
		size = size,
	}

	if move == "top-right" then
		rule.move = { "monitor_w-" .. tostring(size[1]) .. "-10", "40" }
	elseif move == "top-center" then
		rule.move = { "monitor_w*0.5-" .. tostring(size[1] / 2), "40" }
	elseif move == "top-left" then
		rule.move = { "10", "40" }
	elseif move then
		rule.move = move
	else
		rule.center = true
	end

	hl.window_rule(rule)
end

local function opacity_rule(name, class, opacity)
	hl.window_rule({
		name = name,
		match = { class = class },
		opacity = opacity,
	})
end

local function blurred_layer(namespace, ignore_alpha)
	hl.layer_rule({ match = { namespace = namespace }, blur = true })
	hl.layer_rule({ match = { namespace = namespace }, ignore_alpha = ignore_alpha })
end

-- Browsers and their web apps follow each monitor's desktop HDR setting; games retain auto-HDR.
hl.window_rule({
	name = "browser-no-auto-hdr",
	match = { class = "(?i)^(google-chrome(-.*)?|chromium(-.*)?|brave-browser(-.*)?|firefox(-.*)?|microsoft-edge(-.*)?|vivaldi(-.*)?|tor-browser|org\\.mozilla\\.firefox|org\\.torproject\\.torbrowser|(chrome|brave|msedge|vivaldi)-.+)$" },
	no_auto_hdr = true,
})

-- Floating utility windows
local topRightPanelPosition = "top-right"

floating_window_rule("setup-wifi-float", "^(setup-wifi)$", { 700, 480 }, topRightPanelPosition)
hl.window_rule({ name = "eitr-calculator-float", match = { title = "^(Eitr Calculator)$" }, float = true, size = { 340, 540 } })
floating_window_rule("imv-float", "^(imv)$", { 1400, 850 })
floating_window_rule("screenshot-editor-float", "^(dev.local.ScreenshotEditor)$", { 1100, 720 })
floating_window_rule("fif-terminal-float", "^(fif-terminal)$", { 1000, 650 })
floating_window_rule("fifs-terminal-float", "^(fifs-terminal)$", { 1500, 800 })
floating_window_rule("cloud-terminal-float", "^(cloud-terminal)$", { 1700, 950 })
floating_window_rule("about-terminal-float", "^(about-terminal)$", { 1000, 600 })
-- Terminals opened from Walker menus (walker/bin/menu-path/kitty).
floating_window_rule("menu-terminal-float", "^(eitr-menu-terminal|eitr-cloud|eitr-git-accounts|eitr-software|eitr-plugins|system-cleanup|system-check|system-mirrors)$", { 1100, 700 })

-- GTK portal dialogs share a class; the Eitr picture chooser has a stable title suffix.
hl.window_rule({
	name = "eitr-picture-chooser",
	match = { class = "^(xdg-desktop-portal-gtk)$", title = "^.* · Eitr$" },
	float = true,
	center = true,
	size = { 900, 640 },
	stay_focused = true,
})

-- Library windows restore their screen-bounded size.
hl.window_rule({
	name = "eitr-catalog",
	match = { class = "^(eitr-catalog)$" },
	float = true,
	center = true,
	opacity = "1 1",
	no_blur = true,
})

-- App opacity
opacity_rule("set-dolphin-transparency", "^(org.kde.dolphin)$", "1 0.94")
opacity_rule("set-google-chrome-transparency", "^(google-chrome)$", "1 0.96")
opacity_rule("set-vscode-transparency", "^(code)$", "1 0.94")

-- Focus behavior
hl.window_rule({
	name = "jetbrains-no-focus-steal",
	match = { class = "^(jetbrains-.*)$" },
	no_initial_focus = true,
})

hl.window_rule({
	name = "zoom-no-focus-steal",
	match = { class = "^(zoom)$" },
	no_initial_focus = true,
})

-- Ignore maximize requests from all apps
hl.window_rule({
	name = "suppress-maximize-events",
	match = { class = ".*" },
	suppress_event = "maximize",
})

-- Fix some dragging issues with XWayland
hl.window_rule({
	name = "fix-xwayland-drags",
	match = {
		class = "^$",
		title = "^$",
		xwayland = true,
		float = true,
		fullscreen = false,
		pin = false,
	},
	no_focus = true,
})

-- Hyprland-run launcher position
hl.window_rule({
	name = "move-hyprland-run",
	match = { class = "hyprland-run" },
	move = { "20", "monitor_h-120" },
	float = true,
})

-- Layer rules
blurred_layer("desktop-bar", 0.2)
blurred_layer("^eitr-plugin-widget$", 0.2)
hl.layer_rule({ match = { namespace = "desktop-bar" }, blur_popups = true })
hl.layer_rule({
	name = "walker-blur",
	match = { namespace = "walker" },
	blur = true,
	blur_popups = true,
	ignore_alpha = 0.8,
})
blurred_layer("desktop-notifications", 0.2)
blurred_layer("desktop-reload-error", 0.2)
blurred_layer("desktop-overview", 0.2)
-- The overview owns its preview animation; keep its blur and workspace jumps instant.
hl.layer_rule({ match = { namespace = "desktop-overview" }, no_anim = true })
-- The wallpaper reveal draws its own growing circle; a layer fade-in would hide it.
hl.layer_rule({ match = { namespace = "eitr-wallpaper-transition" }, no_anim = true })
blurred_layer("swayosd", 0.3)

------------------------------
-- Machine-Local Overrides --
------------------------------

if focus_bindings then focus_bindings() end

local personal_rules = loadfile(paths.config .. "/hypr/window-rules.lua")
if personal_rules then
    local valid, rules = pcall(personal_rules)
    if valid and type(rules) == "table" then
        for _, rule in ipairs(rules) do
            if type(rule) == "table" and type(rule.match) == "table" then
                pcall(hl.window_rule, rule)
            end
        end
    end
end

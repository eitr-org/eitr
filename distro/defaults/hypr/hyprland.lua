-- Package defaults stay upgradeable; machine settings run once, after defaults.
local root = "/usr/share/eitr"
assert(loadfile(root .. "/hypr/hyprland.lua"))()
assert(loadfile(root .. "/hypr/local-loader.lua"))()

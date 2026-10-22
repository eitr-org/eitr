local M = {}
local home = os.getenv("HOME")
local config = os.getenv("XDG_CONFIG_HOME")
if not config or config:sub(1, 1) ~= "/" then config = home .. "/.config" end
local data = os.getenv("XDG_DATA_HOME")
if not data or data:sub(1, 1) ~= "/" then data = home .. "/.local/share" end
M.root = os.getenv("EITR_CODE_ROOT") or "/usr/share/eitr"
M.config = config
-- The user's own themes, wallpapers and lockscreens (eitr_paths.own).
function M.own(kind) return data .. "/eitr/" .. kind end
function M.code(relative) return M.root .. "/" .. relative end
function M.themes()
    local directories = {}
    local handle = io.popen("eitr-paths themes")
    if not handle then return directories end
    for line in handle:lines() do
        local name, path = line:match("^([^\t]+)\t(.+)$")
        if name then directories[name] = path end
    end
    handle:close()
    return directories
end
return M

local M = {}
local timer
local last_content
local config_root = vim.fs.dirname(vim.fn.stdpath("config"))
local theme_file = config_root .. "/theme/current/neovim.lua"

local function read(path)
  local file = io.open(path, "r")
  if not file then return nil end
  local content = file:read("*a")
  file:close()
  return content
end

local function plugin_name(spec)
  return spec.name or (spec[1] or spec.dir):match("([^/]+)$"):gsub("%.git$", "")
end

-- Keep every bundled colorscheme available to lazy's colorscheme loader.
-- Only the selected theme supplies startup options; others stay lazy-loaded.
function M.specs()
  local ok, specs = pcall(dofile, theme_file)
  specs = ok and specs or {}
  local seen = {}
  for _, spec in ipairs(specs) do seen[plugin_name(spec)] = true end
  -- Bundled themes ship with the package; a home that has not adopted the
  -- package layout still keeps its own copies in ~/.config/themes.
  local shipped = (os.getenv("EITR_CODE_ROOT") or "/usr/share/eitr") .. "/themes/*/neovim.lua"
  local theme_files = vim.fn.glob(shipped, false, true)
  vim.list_extend(theme_files, vim.fn.glob(config_root .. "/themes/*/neovim.lua", false, true))
  for _, path in ipairs(theme_files) do
    local valid, entries = pcall(dofile, path)
    if valid then
      for _, spec in ipairs(entries) do
        local name = plugin_name(spec)
        if spec[1] ~= "LazyVim/LazyVim" and not seen[name] then
          table.insert(specs, { spec[1], name = name, branch = spec.branch, dir = spec.dir, main = spec.main, lazy = true })
          seen[name] = true
        end
      end
    end
  end
  return specs
end

function M.reload(force)
  local content = read(theme_file)
  -- Read the file anew, not its inode: the desktop swaps the entire directory.
  if not content or (content == last_content and force ~= true) then return end
  last_content = content
  local ok, error_message = pcall(function()
    local specs = dofile(theme_file)
    local scheme
    for _, spec in ipairs(specs) do
      if spec[1] == "LazyVim/LazyVim" then scheme = spec.opts.colorscheme end
    end
    assert(type(scheme) == "string", "Missing desktop colorscheme")
    local loader = require("lazy.core.loader")
    local plugins = require("lazy.core.config").plugins
    for _, spec in ipairs(specs) do
      if spec[1] ~= "LazyVim/LazyVim" then
        local name = plugin_name(spec)
        local plugin = plugins[name]
        if plugin then
          require("lazy").load({ plugins = { name } })
        else
          -- Sessions opened before this integration can use already-installed
          -- colorschemes without rebuilding lazy's registry or restarting.
          local directory = spec.dir or (vim.fn.stdpath("data") .. "/lazy/" .. name)
          assert(vim.fn.isdirectory(directory) == 1, "Theme plugin not installed: " .. name .. "; reopen Neovim once to install bundled themes")
          vim.opt.rtp:prepend(directory)
          plugin = { name = name, dir = directory }
        end
        local main = spec.main or loader.get_main(plugin)
        if main then
          local module = require(main)
          if module.setup then module.setup(spec.opts or {}) end
        end
      end
    end
    vim.cmd.colorscheme(scheme)
    vim.cmd.redraw()
  end)
  if not ok then vim.notify("Desktop theme reload failed: " .. tostring(error_message), vim.log.levels.WARN) end
end

function M.setup()
  if timer then timer:stop(); timer:close() end
  last_content = read(theme_file)
  timer = vim.uv.new_timer()
  timer:start(1000, 1000, vim.schedule_wrap(M.reload))
  local group = vim.api.nvim_create_augroup("eitr_desktop_theme", { clear = true })
  vim.api.nvim_create_autocmd("FocusGained", { group = group, callback = M.reload })
  vim.api.nvim_create_autocmd("VimLeavePre", { group = group, callback = function()
    timer:stop(); timer:close(); timer = nil
  end })
end

return M

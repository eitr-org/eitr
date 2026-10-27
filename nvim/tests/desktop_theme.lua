local root = vim.fs.dirname(vim.fn.stdpath("config"))
vim.fn.mkdir(root .. "/theme/current", "p")
vim.fn.mkdir(root .. "/themes/test-dark", "p")
vim.fn.mkdir(root .. "/themes/test-light", "p")
local function spec(scheme, value)
  return 'return {{"example/test.nvim", opts={value="' .. value .. '"}}, {"LazyVim/LazyVim", opts={colorscheme="' .. scheme .. '"}}}'
end
local function write(path, text) vim.fn.writefile({text}, path) end
write(root .. "/theme/current/neovim.lua", spec("habamax", "dark"))
write(root .. "/themes/test-dark/neovim.lua", spec("habamax", "dark"))
write(root .. "/themes/test-light/neovim.lua", 'return {{"example/light.nvim"}}')
-- Bundled themes ship in the package (EITR_CODE_ROOT), not in ~/.config/themes.
local code = os.getenv("EITR_CODE_ROOT")
vim.fn.mkdir(code .. "/themes/test-shipped", "p")
write(code .. "/themes/test-shipped/neovim.lua", 'return {{"example/shipped.nvim"}}')
local setup_value
package.loaded["test"] = { setup = function(opts) setup_value = opts.value end }
package.loaded["lazy"] = { load = function() end }
package.loaded["lazy.core.loader"] = { get_main = function() return "test" end }
package.loaded["lazy.core.config"] = { plugins = {["test.nvim"] = {}} }
local theme = dofile("nvim/lua/config/desktop_theme.lua")
local specs = theme.specs()
assert(#specs == 4, "Dormant theme plugins must be registered without duplicate specs")
assert(vim.iter(specs):any(function(item) return item.name == "shipped.nvim" end), "Shipped themes must be registered")
vim.api.nvim_buf_set_lines(0, 0, -1, false, {"unsaved work"})
local buffer = vim.api.nvim_get_current_buf()
theme.setup()
write(root .. "/theme/current/neovim.lua", spec("retrobox", "light"))
assert(vim.wait(2500, function() return vim.g.colors_name == "retrobox" end), "Timer must reload an open editor")
assert(setup_value == "light", "Theme options must be reapplied")
assert(vim.api.nvim_get_current_buf() == buffer and vim.bo.modified, "Reload must preserve unsaved buffers")
assert(vim.api.nvim_buf_get_lines(buffer, 0, -1, false)[1] == "unsaved work")
-- Simulate the atomic directory swap performed by the desktop switcher.
vim.fn.rename(root .. "/theme/current", root .. "/theme/previous")
theme.reload()
vim.fn.mkdir(root .. "/theme/current", "p")
write(root .. "/theme/current/neovim.lua", spec("habamax", "dark"))
theme.reload()
assert(vim.g.colors_name == "habamax" and setup_value == "dark")
local warnings = 0
vim.notify = function() warnings = warnings + 1 end
write(root .. "/theme/current/neovim.lua", "invalid lua!")
theme.reload(); theme.reload()
assert(warnings == 1, "Invalid theme must not repeatedly notify")
assert(vim.g.colors_name == "habamax", "Failed reload must retain the current scheme")
print("Desktop theme live reload tests passed")
vim.cmd("qa!")

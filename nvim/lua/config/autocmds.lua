-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

require("config.desktop_theme").setup()

local transparent_group = vim.api.nvim_create_augroup("user_transparent_background", { clear = true })

local function clear_bg(group)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  if not ok then
    return
  end

  hl.bg = nil
  hl.ctermbg = nil
  vim.api.nvim_set_hl(0, group, hl)
end

local function apply_transparent_background()
  for _, group in ipairs({
    "Normal",
    "NormalNC",
    "NormalFloat",
    "FloatBorder",
    "SignColumn",
    "FoldColumn",
    "LineNr",
    "CursorLineNr",
    "EndOfBuffer",
    "Pmenu",
    "Terminal",
    "TermNormal",
    "TermNormalNC",
    "SnacksNormal",
    "SnacksNormalNC",
    "SnacksDashboardNormal",
  }) do
    clear_bg(group)
  end
end

vim.api.nvim_create_autocmd({ "ColorScheme", "VimEnter" }, {
  group = transparent_group,
  callback = apply_transparent_background,
})

vim.api.nvim_create_autocmd("TermOpen", {
  group = transparent_group,
  callback = function()
    apply_transparent_background()
    vim.wo.winhighlight = "Normal:Normal,NormalNC:NormalNC,EndOfBuffer:EndOfBuffer"
  end,
})

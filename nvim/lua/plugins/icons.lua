local function icon(codepoint, color)
  return { glyph = vim.fn.nr2char(codepoint), hl = "MiniIcons" .. color }
end

local function apply_icon_colors()
  -- Catppuccin Mocha colors, independent of the editor colorscheme.
  local colors = {
    Azure = "#74c7ec",
    Blue = "#89b4fa",
    Cyan = "#94e2d5",
    Green = "#a6e3a1",
    Grey = "#cdd6f4",
    Orange = "#fab387",
    Purple = "#cba6f7",
    Red = "#f38ba8",
    Yellow = "#f9e2af",
  }
  for name, color in pairs(colors) do
    vim.api.nvim_set_hl(0, "MiniIcons" .. name, { fg = color })
  end
end

return {
  {
    "nvim-mini/mini.icons",
    config = function(_, opts)
      require("mini.icons").setup(opts)
      vim.api.nvim_create_autocmd("ColorScheme", {
        group = vim.api.nvim_create_augroup("user_icon_colors", { clear = true }),
        callback = apply_icon_colors,
      })
      apply_icon_colors()
    end,
    opts = {
      style = "glyph",
      default = {
        directory = icon(0xf024b, "Azure"),
        file = icon(0xf0214, "Grey"),
      },
      directory = {
        src = icon(0xf024b, "Azure"),
        components = icon(0xf024b, "Purple"),
        tests = icon(0xf024b, "Green"),
        docs = icon(0xf024b, "Yellow"),
      },
      file = {
        ["devcontainer.json"] = icon(0xf0868, "Azure"),
      },
      extension = {
        sh = icon(0xf018d, "Green"),
        bash = icon(0xf018d, "Green"),
        zsh = icon(0xf018d, "Green"),
        yaml = icon(0xf067b, "Purple"),
        yml = icon(0xf067b, "Purple"),
      },
      filetype = {
        sh = icon(0xf018d, "Green"),
        zsh = icon(0xf018d, "Green"),
        yaml = icon(0xf067b, "Purple"),
        dotenv = icon(0xf0493, "Yellow"),
      },
    },
  },
}

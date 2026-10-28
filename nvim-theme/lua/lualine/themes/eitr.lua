local colors = require("eitr_theme").palette()
local function section(accent)
  return {
    a = { fg = colors.bg, bg = accent, gui = "bold" },
    b = { fg = colors.fg, bg = colors.role_visual or colors.lighter_bg },
    c = { fg = colors.fg, bg = colors.role_surface or colors.dark_bg },
  }
end
return {
  normal = section(colors.accent), insert = section(colors.green),
  visual = section(colors.magenta), replace = section(colors.red),
  command = section(colors.yellow), inactive = section(colors.muted),
}

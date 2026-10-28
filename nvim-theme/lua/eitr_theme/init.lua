local M = {}
local defaults = {
	accent = "#b9d77e",
	background = "#000000",
	bg = "#000000",
	blue = "#8cafcb",
	bright_blue = "#a9c3d8",
	bright_cyan = "#a0d6cb",
	bright_fg = "#e9efe9",
	bright_green = "#a4d4b3",
	bright_magenta = "#c6b4d8",
	bright_red = "#d6999e",
	bright_yellow = "#e0d19e",
	brown = "#91a397",
	cursor = "#e2eae2",
	cyan = "#80c8ba",
	dark_bg = "#0b110e",
	dark_fg = "#91a397",
	darker_bg = "#000000",
	fg = "#e2eae2",
	foreground = "#e2eae2",
	green = "#85c69a",
	light_fg = "#e2eae2",
	lighter_bg = "#19251d",
	magenta = "#b39bcb",
	muted = "#91a397",
	orange = "#d5c27d",
	red = "#c9777d",
	selection = "#19251d",
	selection_background = "#19251d",
	selection_foreground = "#e2eae2",
	yellow = "#d5c27d",
}
local colors = vim.deepcopy(defaults)
local background = "dark"

function M.setup(opts)
  opts = opts or {}
  colors = vim.tbl_extend("force", defaults, opts.colors or {})
  for _, name in ipairs({ "red", "green", "yellow", "blue", "magenta", "cyan" }) do colors["ansi_" .. name] = colors[name] end
  for _, name in ipairs({ "accent", "second", "alert", "muted", "fg", "red", "green", "yellow", "blue", "magenta", "cyan" }) do
    colors[name] = colors["role_" .. name] or colors[name]
  end
  colors.second = colors.second or colors.cyan
  colors.alert = colors.alert or colors.red
  colors.dark_bg = colors.role_surface or colors.dark_bg
  colors.lighter_bg = colors.role_raised or colors.lighter_bg
  colors.selection_background = colors.role_visual or colors.selection_background
  colors.selection_foreground = colors.role_selection_text or colors.fg
  background = opts.background or "dark"
  assert(background == "dark" or background == "light", "Invalid Eitr background mode")
end

function M.palette()
  return vim.deepcopy(colors)
end

function M.apply()
  vim.o.termguicolors = true
  vim.o.background = background
  vim.cmd("highlight clear")
  if vim.g.syntax_on then vim.cmd("syntax reset") end
  vim.g.colors_name = "eitr"
  local function paint(names, style)
    for name in names:gmatch("%S+") do vim.api.nvim_set_hl(0, name, style) end
  end
  local function link(names, target) paint(names, { link = target }) end
  paint("Normal NormalNC", { fg = colors.fg, bg = colors.bg })
  paint("NormalFloat Pmenu", { fg = colors.fg, bg = colors.dark_bg })
  paint("FloatBorder WinSeparator", { fg = colors.muted, bg = colors.dark_bg })
  paint("CursorLine CursorColumn ColorColumn", { bg = colors.dark_bg })
  paint("LineNr SignColumn FoldColumn EndOfBuffer NonText Whitespace", { fg = colors.muted })
  paint("CursorLineNr", { fg = colors.accent, bold = true })
  paint("Cursor", { fg = colors.bg, bg = colors.cursor })
  paint("Visual PmenuSel", { fg = colors.selection_foreground, bg = colors.selection_background })
  paint("Search", { fg = colors.bg, bg = colors.yellow })
  paint("IncSearch CurSearch", { fg = colors.bg, bg = colors.accent, bold = true })
  paint("MatchParen", { fg = colors.accent, bg = colors.lighter_bg, bold = true })
  paint("StatusLine TabLineSel WinBar", { fg = colors.fg, bg = colors.lighter_bg, bold = true })
  paint("StatusLineNC TabLine TabLineFill WinBarNC Folded", { fg = colors.muted, bg = colors.dark_bg })
  paint("PmenuSbar", { bg = colors.lighter_bg })
  paint("PmenuThumb", { bg = colors.muted })
  paint("Directory Title MoreMsg Question", { fg = colors.accent })
  paint("ErrorMsg", { fg = colors.red })
  paint("WarningMsg", { fg = colors.yellow })
  paint("Comment", { fg = colors.muted, italic = true })
  paint("Constant Number Boolean Float", { fg = colors.orange })
  paint("String Character", { fg = colors.green })
  paint("Identifier", { fg = colors.fg })
  paint("Function", { fg = colors.blue })
  paint("Statement Conditional Repeat Label Keyword Exception", { fg = colors.magenta })
  paint("Operator Delimiter", { fg = colors.dark_fg })
  paint("PreProc Include Define Macro PreCondit", { fg = colors.cyan })
  paint("Type StorageClass Structure Typedef", { fg = colors.yellow })
  paint("Special SpecialChar Tag Debug", { fg = colors.cyan })
  paint("Underlined", { fg = colors.blue, underline = true })
  paint("Ignore Conceal", { fg = colors.muted })
  paint("Error", { fg = colors.red, bold = true })
  paint("Todo", { fg = colors.bg, bg = colors.yellow, bold = true })
  local function blend(foreground, backdrop, alpha)
    local channels = {}
    for offset = 2, 6, 2 do
      local front = tonumber(foreground:sub(offset, offset + 1), 16)
      local back = tonumber(backdrop:sub(offset, offset + 1), 16)
      channels[#channels + 1] = math.floor(front * alpha + back * (1 - alpha) + 0.5)
    end
    return string.format("#%02x%02x%02x", unpack(channels))
  end
  for kind, color in pairs({ Add = colors.green, Change = colors.blue, Delete = colors.red, Text = colors.yellow }) do
    paint("Diff" .. kind, { bg = blend(color, colors.bg, 0.18) })
  end
  for severity, color in pairs({ Error = colors.alert, Warn = colors.yellow, Info = colors.blue, Hint = colors.cyan, Ok = colors.green }) do
    paint("Diagnostic" .. severity .. " DiagnosticSign" .. severity .. " DiagnosticFloating" .. severity, { fg = color })
    paint("DiagnosticVirtualText" .. severity, { fg = color, bg = blend(color, colors.bg, 0.1) })
    paint("DiagnosticUnderline" .. severity, { sp = color, undercurl = true })
  end
  for spelling, color in pairs({ Bad = colors.red, Cap = colors.blue, Rare = colors.magenta, Local = colors.cyan }) do
    paint("Spell" .. spelling, { sp = color, undercurl = true })
  end
  local captures = {
    Comment = "comment comment.documentation", String = "string string.documentation character string.escape string.regexp markup.raw",
    Number = "number number.float boolean", Function = "function function.call function.method function.method.call constructor",
    Keyword = "keyword keyword.function keyword.return keyword.operator keyword.import keyword.repeat keyword.conditional keyword.exception keyword.directive",
    Type = "type type.builtin type.definition attribute", Identifier = "variable variable.member variable.parameter property",
    Constant = "constant constant.builtin constant.macro", Special = "function.builtin variable.builtin module module.builtin label tag tag.attribute",
    Delimiter = "punctuation.delimiter punctuation.bracket punctuation.special tag.delimiter", Operator = "operator",
    Title = "markup.heading", Underlined = "markup.link markup.link.url",
  }
  for target, names in pairs(captures) do
    for capture in names:gmatch("%S+") do link("@" .. capture, target) end
  end
  paint("@markup.strong", { bold = true })
  paint("@markup.italic", { italic = true })
  paint("@markup.strikethrough", { strikethrough = true })
  for token, target in pairs({ class = "Type", enum = "Type", interface = "Type", struct = "Type", type = "Type", typeParameter = "Type", parameter = "Identifier", variable = "Identifier", property = "Identifier", enumMember = "Constant", event = "Special", namespace = "Special", ["function"] = "Function", method = "Function", macro = "Macro", keyword = "Keyword", modifier = "Keyword", comment = "Comment", string = "String", number = "Number", regexp = "String", operator = "Operator", decorator = "Special" }) do
    link("@lsp.type." .. token, target)
  end
  link("@lsp.mod.readonly @lsp.mod.defaultLibrary", "Constant")
  local integrations = {
    NormalFloat = "SnacksNormal SnacksPicker SnacksPickerInput SnacksPickerList SnacksPickerPreview SnacksNotifierNormal NoiceCmdlinePopup NoicePopup TroubleNormal BlinkCmpMenu BlinkCmpDoc WhichKeyNormal",
    FloatBorder = "SnacksPickerBorder SnacksPickerInputBorder SnacksPickerListBorder SnacksPickerPreviewBorder SnacksNotifierBorder NoiceCmdlinePopupBorder NoicePopupBorder BlinkCmpMenuBorder BlinkCmpDocBorder WhichKeyBorder",
    Title = "SnacksDashboardHeader SnacksDashboardTitle SnacksPickerTitle NoiceCmdlineIcon WhichKeyGroup TroubleText",
    Comment = "SnacksDashboardFooter SnacksPickerComment SnacksPickerDir SnacksIndent SnacksIndentScope BlinkCmpLabelDescription BlinkCmpLabelDetail WhichKeySeparator WhichKeyDesc TroubleIndent BufferLineBackground",
    Directory = "SnacksExplorerDirectory SnacksPickerDirectory",
    Function = "SnacksDashboardKey SnacksDashboardIcon SnacksPickerFile BlinkCmpKindFunction WhichKeyValue TroubleCode",
    Search = "SnacksPickerMatch BlinkCmpLabelMatch NoiceSearch FlashMatch",
    Visual = "SnacksPickerListCursorLine BlinkCmpMenuSelection TroublePreview BufferLineBufferSelected",
    Normal = "BlinkCmpLabel BufferLineFill BufferLineBuffer",
    DiagnosticError = "SnacksNotifierError TroubleError BufferLineError",
    DiagnosticWarn = "SnacksNotifierWarn TroubleWarning BufferLineWarning",
    DiagnosticInfo = "SnacksNotifierInfo TroubleInformation BufferLineInfo",
    DiagnosticHint = "SnacksNotifierDebug SnacksNotifierTrace TroubleHint BufferLineHint",
    DiffAdd = "SnacksDiffAdd RenderMarkdownCode",
  }
  for target, names in pairs(integrations) do link(names, target) end
  paint("FlashLabel", { fg = colors.bg, bg = colors.magenta, bold = true })
  link("FlashBackdrop", "Comment")
  for kind, color in pairs({ Add = colors.green, Change = colors.blue, Delete = colors.red }) do
    paint("GitSigns" .. kind .. " GitSigns" .. kind .. "Nr", { fg = color })
    link("GitSigns" .. kind .. "Ln", "Diff" .. kind)
  end
  for name, color in pairs({ Red = colors.red, Orange = colors.orange, Yellow = colors.yellow, Green = colors.green, Cyan = colors.cyan, Blue = colors.blue, Violet = colors.magenta, Grey = colors.muted, Purple = colors.magenta }) do
    paint("MiniIcons" .. name .. " RainbowDelimiter" .. name, { fg = color })
  end
  for kind, color in pairs({ FIX = colors.red, TODO = colors.blue, HACK = colors.orange, WARN = colors.yellow, PERF = colors.magenta, NOTE = colors.cyan, TEST = colors.green }) do
    paint("TodoFg" .. kind .. " TodoSign" .. kind, { fg = color })
    paint("TodoBg" .. kind, { fg = colors.bg, bg = color, bold = true })
  end
  for index, color in ipairs({ colors.accent, colors.blue, colors.green, colors.yellow, colors.magenta, colors.cyan }) do
    paint("RenderMarkdownH" .. index, { fg = color, bold = true })
    paint("RenderMarkdownH" .. index .. "Bg", { bg = blend(color, colors.bg, 0.1) })
  end
  link("RenderMarkdownBullet RenderMarkdownQuote RenderMarkdownDash RenderMarkdownCodeInfo", "Special")
  link("RenderMarkdownLink RenderMarkdownWikiLink", "Underlined")
  link("RenderMarkdownChecked", "String")
  link("RenderMarkdownUnchecked", "Comment")
  local fallbacks = { keyword = colors.accent, ["function"] = colors.second, type = colors.yellow,
    string = colors.green, number = colors.magenta, constant = colors.alert, builtin = colors.cyan,
    property = colors.blue, parameter = colors.second, comment = colors.muted, line = colors.dark_bg,
    visual = colors.selection_background, search = colors.lighter_bg, selection_text = colors.fg }
  local function role(name) return colors["role_" .. name] or fallbacks[name] or colors.accent end
  paint("CursorLine CursorColumn ColorColumn", { bg = role("line") })
  paint("Search", { fg = role("selection_text"), bg = role("search") })
  paint("FloatBorder WinSeparator", { fg = colors.second, bg = colors.dark_bg })
  paint("SnacksDashboardHeader SnacksDashboardKey SnacksPickerMatch WhichKey WhichKeyGroup SnacksIndentScope", { fg = colors.accent, bold = true })
  paint("SnacksDashboardDesc SnacksDashboardIcon SnacksExplorerDirectory SnacksPickerDirectory SnacksExplorerDir SnacksPickerDir SnacksExplorerRoot SnacksPickerPathHidden", { fg = colors.second })
  paint("SnacksDashboardFooter", { fg = role("comment") })
  paint("SnacksPickerListCursorLine BufferLineBufferSelected BufferLineTabSelected TabLineSel", { fg = colors.accent, bg = role("visual"), bold = true })
  paint("SnacksPickerGitStatusAdded SnacksExplorerGitAdded", { fg = colors.green })
  paint("SnacksPickerGitStatusModified SnacksExplorerGitModified", { fg = colors.blue })
  paint("SnacksPickerGitStatusDeleted SnacksExplorerGitDeleted", { fg = colors.alert })
  for group, name in pairs({ Keyword = "keyword", Statement = "keyword", Function = "function", Type = "type", String = "string", Number = "number", Constant = "constant", Special = "builtin", Comment = "comment", Property = "property", Parameter = "parameter" }) do
    paint(group, { fg = role(name), italic = group == "Comment" })
  end
  link("Conditional Repeat Label Exception", "Keyword")
  link("StorageClass Structure Typedef", "Type")
  link("Character", "String")
  link("Float", "Number")
  link("Boolean", "Constant")
  link("@variable.member @property @lsp.type.property", "Property")
  link("@variable.parameter @lsp.type.parameter", "Parameter")
  link("@function.builtin @variable.builtin", "Special")
  link("WhichKeyDesc", "Function")
  local terminal = { colors.dark_bg, (colors.ansi_red or colors.red), (colors.ansi_green or colors.green), (colors.ansi_yellow or colors.yellow), (colors.ansi_blue or colors.blue), (colors.ansi_magenta or colors.magenta), (colors.ansi_cyan or colors.cyan), colors.light_fg, colors.muted, colors.bright_red, colors.bright_green, colors.bright_yellow, colors.bright_blue, colors.bright_magenta, colors.bright_cyan, colors.bright_fg }
  for index, color in ipairs(terminal) do vim.g["terminal_color_" .. (index - 1)] = colors["ansi_" .. (index - 1)] or color end
end

return M

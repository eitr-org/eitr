from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


class DesktopThemeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("nvim"), "Neovim is not installed")
    def test_live_reload_preserves_buffers_and_handles_directory_swaps(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["nvim", "--headless", "-u", "NONE", "-l", "nvim/tests/desktop_theme.lua"],
                cwd=root, env={**os.environ, "XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory, "EITR_CODE_ROOT": directory + "/code"},
                capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Desktop theme live reload tests passed", result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("nvim"), "Neovim is not installed")
    def test_original_colorscheme_and_generated_palettes(self):
        root = Path(__file__).resolve().parents[2]
        import json
        integrations = json.loads((root / "themes/integrations.json").read_text())
        themes = [name for name, entry in integrations.items() if entry["neovim"].get("eitr")]
        self.assertEqual(len(themes), 13)
        script = '''
vim.opt.rtp:prepend(os.getenv("EITR_CODE_ROOT") .. "/nvim-theme")
vim.cmd.colorscheme("eitr")
assert(vim.g.terminal_color_2 == "#85c69a")
local spec = dofile(os.getenv("EITR_CODE_ROOT") .. "/themes/" .. os.getenv("TEST_THEME") .. "/neovim.lua")[1]
assert(spec.dir == os.getenv("EITR_CODE_ROOT") .. "/nvim-theme")
assert(spec.main == "eitr_theme")
require(spec.main).setup(spec.opts)
vim.cmd.colorscheme("eitr")
assert(vim.o.background == spec.opts.background)
if os.getenv("TEST_THEME") == "daylight" then assert(vim.o.background == "light") end
local function hl(name) return vim.api.nvim_get_hl(0, {name=name, link=false}) end
local function hex(value) return tonumber(value:sub(2), 16) end
assert(hl("Normal").fg == hex(spec.opts.colors.role_fg))
assert(hl("@function").fg == hex(spec.opts.colors.role_function))
assert(hl("DiagnosticUnderlineError").sp == hex(spec.opts.colors.role_alert))
assert(hl("DiagnosticUnderlineError").undercurl)
assert(hl("SnacksPickerMatch").fg == hex(spec.opts.colors.role_accent))
for group, role in pairs({SnacksDashboardHeader="accent", SnacksDashboardKey="accent", SnacksDashboardIcon="second", SnacksDashboardDesc="second", SnacksDashboardFooter="comment", CursorLineNr="accent", SnacksIndentScope="accent"}) do
  assert(hl(group).fg == hex(spec.opts.colors["role_" .. role]), group)
end
assert(hl("CursorLine").bg == hex(spec.opts.colors.role_line))
assert(hl("Visual").bg == hex(spec.opts.colors.role_visual))
assert(hl("@variable.parameter").fg == hex(spec.opts.colors.role_parameter))
for index=0,15 do assert(vim.g["terminal_color_" .. index] == spec.opts.colors["ansi_" .. index]) end
assert(vim.g.terminal_color_1 == spec.opts.colors.red)
assert(require("lualine.themes.eitr").normal.a.bg == spec.opts.colors.role_accent)
require("eitr_theme").setup({background="light", colors={bg="#ffffff", fg="#111111"}})
vim.cmd.colorscheme("eitr")
assert(vim.o.background == "light")
assert(hl("Normal").bg == 0xffffff)
vim.cmd("qa!")
'''
        with tempfile.TemporaryDirectory() as directory:
            script_file = Path(directory) / "test.lua"
            script_file.write_text(script)
            for theme in themes:
                with self.subTest(theme=theme):
                    result = subprocess.run(["nvim", "--headless", "--clean", "-l", str(script_file)],
                        env={**os.environ, "EITR_CODE_ROOT": str(root), "TEST_THEME": theme,
                             "XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory},
                        capture_output=True, text=True, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

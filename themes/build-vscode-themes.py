#!/usr/bin/env python3
"""Build deterministic local VS Code themes; --check verifies all artifacts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tomllib
import zipfile

# Keep the themes folder free of a __pycache__ that would look like a theme.
sys.dont_write_bytecode = True
from editor_roles import roles, readable  # noqa: E402

THEMES = Path(__file__).resolve().parent


def theme(palette, display):
    r = roles(palette)
    BG, SURFACE, RAISED, BORDER = r['bg'], r['surface'], r['raised'], r['second']
    FG, MUTED, DIM = r['fg'], r['comment'], r['muted']
    ACCENT = palette['accent']
    ACCENT_TEXT = r['accent']
    GREEN, CYAN, MAGENTA, LIME = r['string'], r['builtin'], r['keyword'], r['number']
    BUTTON_TEXT = readable(BG, ACCENT)
    RED, AMBER, BLUE, SELECTION = r['alert'], r['type'], r['function'], r['visual']
    COLORS = {
        "focusBorder": ACCENT + "80", "foreground": FG, "descriptionForeground": MUTED, "errorForeground": RED,
        "widget.shadow": "#00000066", "selection.background": SELECTION,
        "editor.background": BG, "editor.foreground": FG, "editorCursor.foreground": ACCENT_TEXT,
        "editor.lineHighlightBackground": SURFACE, "editor.selectionBackground": SELECTION,
        "editor.inactiveSelectionBackground": SELECTION + "aa", "editor.findMatchBackground": LIME + "55",
        "editor.findMatchHighlightBackground": LIME + "33", "editor.wordHighlightBackground": CYAN + "26",
        "editorLineNumber.foreground": MUTED, "editorLineNumber.activeForeground": ACCENT_TEXT,
        "editorIndentGuide.background1": SURFACE, "editorIndentGuide.activeBackground1": BORDER,
        "editorWhitespace.foreground": BORDER, "editorBracketMatch.border": ACCENT + "88",
        "editorBracketHighlight.foreground1": CYAN, "editorBracketHighlight.foreground2": MAGENTA,
        "editorBracketHighlight.foreground3": LIME, "editorGutter.addedBackground": GREEN,
        "editorGutter.modifiedBackground": BLUE, "editorGutter.deletedBackground": RED,
        "editorError.foreground": RED, "editorWarning.foreground": AMBER, "editorInfo.foreground": CYAN,
        "editorWidget.background": SURFACE, "editorWidget.border": BORDER, "editorHoverWidget.background": SURFACE,
        "editorHoverWidget.border": BORDER, "editorSuggestWidget.background": SURFACE,
        "editorSuggestWidget.selectedBackground": RAISED, "editorSuggestWidget.highlightForeground": ACCENT_TEXT,
        "activityBar.background": BG, "activityBar.foreground": FG, "activityBar.inactiveForeground": DIM,
        "activityBarBadge.background": ACCENT, "activityBarBadge.foreground": BUTTON_TEXT, "activityBar.activeBorder": ACCENT,
        "sideBar.background": SURFACE, "sideBar.foreground": MUTED, "sideBar.border": BORDER,
        "sideBarTitle.foreground": FG, "sideBarSectionHeader.background": SURFACE,
        "sideBarSectionHeader.foreground": LIME, "list.activeSelectionBackground": RAISED,
        "list.activeSelectionForeground": FG, "list.inactiveSelectionBackground": SURFACE,
        "list.hoverBackground": SURFACE, "list.highlightForeground": ACCENT_TEXT, "list.focusOutline": ACCENT + "66",
        "titleBar.activeBackground": BG, "titleBar.activeForeground": MUTED,
        "titleBar.inactiveBackground": BG, "titleBar.inactiveForeground": DIM,
        "tab.activeBackground": BG, "tab.activeForeground": ACCENT_TEXT, "tab.inactiveBackground": SURFACE,
        "tab.inactiveForeground": DIM, "tab.activeBorderTop": ACCENT, "tab.border": BORDER,
        "editorGroupHeader.tabsBackground": SURFACE, "editorGroup.border": BORDER,
        "statusBar.background": RAISED, "statusBar.foreground": MUTED, "statusBar.border": BORDER,
        "statusBar.debuggingBackground": LIME, "statusBar.noFolderBackground": BG,
        "statusBarItem.remoteBackground": ACCENT, "statusBarItem.remoteForeground": BUTTON_TEXT,
        "panel.background": BG, "panel.border": BORDER, "panelTitle.activeBorder": ACCENT,
        "panelTitle.activeForeground": FG, "panelTitle.inactiveForeground": DIM,
        "terminal.background": BG, "terminal.foreground": FG, "terminalCursor.foreground": ACCENT_TEXT,
        "terminal.ansiBlack": SURFACE, "terminal.ansiRed": RED, "terminal.ansiGreen": GREEN,
        "terminal.ansiYellow": AMBER, "terminal.ansiBlue": BLUE, "terminal.ansiMagenta": MAGENTA,
        "terminal.ansiCyan": CYAN, "terminal.ansiWhite": FG, "terminal.ansiBrightBlack": MUTED,
        "terminal.ansiBrightRed": palette["color9"], "terminal.ansiBrightGreen": palette["color10"],
        "terminal.ansiBrightYellow": palette["color11"], "terminal.ansiBrightBlue": palette["color12"],
        "terminal.ansiBrightMagenta": palette["color13"], "terminal.ansiBrightCyan": palette["color14"],
        "terminal.ansiBrightWhite": r["parameter"],
        "input.background": SURFACE, "input.border": BORDER, "input.placeholderForeground": DIM,
        "dropdown.background": SURFACE, "dropdown.border": BORDER,
        "button.background": ACCENT, "button.foreground": BUTTON_TEXT, "button.hoverBackground": CYAN,
        "badge.background": ACCENT, "badge.foreground": BUTTON_TEXT, "progressBar.background": ACCENT,
        "scrollbarSlider.background": "#ffffff12", "scrollbarSlider.hoverBackground": "#ffffff1f",
        "scrollbarSlider.activeBackground": "#ffffff2b", "textLink.foreground": CYAN,
        "textLink.activeForeground": ACCENT_TEXT, "gitDecoration.addedResourceForeground": GREEN,
        "gitDecoration.modifiedResourceForeground": BLUE, "gitDecoration.deletedResourceForeground": RED,
        "gitDecoration.untrackedResourceForeground": CYAN, "gitDecoration.ignoredResourceForeground": DIM,
        "peekView.border": ACCENT, "peekViewEditor.background": SURFACE, "peekViewResult.background": SURFACE,
        "minimap.selectionHighlight": SELECTION, "breadcrumb.foreground": DIM, "breadcrumb.focusForeground": FG,
    }

    for index, name in enumerate(('Black', 'Red', 'Green', 'Yellow', 'Blue', 'Magenta', 'Cyan', 'White', 'BrightBlack', 'BrightRed', 'BrightGreen', 'BrightYellow', 'BrightBlue', 'BrightMagenta', 'BrightCyan', 'BrightWhite')):
        COLORS['terminal.ansi' + name] = palette['color' + str(index)]

    TOKENS = [
        (["support.function", "support.variable"], r["builtin"], ""),
        (["comment", "punctuation.definition.comment"], DIM, "italic"),
        (["keyword", "storage", "storage.type", "keyword.control"], r["keyword"], ""),
        (["keyword.operator", "punctuation"], MUTED, ""),
        (["string", "string.quoted", "markup.inline.raw"], GREEN, ""),
        (["constant.character.escape", "string.regexp"], CYAN, ""),
        (["constant.numeric"], r["number"], ""),
        (["constant.language", "constant.other", "support.constant"], r["constant"], ""),
        (["entity.name.function", "meta.function-call"], r["function"], ""),
        (["entity.name.type", "entity.name.class", "support.type", "support.class"], AMBER, ""),
        (["variable.parameter"], r["parameter"], "italic"),
        (["variable", "meta.definition.variable"], FG, ""),
        (["variable.other.property", "support.variable.property", "meta.object-literal.key"], r["property"], ""),
        (["entity.name.tag"], RED, ""),
        (["entity.other.attribute-name"], AMBER, "italic"),
        (["markup.heading", "entity.name.section"], LIME, "bold"),
        (["markup.bold"], FG, "bold"),
        (["markup.italic"], FG, "italic"),
        (["markup.underline.link", "string.other.link"], CYAN, ""),
        (["markup.inserted"], GREEN, ""),
        (["markup.deleted", "invalid"], RED, ""),
        (["markup.changed"], BLUE, ""),
    ]


    return {
        "name": display, "type": palette.get("mode", "dark"), "semanticHighlighting": True, "colors": COLORS,
        "semanticTokenColors": {name: r[role] for name, role in {"keyword": "keyword", "function": "function", "method": "function", "type": "type", "class": "type", "string": "string", "number": "number", "variable.readonly": "constant", "variable.defaultLibrary": "builtin", "function.defaultLibrary": "builtin", "property": "property", "parameter": "parameter", "comment": "comment"}.items()},
        "tokenColors": [{"scope": scopes, "settings": {"foreground": color, **({"fontStyle": style} if style else {})}}
                        for scopes, color, style in TOKENS],
    }



def archive(identifier, display, palette):
    document = theme(palette, display)
    version = '1.0.' + str(int(hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()[:8], 16))
    name = 'eitr-' + identifier + '-theme'
    package = {'name': name, 'publisher': 'local', 'version': version, 'displayName': display,
               'engines': {'vscode': '^1.70.0'}, 'categories': ['Themes'],
               'contributes': {'themes': [{'label': display, 'uiTheme': 'vs' if palette.get('mode') == 'light' else 'vs-dark', 'path': './themes/colors.json'}]}}
    manifest = f'<PackageManifest xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" Version="2.0.0"><Metadata><Identity Id="{name}" Version="{version}" Language="en-US" Publisher="local"/><DisplayName>{display}</DisplayName><Description>{display} palette</Description></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>'
    types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>'
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as bundle:
        for filename, data in [('extension.vsixmanifest', manifest), ('[Content_Types].xml', types), ('extension/package.json', json.dumps(package)), ('extension/themes/colors.json', json.dumps(document, indent=2))]:
            bundle.writestr(zipfile.ZipInfo(filename, (2026, 1, 1, 0, 0, 0)), data)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    arguments = parser.parse_args()
    integrations = json.loads((THEMES / 'integrations.json').read_text())
    stale = []
    for identifier, integration in integrations.items():
        if not integration['neovim'].get('eitr') or identifier in ('afterglow', 'wisteria'):
            continue
        directory = THEMES / identifier
        display = integration['vscode']['name']
        palette = tomllib.loads((directory / 'colors.toml').read_text())
        outputs = {'vscode.vsix': archive(identifier, display, palette), 'vscode.json': (json.dumps(integration['vscode'], indent=2, ensure_ascii=False) + '\n').encode()}
        for filename, data in outputs.items():
            path = directory / filename
            if arguments.check:
                if not path.exists() or path.read_bytes() != data:
                    stale.append(str(path.relative_to(THEMES)))
            else:
                path.write_bytes(data)
    if stale:
        raise SystemExit('Stale VS Code themes: ' + ', '.join(stale))


if __name__ == '__main__':
    main()

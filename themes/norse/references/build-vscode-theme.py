#!/usr/bin/env python3
"""Build ../vscode.vsix: the local Norse color theme for VS Code.

The palette matches ../colors.toml. Run after changing either file.
"""
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parent / "vscode.vsix"

BG, SURFACE, RAISED, BORDER = "#0a0b12", "#13141e", "#1a1b28", "#2a2c40"
FG, MUTED, DIM = "#e8ecf2", "#959bb0", "#666c85"
# ACCENT fills what is active or focused; ACCENT_TEXT is its readable shade for text and
# thin lines. GREEN is only for strings and additions.
ACCENT_TEXT = "#2bb87a"
ACCENT, GREEN, CYAN, MAGENTA, LIME = "#2bb87a", "#3fe39a", "#4fd2c0", "#e04fc3", "#c2ee5a"
RED, AMBER, BLUE, SELECTION = "#ff6b7a", "#c2ee5a", "#8a8cf5", "#1e3a32"

COLORS = {
    "focusBorder": ACCENT + "80", "foreground": FG, "descriptionForeground": MUTED, "errorForeground": RED,
    "widget.shadow": "#00000066", "selection.background": SELECTION,
    "editor.background": BG, "editor.foreground": FG, "editorCursor.foreground": ACCENT_TEXT,
    "editor.lineHighlightBackground": SURFACE, "editor.selectionBackground": SELECTION,
    "editor.inactiveSelectionBackground": SELECTION + "aa", "editor.findMatchBackground": LIME + "55",
    "editor.findMatchHighlightBackground": LIME + "33", "editor.wordHighlightBackground": CYAN + "26",
    "editorLineNumber.foreground": "#454a63", "editorLineNumber.activeForeground": MUTED,
    "editorIndentGuide.background1": "#1a1b28", "editorIndentGuide.activeBackground1": "#2e3046",
    "editorWhitespace.foreground": "#2a2c40", "editorBracketMatch.border": ACCENT + "88",
    "editorBracketHighlight.foreground1": CYAN, "editorBracketHighlight.foreground2": MAGENTA,
    "editorBracketHighlight.foreground3": LIME, "editorGutter.addedBackground": GREEN,
    "editorGutter.modifiedBackground": BLUE, "editorGutter.deletedBackground": RED,
    "editorError.foreground": RED, "editorWarning.foreground": AMBER, "editorInfo.foreground": CYAN,
    "editorWidget.background": SURFACE, "editorWidget.border": BORDER, "editorHoverWidget.background": SURFACE,
    "editorHoverWidget.border": BORDER, "editorSuggestWidget.background": SURFACE,
    "editorSuggestWidget.selectedBackground": RAISED, "editorSuggestWidget.highlightForeground": ACCENT_TEXT,
    "activityBar.background": "#06070c", "activityBar.foreground": FG, "activityBar.inactiveForeground": DIM,
    "activityBarBadge.background": ACCENT, "activityBarBadge.foreground": BG, "activityBar.activeBorder": ACCENT,
    "sideBar.background": "#0d0e16", "sideBar.foreground": MUTED, "sideBar.border": BORDER,
    "sideBarTitle.foreground": FG, "sideBarSectionHeader.background": "#0d0e16",
    "sideBarSectionHeader.foreground": LIME, "list.activeSelectionBackground": RAISED,
    "list.activeSelectionForeground": FG, "list.inactiveSelectionBackground": SURFACE,
    "list.hoverBackground": SURFACE, "list.highlightForeground": ACCENT_TEXT, "list.focusOutline": ACCENT + "66",
    "titleBar.activeBackground": "#06070c", "titleBar.activeForeground": MUTED,
    "titleBar.inactiveBackground": "#06070c", "titleBar.inactiveForeground": DIM,
    "tab.activeBackground": BG, "tab.activeForeground": FG, "tab.inactiveBackground": "#0d0e16",
    "tab.inactiveForeground": DIM, "tab.activeBorderTop": ACCENT, "tab.border": BORDER,
    "editorGroupHeader.tabsBackground": "#0d0e16", "editorGroup.border": BORDER,
    "statusBar.background": "#06070c", "statusBar.foreground": MUTED, "statusBar.border": BORDER,
    "statusBar.debuggingBackground": LIME, "statusBar.noFolderBackground": "#06070c",
    "statusBarItem.remoteBackground": ACCENT, "statusBarItem.remoteForeground": BG,
    "panel.background": BG, "panel.border": BORDER, "panelTitle.activeBorder": ACCENT,
    "panelTitle.activeForeground": FG, "panelTitle.inactiveForeground": DIM,
    "terminal.background": BG, "terminal.foreground": FG, "terminalCursor.foreground": ACCENT_TEXT,
    "terminal.ansiBlack": "#1a1b28", "terminal.ansiRed": RED, "terminal.ansiGreen": GREEN,
    "terminal.ansiYellow": AMBER, "terminal.ansiBlue": BLUE, "terminal.ansiMagenta": MAGENTA,
    "terminal.ansiCyan": CYAN, "terminal.ansiWhite": "#c9cfdb", "terminal.ansiBrightBlack": "#454a63",
    "terminal.ansiBrightRed": "#ff8f9a", "terminal.ansiBrightGreen": "#7ff0bd",
    "terminal.ansiBrightYellow": "#d8f58a", "terminal.ansiBrightBlue": "#aaacff",
    "terminal.ansiBrightMagenta": "#f08bd8", "terminal.ansiBrightCyan": "#86e6d8",
    "terminal.ansiBrightWhite": "#f4f6fa",
    "input.background": SURFACE, "input.border": BORDER, "input.placeholderForeground": DIM,
    "dropdown.background": SURFACE, "dropdown.border": BORDER,
    "button.background": ACCENT, "button.foreground": BG, "button.hoverBackground": "#3fe39a",
    "badge.background": ACCENT, "badge.foreground": BG, "progressBar.background": ACCENT,
    "scrollbarSlider.background": "#ffffff12", "scrollbarSlider.hoverBackground": "#ffffff1f",
    "scrollbarSlider.activeBackground": "#ffffff2b", "textLink.foreground": CYAN,
    "textLink.activeForeground": ACCENT_TEXT, "gitDecoration.addedResourceForeground": GREEN,
    "gitDecoration.modifiedResourceForeground": BLUE, "gitDecoration.deletedResourceForeground": RED,
    "gitDecoration.untrackedResourceForeground": CYAN, "gitDecoration.ignoredResourceForeground": DIM,
    "peekView.border": ACCENT, "peekViewEditor.background": SURFACE, "peekViewResult.background": "#0d0e16",
    "minimap.selectionHighlight": SELECTION, "breadcrumb.foreground": DIM, "breadcrumb.focusForeground": FG,
}

TOKENS = [
    (["comment", "punctuation.definition.comment"], DIM, "italic"),
    (["keyword", "storage", "storage.type", "keyword.control"], MAGENTA, ""),
    (["keyword.operator", "punctuation"], MUTED, ""),
    (["string", "string.quoted", "markup.inline.raw"], GREEN, ""),
    (["constant.character.escape", "string.regexp"], CYAN, ""),
    (["constant.numeric", "constant.language", "constant.other", "support.constant"], LIME, ""),
    (["entity.name.function", "support.function", "meta.function-call"], BLUE, ""),
    (["entity.name.type", "entity.name.class", "support.type", "support.class"], AMBER, ""),
    (["variable.parameter"], "#f4f6fa", "italic"),
    (["variable", "meta.definition.variable"], FG, ""),
    (["variable.other.property", "support.variable.property", "meta.object-literal.key"], CYAN, ""),
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


def theme():
    return {
        "name": "Norse", "type": "dark", "semanticHighlighting": True, "colors": COLORS,
        "tokenColors": [{"scope": scopes, "settings": {"foreground": color, **({"fontStyle": style} if style else {})}}
                        for scopes, color, style in TOKENS],
    }


def main():
    package = {"name": "norse-theme", "publisher": "local", "version": "1.0.0", "displayName": "Norse",
               "engines": {"vscode": "^1.70.0"}, "categories": ["Themes"],
               "contributes": {"themes": [{"label": "Norse", "uiTheme": "vs-dark", "path": "./themes/colors.json"}]}}
    manifest = ('<PackageManifest xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" Version="2.0.0">'
                '<Metadata><Identity Id="norse-theme" Version="1.0.0" Language="en-US" Publisher="local" />'
                '<DisplayName>Norse</DisplayName><Description xml:space="preserve">Norse color theme for ACCENT'
                '</Description></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code" />'
                '</Installation><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" '
                'Path="extension/package.json" Addressable="true" /></Assets></PackageManifest>')
    content_types = ('<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/'
                     'package/2006/content-types"><Default Extension=".json" ContentType="application/json" />'
                     '<Default Extension=".vsixmanifest" ContentType="text/xml" /></Types>')
    # A fixed timestamp keeps rebuilds byte-identical.
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in (("extension.vsixmanifest", manifest), ("[Content_Types].xml", content_types),
                           ("extension/package.json", json.dumps(package)),
                           ("extension/themes/colors.json", json.dumps(theme(), indent=2))):
            archive.writestr(zipfile.ZipInfo(name, (2026, 10, 14, 0, 0, 0)), data)
    print(OUTPUT.name)


if __name__ == "__main__":
    main()

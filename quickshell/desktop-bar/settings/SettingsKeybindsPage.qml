import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Wayland
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "KeyCapture.js" as KeyCapture

Column {
    id: pageBody
    objectName: "editor-keybinds"
    property alias editorHelper: editor
    required property var context
    readonly property var view: context
    property string editing: ""
    // While a shortcut is captured, Hyprland passes every key to this window, so a
    // combination it already binds (SUPER + W closes the window) reaches the page.
    ShortcutInhibitor {
        window: pageBody.QsWindow.window
        enabled: pageBody.editing !== "" && !!pageBody.QsWindow.window
    }
    property string proposed: ""
    property var clash: null
    property var pending: []
    readonly property var matches: editor.summary.items.filter(entry => [entry.group, entry.title, entry.default, entry.effective || ""].join(" ").toLocaleLowerCase().includes(view.shortcutQuery.trim().toLocaleLowerCase()))
    width: parent ? parent.width : 0
    spacing: 12
    function apply(arguments) { editing = ""; clash = null; editor.change(arguments); }
    SettingsHelper {
        id: editor
        active: view.active && view.page === "keybinds"
        live: view.live
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/keybinds.py")
        schema: ({items: "array"})
        summary: ({items: []})
    }
    Row {
        width: parent.width; spacing: 12
        PanelTextField {
            SettingsTarget { objectName: "setting-keybinds-search-shortcuts" }
            onTextChanged: view.shortcutQuery = text
            width: parent.width - (resetAll.visible ? resetAll.width + 12 : 0)
            placeholderText: Eitr.I18n.tr("Search shortcuts")
            foreground: view.foreground; accent: view.accent
        }
        PanelButton {
            id: resetAll; visible: editor.summary.items.some(entry => entry.changed)
            width: 120; foreground: view.foreground; text: Eitr.I18n.tr("Reset all"); enabled: !editor.busy
            onClicked: { pageBody.pending = ["reset-all"]; confirm.title = Eitr.I18n.tr("Reset all"); confirm.open(); }
        }
    }
    SettingsText { visible: editor.error !== ""; text: editor.error }
    SettingsText { visible: pageBody.matches.length === 0; text: Eitr.I18n.tr("No matching shortcuts") }
    Repeater {
        model: pageBody.matches
        Rectangle {
            id: shortcut
            required property var modelData
            readonly property bool capturing: pageBody.editing === modelData.default
            width: parent.width; height: body.implicitHeight + 24
            radius: DesktopStyle.radius(8)
            color: Qt.alpha(view.foreground, 0.04)
            border.width: 1; border.color: capturing ? view.accent : Qt.alpha(view.foreground, 0.15)
            Column {
                id: body; x: 12; y: 12; width: parent.width - 24; spacing: 6
                Row {
                    width: parent.width; spacing: 6
                    Text {
                        width: parent.width - chip.width - actions.width - 12; anchors.verticalCenter: parent.verticalCenter
                        text: shortcut.modelData.title; color: view.foreground; font.family: DesktopFonts.family; font.pixelSize: 13; elide: Text.ElideRight
                    }
                    Rectangle {
                        id: chip; width: Math.min(chipLabel.implicitWidth + 16, parent.width * (shortcut.capturing ? 0.68 : 0.45)); height: 26
                        radius: DesktopStyle.radius(4); color: Qt.alpha(view.foreground, 0.08)
                        Text { id: chipLabel; anchors.fill: parent; anchors.margins: 4; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; font.family: DesktopFonts.family; font.pixelSize: shortcut.capturing ? 11 : 12; color: shortcut.capturing ? view.accent : view.foreground
                            text: shortcut.capturing ? Eitr.I18n.tr("Press the new shortcut · Esc cancels · Backspace disables") : shortcut.modelData.effective || Eitr.I18n.tr("Disabled")
                        }
                    }
                    Row {
                        id: actions; spacing: 6
                        PanelButton {
                            id: editButton; width: 24; height: 24; icon: true; iconSize: 14; foreground: view.foreground
                            text: "\uf040"; Accessible.name: Eitr.I18n.tr("Edit"); enabled: !shortcut.modelData.protected && !editor.busy
                            onClicked: { pageBody.editing = shortcut.modelData.default; pageBody.clash = null; capture.forceActiveFocus(); }
                            HoverHandler { id: editHover }
                            BarTooltip { target: editButton; hovered: editHover.hovered; text: Eitr.I18n.tr("Edit"); foreground: view.foreground; background: view.background }
                        }
                        PanelButton {
                            id: resetButton; visible: shortcut.modelData.changed; width: 24; height: 24; icon: true; iconSize: 14; foreground: view.foreground
                            text: "\uf0e2"; Accessible.name: Eitr.I18n.tr("Reset"); enabled: !editor.busy
                            onClicked: pageBody.apply(["reset", shortcut.modelData.default])
                            HoverHandler { id: resetHover }
                            BarTooltip { target: resetButton; hovered: resetHover.hovered; text: Eitr.I18n.tr("Reset"); foreground: view.foreground; background: view.background }
                        }
                    }
                }
                SettingsText { visible: shortcut.modelData.changed; text: Eitr.I18n.tr("Default: %1").arg(shortcut.modelData.default) }
                Column {
                    id: capture
                    visible: pageBody.editing === shortcut.modelData.default
                    width: parent.width; spacing: 8
                    Keys.onPressed: event => {
                        event.accepted = true;
                        if (event.isAutoRepeat) return;
                        if (event.key === Qt.Key_Escape) { pageBody.editing = ""; return; }
                        if (event.key === Qt.Key_Backspace) {
                            pageBody.pending = ["disable", pageBody.editing];
                            confirm.title = Eitr.I18n.tr("Disable shortcut"); confirm.open(); return;
                        }
                        const key = KeyCapture.combination(event);
                        if (!key) return;
                        pageBody.proposed = key;
                        pageBody.clash = editor.summary.items.find(entry => entry.default !== pageBody.editing && entry.effective === key) || null;
                        if (!pageBody.clash) pageBody.apply(["set", pageBody.editing, key]);
                    }
                    SettingsText {
                        visible: pageBody.clash !== null
                        text: pageBody.clash ? Eitr.I18n.tr("%1 is used by %2").arg(pageBody.proposed).arg(pageBody.clash.title) : ""
                    }
                    Row {
                        visible: pageBody.clash !== null; spacing: 8
                        PanelButton { width: 110; foreground: view.foreground; text: Eitr.I18n.tr("Swap"); onClicked: pageBody.apply(["set", pageBody.editing, pageBody.proposed, "--swap"]) }
                        PanelButton { width: 110; foreground: view.foreground; text: Eitr.I18n.tr("Cancel"); onClicked: { pageBody.editing = ""; pageBody.clash = null; } }
                    }
                }
            }
        }
    }
    SettingsConfirmSheet {
        id: confirm
        foreground: view.foreground; surfaceColor: view.background
        confirmText: Eitr.I18n.tr("Apply")
        onConfirmed: pageBody.apply(pageBody.pending)
    }
}

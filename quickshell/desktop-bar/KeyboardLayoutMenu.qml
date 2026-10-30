import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

// Switches between the configured layouts. Adding and removing them belongs to
// Walker's Settings > Devices & Input > Keyboard menu. The bar reads `layouts` and
// `activeCode` to show its indicator only when there is more than one layout.
ThemedPopup {
    id: menu
    waitForFreshData: true
    property var layouts: []
    property int activeLayout: -1
    property string error: ""
    readonly property string helper: Quickshell.shellDir + "/scripts/keyboard-layout.py"
    readonly property var active: layouts.find(entry => entry.index === activeLayout) || null
    readonly property string activeCode: active ? active.code : ""
    readonly property string activeLabel: active ? active.label : ""
    implicitWidth: 428
    implicitHeight: heading.implicitHeight + 16 + Math.max(1, layouts.length) * (PanelStyle.selectionRowHeight + PanelStyle.selectionRowGap)
        + 8 + PanelStyle.selectionRowHeight + (error ? 34 : 0) + verticalContentInset

    function refresh() { if (!query.running && !operation.running) query.running = true; }
    function perform(command) {
        if (operation.running) return;
        error = "";
        operation.command = ["python3", helper].concat(command);
        operation.running = true;
    }
    function manageInWalker() {
        opened = false;
        Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:keyboard"]);
    }
    Component.onCompleted: refresh()
    onOpenedChanged: if (opened) { error = ""; refresh(); }
    // Alt+Shift switches fire activelayout; adding or removing a layout reloads the config.
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "activelayout" || event.name === "configreloaded") menu.refresh();
        }
    }
    Process {
        id: query
        command: ["python3", menu.helper]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const received = output.text;
            menu.updateContent(function() {
                try {
                    var result = JSON.parse(received);
                    if (code !== 0) throw new Error(result.error || Eitr.I18n.tr("Layouts unavailable"));
                    menu.applySnapshot("layouts", result.layouts);
                    menu.activeLayout = result.active;
                } catch (e) { menu.error = e.message; }

            });
        }
    }
    Process {
        id: operation
        stdout: StdioCollector { id: operationOutput }
        onExited: function(code) {
            if (code === 0) {
                menu.refresh();
                menu.opened = false;
            } else {
                try { menu.error = JSON.parse(operationOutput.text).error || Eitr.I18n.tr("Could not change layout"); }
                catch (e) { menu.error = Eitr.I18n.tr("Could not change layout"); }
            }
        }
    }
    Item {
        id: body
        anchors.fill: parent
        anchors.margins: 0
        PanelHeading {
            id: heading
            width: parent.width; text: Eitr.I18n.tr("Keyboard Layout")
            foreground: menu.foreground; accent: menu.accent; rune: "keyboard"
        }
        ListView {
            id: choices
            anchors.top: heading.bottom
            anchors.topMargin: 16
            anchors.bottom: errorLabel.top
            anchors.bottomMargin: 8
            width: parent.width
            clip: true
            model: menu.layouts
            spacing: PanelStyle.selectionRowGap
            boundsBehavior: Flickable.StopAtBounds
            delegate: KeyboardLayoutRow {
                required property var modelData
                width: choices.width
                label: modelData.label
                foreground: menu.foreground; tooltipBackground: menu.background
                selected: modelData.index === menu.activeLayout
                available: !operation.running
                showRemove: false
                onActivated: menu.perform(["select", String(modelData.index)])
            }
            Text {
                anchors.centerIn: parent
                visible: choices.count === 0
                text: Eitr.I18n.tr("Loading...")
                color: menu.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
        }
        Text {
            id: errorLabel
            anchors.bottom: footer.top
            anchors.bottomMargin: 8
            width: parent.width
            height: menu.error ? implicitHeight : 0
            text: menu.error
            wrapMode: Text.Wrap
            color: menu.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.secondarySize
        }
        PanelFooterLink {
            id: footer
            anchors.bottom: parent.bottom
            text: Eitr.I18n.tr("Add or Remove Layouts…")
            foreground: menu.foreground
            onClicked: menu.manageInWalker()
        }
    }
}

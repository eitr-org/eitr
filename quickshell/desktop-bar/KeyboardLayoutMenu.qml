import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    property var layouts: []
    property var availableLayouts: []
    property int activeLayout: -1
    property bool adding: false
    property string error: ""
    readonly property string helper: Quickshell.shellDir + "/scripts/keyboard-layout.py"
    readonly property var filteredLayouts: availableLayouts.filter(entry =>
        (entry.label + " " + entry.layout + " " + entry.variant).toLowerCase().includes(search.text.toLowerCase()))
    implicitWidth: 388
    implicitHeight: 44 + (adding ? 468 : Math.max(1, layouts.length) * (PanelStyle.selectionRowHeight + PanelStyle.selectionRowGap) + 104 + (error ? 34 : 0))
    keyTarget: adding ? search : body

    function refresh() { if (!query.running && !operation.running) query.running = true; }
    function loadCatalog() { if (!catalog.running && !availableLayouts.length) catalog.running = true; }
    function perform(command) {
        if (operation.running) return;
        error = "";
        operation.command = ["python3", helper].concat(command);
        operation.running = true;
    }
    onOpenedChanged: {
        if (opened) { error = ""; adding = false; search.text = ""; refresh(); }
    }
    onAddingChanged: {
        error = "";
        if (adding) {
            if (!catalog.running && !availableLayouts.length) catalog.running = true;
            Qt.callLater(function() { search.forceActiveFocus(); });
        }
    }
    Timer { interval: 1000; running: menu.opened && !menu.adding; repeat: true; onTriggered: menu.refresh() }
    Process {
        id: query
        command: ["python3", menu.helper]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            try {
                var result = JSON.parse(output.text);
                if (code !== 0) throw new Error(result.error || Eitr.I18n.tr("Layouts unavailable"));
                menu.layouts = result.layouts;
                menu.activeLayout = result.active;
            } catch (e) { menu.error = e.message; }
        }
    }
    Process {
        id: catalog
        command: ["python3", menu.helper, "catalog"]
        stdout: StdioCollector { id: catalogOutput }
        onExited: function(code) {
            try {
                var result = JSON.parse(catalogOutput.text);
                if (code !== 0) throw new Error(result.error || Eitr.I18n.tr("Layouts unavailable"));
                menu.availableLayouts = result.layouts;
            } catch (e) { menu.error = e.message; }
        }
    }
    Process {
        id: operation
        stdout: StdioCollector { id: operationOutput }
        onExited: function(code) {
            if (code === 0) {
                menu.refresh();
                if (menu.adding) { menu.adding = false; menu.refresh(); }
                else menu.opened = false;
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
        TextField {
            id: search
            y: heading.height + 12
            visible: menu.adding
            width: parent.width
            height: 36
            placeholderText: Eitr.I18n.tr("Search layouts...")
            color: menu.foreground
            placeholderTextColor: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.5)
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
            background: Rectangle {
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.08)
                border.color: search.activeFocus ? menu.accent : "transparent"
            }
            HoverHandler { cursorShape: Qt.IBeamCursor }
            onTextChanged: choices.currentIndex = 0
            Keys.onDownPressed: choices.incrementCurrentIndex()
            Keys.onUpPressed: choices.decrementCurrentIndex()
            onAccepted: if (menu.filteredLayouts.length) {
                var entry = menu.filteredLayouts[Math.max(0, choices.currentIndex)];
                menu.perform(["add", entry.layout, entry.variant]);
            }
        }
        ListView {
            id: choices
            anchors.top: menu.adding ? search.bottom : heading.bottom
            anchors.topMargin: menu.adding ? 10 : 12
            anchors.bottom: errorLabel.top
            anchors.bottomMargin: 8
            width: parent.width
            clip: true
            model: menu.adding ? menu.filteredLayouts : menu.layouts
            spacing: PanelStyle.selectionRowGap
            boundsBehavior: Flickable.StopAtBounds
            delegate: KeyboardLayoutRow {
                id: entryRow
                required property var modelData
                required property int index
                width: choices.width
                label: modelData.label
                foreground: menu.foreground; tooltipBackground: menu.background
                selected: menu.adding ? choices.currentIndex === index : modelData.index === menu.activeLayout
                available: !operation.running
                showRemove: !menu.adding
                removable: menu.layouts.length > 1
                onActivated: menu.perform(menu.adding ? ["add", modelData.layout, modelData.variant] : ["select", String(modelData.index)])
                onRemoveRequested: menu.perform(["remove", String(modelData.index)])
            }
            Text {
                anchors.centerIn: parent
                visible: choices.count === 0
                text: menu.adding ? (catalog.running ? Eitr.I18n.tr("Loading...") : Eitr.I18n.tr("No layouts found")) : Eitr.I18n.tr("Loading...")
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
        PanelButton {
            id: footer
            anchors.bottom: parent.bottom
            width: parent.width
            height: 32
            text: menu.adding ? Eitr.I18n.tr("Back") : Eitr.I18n.tr("Add Layout")
            foreground: menu.foreground
            available: !operation.running
            onClicked: { if (available) menu.adding = !menu.adding; }
        }
    }
}

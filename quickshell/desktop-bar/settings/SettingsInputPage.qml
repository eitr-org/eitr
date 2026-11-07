import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

Column {
    id: view
    objectName: "settings-input-content"
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property var layouts: []
    property var catalog: []
    property int selected: -1
    property string error: ""
    readonly property string helper: Eitr.Paths.code("quickshell/desktop-bar/scripts/keyboard-layout.py")
    spacing: PanelStyle.selectionRowGap
    function refresh() {
        if (!live || !active) return;
        if (!query.running) query.running = true;
        if (!catalog.length && !catalogQuery.running) catalogQuery.running = true;
    }
    function change(arguments) {
        if (!live || operation.running) return;
        operation.command = ["python3", helper].concat(arguments);
        operation.running = true;
    }
    onActiveChanged: refresh()
    Process {
        id: query
        command: ["python3", view.helper, "summary"]
        stdout: StdioCollector { id: summaryOutput }
        onExited: function(code) {
            const result = JsonState.parse(summaryOutput.text, code, {layouts: "array", active: "number"});
            view.error = result.ok ? "" : result.error;
            if (result.ok) { view.layouts = result.data.layouts; view.selected = result.data.active; }
        }
    }
    Process {
        id: catalogQuery
        command: ["python3", view.helper, "catalog"]
        stdout: StdioCollector { id: catalogOutput }
        onExited: function(code) {
            const result = JsonState.parse(catalogOutput.text, code, {layouts: "array"});
            view.error = result.ok ? "" : result.error;
            if (result.ok) view.catalog = result.data.layouts;
        }
    }
    Process {
        id: operation
        stderr: StdioCollector { id: errors }
        onExited: function(code) { view.error = code ? errors.text.trim() : ""; view.refresh(); }
    }
    Text { text: Eitr.I18n.tr("Select, reorder or remove your keyboard layouts."); color: view.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
    Repeater {
        model: view.layouts
        Row {
            required property var modelData
            required property int index
            width: view.width; spacing: 6
            KeyboardLayoutRow {
                width: parent.width - 60
                label: parent.modelData.label
                foreground: view.foreground; tooltipBackground: view.background
                selected: parent.modelData.index === view.selected
                removable: view.layouts.length > 1
                available: !operation.running
                onActivated: view.change(["select", String(parent.modelData.index)])
                onRemoveRequested: view.change(["remove", String(parent.modelData.index)])
            }
            PanelButton { width: 24; height: 24; anchors.verticalCenter: parent.verticalCenter; icon: true; text: "↑"; foreground: view.foreground; available: parent.index > 0 && !operation.running; onClicked: view.change(["move", String(parent.index), String(parent.index - 1)]) }
            PanelButton { width: 24; height: 24; anchors.verticalCenter: parent.verticalCenter; icon: true; text: "↓"; foreground: view.foreground; available: parent.index < view.layouts.length - 1 && !operation.running; onClicked: view.change(["move", String(parent.index), String(parent.index + 1)]) }
        }
    }
    // Choosing a layout from the floating list adds it; the catalog loads with the page.
    ChoiceDropdown {
        objectName: "settings-add-layout"
        width: Math.min(parent.width, 360)
        gold: SettingsInk.gold; background: SettingsInk.background
        foreground: view.foreground
        label: Eitr.I18n.tr("Add Layout")
        placeholder: view.catalog.length ? "" : Eitr.I18n.tr("Loading...")
        available: view.layouts.length < 4 && !operation.running
        choices: view.catalog.map(layout => ({value: layout.layout + "|" + layout.variant, label: layout.label}))
        onChosen: value => { const parts = value.split("|"); view.change(["add", parts[0], parts[1]]); }
    }
    Text { width: parent.width; visible: view.error !== ""; text: view.error; wrapMode: Text.WordWrap; color: view.foreground; font.pixelSize: PanelStyle.captionSize }
}

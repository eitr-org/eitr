import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

Column {
    id: view
    // Layout names are short: the list keeps a compact width instead of filling the card.
    readonly property real listWidth: Math.min(width, 480)
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
    SettingsTarget { objectName: "setting-input-keyboard-layout" }
    Repeater {
        model: view.layouts
        KeyboardLayoutRow {
            required property var modelData
            required property int index
            width: view.listWidth
            label: modelData.label
            foreground: view.foreground; tooltipBackground: view.background
            selected: modelData.index === view.selected
            removable: view.layouts.length > 1
            available: !operation.running
            reorderable: true
            canMoveUp: index > 0
            canMoveDown: index < view.layouts.length - 1
            onActivated: view.change(["select", String(modelData.index)])
            onRemoveRequested: view.change(["remove", String(modelData.index)])
            onMoveRequested: direction => view.change(["move", String(index), String(index + direction)])
        }
    }
    // Choosing a layout from the floating list adds it; the catalog loads with the page.
    ControlRow {
        text: Eitr.I18n.tr("Add Layout")
        description: Eitr.I18n.tr("Add another keyboard layout to your list.")
        foreground: view.foreground
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-input-add-layout" }

            objectName: "settings-add-layout"
            width: parent.width
            gold: SettingsInk.gold; background: SettingsInk.background
            foreground: view.foreground
            accessibleName: Eitr.I18n.tr("Add Layout")
            placeholder: view.catalog.length ? "" : Eitr.I18n.tr("Loading...")
            available: view.layouts.length < 4 && !operation.running
            choices: view.catalog.map(layout => ({value: layout.layout + "|" + layout.variant, label: layout.label}))
            onChosen: value => { const parts = value.split("|"); view.change(["add", parts[0], parts[1]]); }
        }
    }
    Text { width: parent.width; visible: view.error !== ""; text: view.error; wrapMode: Text.WordWrap; color: view.foreground; font.pixelSize: PanelStyle.captionSize }
}

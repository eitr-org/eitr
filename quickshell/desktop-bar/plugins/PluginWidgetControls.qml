import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../PluginGeometry.js" as Geometry

// Every setting of one placed widget copy: Edit position and Duplicate, size, rotation,
// display, background, above windows, the plugin's own options and Remove from desktop.
// Control Center's widget cards and the desktop right-click menu both show this, so the
// two never drift apart.
Column {
    id: controls
    required property var entry
    required property var placement
    required property color foreground
    required property color background
    required property color accent
    // Connected displays as {name, description, width, height} in logical pixels.
    property var monitors: Quickshell.screens.map(screen => ({name: screen.name, description: screen.model || screen.name,
        width: screen.width, height: screen.height}))
    // Finished one-shot actions (edit, duplicate, display, remove), so a menu can close.
    signal acted(string action)
    readonly property string instance: placement ? placement.instance : ""
    readonly property var options: placement ? PluginRegistry.widgetMenus[PluginRegistry.widgetKey(placement)] || [] : []
    readonly property bool editing: !!placement && PluginRegistry.editingCopy(placement)
    readonly property int rotation: placement ? PluginRegistry.rotation(placement) : 0
    readonly property string surface: placement ? PluginRegistry.widgetSurface(Object.assign({}, entry, {geometry: placement})) : "none"
    readonly property var displayChoices: {
        const choices = monitors.map(monitor => ({value: monitor.name, label: monitor.description}));
        if (placement && !monitors.some(monitor => monitor.name === placement.monitor))
            choices.push({value: placement.monitor, label: placement.monitor});
        return choices;
    }
    readonly property var labels: [Eitr.I18n.tr("Size"), Eitr.I18n.tr("Rotation"), Eitr.I18n.tr("Display"),
        Eitr.I18n.tr("Background"), Eitr.I18n.tr("Style")]
    // The label column fits the longest label in the current language.
    readonly property real labelWidth: Math.min(width * 0.42, Math.ceil(Math.max(...labels.map(text => bodyMetrics.advanceWidth(text)))) + 38)
    readonly property real controlWidth: width - labelWidth
    spacing: PanelStyle.selectionRowGap

    function change(action, settings) {
        PluginRegistry.change(action, entry, Object.assign({instance: instance}, settings || {}));
    }
    function act(action) { PluginRegistry.widgetAction(entry.plugin, entry.id, instance, action, false); }
    function screenOf(name) { return monitors.find(monitor => monitor.name === name) || null; }
    function duplicate() {
        const screen = screenOf(placement.monitor);
        const geometry = {x: placement.x, y: placement.y, width: placement.width, height: placement.height};
        change("duplicate", screen ? {geometry: Geometry.beside(geometry, screen.width, screen.height, 24)} : {});
        acted("duplicate");
    }
    function moveTo(name) {
        const screen = screenOf(name);
        const geometry = {x: placement.x, y: placement.y, width: placement.width, height: placement.height};
        change("move", {monitor: name, geometry: screen ? Geometry.clampToScreen(geometry, screen.width, screen.height) : geometry});
        acted("display");
    }
    function rotate(degrees) {
        const value = Geometry.snapRotation(degrees);
        PluginRegistry.previewRotation(placement, value);
        change("rotate", {rotation: value});
    }
    function fitWidth(text, glyph) {
        return Math.ceil(controlMetrics.advanceWidth(text)) + (glyph ? 34 : 8) + 10;
    }

    FontMetrics { id: bodyMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
    FontMetrics { id: controlMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }

    // A setting's glyph and name in the label column; its control fills the rest of the row.
    component Setting: Item {
        id: setting
        property string glyph: ""
        property string text: ""
        default property alias control: slot.data
        width: controls.width
        height: Math.max(PanelStyle.selectionRowHeight, slot.childrenRect.height)
        Text {
            id: settingGlyph
            width: 20; anchors.verticalCenter: parent.verticalCenter
            text: setting.glyph; color: controls.foreground; opacity: 0.8
            horizontalAlignment: Text.AlignHCenter
            font.family: PanelStyle.fontFamily; font.pixelSize: 15
        }
        Text {
            x: 26; width: controls.labelWidth - x - 4; anchors.verticalCenter: parent.verticalCenter
            text: setting.text; textFormat: Text.PlainText; elide: Text.ElideRight
            color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        Item {
            id: slot
            x: controls.labelWidth; width: controls.controlWidth
            height: childrenRect.height; anchors.verticalCenter: parent.verticalCenter
        }
    }
    // A text button as wide as its label (and glyph), so translations are never cut.
    component FitButton: PanelButton {
        id: fitButton
        width: controls.fitWidth(fitButton.text, fitButton.leadingIcon !== "")
        outlined: true
        foreground: controls.foreground
    }
    component Divider: Rectangle {
        width: controls.width; height: 1
        color: Qt.alpha(controls.foreground, PanelStyle.dividerAlpha)
    }

    // Side by side when both labels fit, otherwise one per line.
    Flow {
        id: actionRow
        readonly property real half: (controls.width - spacing) / 2
        readonly property bool stacked: Math.max(controls.fitWidth(Eitr.I18n.tr("Edit position"), true),
            controls.fitWidth(Eitr.I18n.tr("Done"), true), controls.fitWidth(Eitr.I18n.tr("Duplicate"), true)) > half
        width: controls.width; spacing: PanelStyle.selectionActionGap
        PanelButton {
            width: actionRow.stacked ? controls.width : actionRow.half
            leadingIcon: String.fromCodePoint(0xF03EB); textAlignment: Text.AlignLeft; outlined: true
            text: controls.editing ? Eitr.I18n.tr("Done") : Eitr.I18n.tr("Edit position")
            selected: controls.editing; foreground: controls.foreground
            onClicked: { PluginRegistry.editCopy(controls.placement, !controls.editing); controls.acted("edit"); }
        }
        PanelButton {
            width: actionRow.stacked ? controls.width : actionRow.half
            leadingIcon: String.fromCodePoint(0xF018F); textAlignment: Text.AlignLeft; outlined: true
            text: Eitr.I18n.tr("Duplicate"); foreground: controls.foreground
            onClicked: controls.duplicate()
        }
    }
    Divider {}
    Setting {
        glyph: String.fromCodePoint(0xF0A68); text: Eitr.I18n.tr("Size")
        Row {
            spacing: PanelStyle.selectionActionGap
            FitButton { width: 36; text: "−"; Accessible.name: Eitr.I18n.tr("Smaller"); onClicked: controls.act("smaller") }
            FitButton { width: 36; text: "+"; Accessible.name: Eitr.I18n.tr("Larger"); onClicked: controls.act("larger") }
            FitButton { text: Eitr.I18n.tr("Full width"); onClicked: controls.act("full") }
        }
    }
    Setting {
        glyph: String.fromCodePoint(0xF0467); text: Eitr.I18n.tr("Rotation")
        Column {
            width: parent.width; spacing: 2
            Item {
                width: parent.width; height: 30
                PanelSlider {
                    id: rotationSlider
                    width: parent.width - degrees.width - 4
                    from: 0; to: 359; stepSize: 1; live: true
                    foreground: controls.foreground; accent: controls.accent
                    Accessible.name: Eitr.I18n.tr("Rotation")
                    // Follows the saved angle except while the pointer holds it.
                    readonly property int saved: controls.rotation
                    onSavedChanged: if (!pressed) value = saved
                    Component.onCompleted: value = saved
                    onMoved: {
                        const snapped = Geometry.snapRotation(value);
                        if (snapped !== value) value = snapped;
                        PluginRegistry.previewRotation(controls.placement, snapped);
                        if (!pressed) keyboardCommit.restart();
                    }
                    onPressedChanged: if (!pressed) controls.rotate(value)
                    Timer { id: keyboardCommit; interval: 400; onTriggered: controls.rotate(rotationSlider.value) }
                }
                Text {
                    id: degrees
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    width: Math.ceil(controlMetrics.advanceWidth("359°")) + 2; horizontalAlignment: Text.AlignRight
                    text: controls.rotation + "°"; color: controls.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; font.features: PanelStyle.tabularFigures
                }
            }
            Row {
                spacing: PanelStyle.selectionActionGap
                FitButton {
                    width: 36; text: String.fromCodePoint(0xF0465); textSize: 16; textAlignment: Text.AlignHCenter
                    Accessible.name: Eitr.I18n.tr("Turn left")
                    onClicked: controls.rotate(Math.round(controls.rotation / 90) * 90 - 90)
                }
                FitButton {
                    width: 36; text: String.fromCodePoint(0xF0467); textSize: 16; textAlignment: Text.AlignHCenter
                    Accessible.name: Eitr.I18n.tr("Turn right")
                    onClicked: controls.rotate(Math.round(controls.rotation / 90) * 90 + 90)
                }
                FitButton {
                    text: Eitr.I18n.tr("Reset"); available: controls.rotation !== 0
                    onClicked: controls.rotate(0)
                }
            }
        }
    }
    Setting {
        visible: controls.displayChoices.length > 1
        glyph: String.fromCodePoint(0xF0379); text: Eitr.I18n.tr("Display")
        ChoiceDropdown {
            width: parent.width
            foreground: controls.foreground; background: controls.background; gold: controls.accent
            accessibleName: Eitr.I18n.tr("Display")
            choices: controls.displayChoices
            current: controls.placement ? controls.placement.monitor : ""
            onChosen: value => controls.moveTo(value)
        }
    }
    Setting {
        glyph: String.fromCodePoint(0xF013A); text: Eitr.I18n.tr("Background")
        ChoiceSegmented {
            width: parent.width; foreground: controls.foreground
            choices: [{id: "panel", label: Eitr.I18n.tr("Panel")}, {id: "none", label: Eitr.I18n.tr("Transparent")}]
            current: controls.surface
            onChosen: value => controls.change("surface", {surface: value})
        }
    }
    Setting {
        visible: controls.options.length > 0
        glyph: String.fromCodePoint(0xF062E); text: Eitr.I18n.tr("Style")
        Flow {
            id: optionFlow
            width: parent.width; spacing: PanelStyle.selectionActionGap
            Repeater {
                model: controls.options
                FitButton {
                    required property var modelData
                    text: modelData.text; selected: !!modelData.checked; outlined: !modelData.checked
                    Accessible.role: Accessible.RadioButton
                    Accessible.checked: selected
                    onClicked: PluginRegistry.widgetAction(controls.entry.plugin, controls.entry.id, controls.instance, modelData.id, true)
                }
            }
        }
    }
    Item {
        width: controls.width; height: Math.max(PanelStyle.selectionRowHeight, layerLabel.implicitHeight + 8)
        Text {
            width: 20; anchors.verticalCenter: parent.verticalCenter
            text: String.fromCodePoint(0xF0328); color: controls.foreground; opacity: 0.8
            horizontalAlignment: Text.AlignHCenter
            font.family: PanelStyle.fontFamily; font.pixelSize: 15
        }
        Text {
            id: layerLabel
            x: 26; width: layerSwitch.x - x - 8; anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Show above windows"); textFormat: Text.PlainText; wrapMode: Text.Wrap
            color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelSwitch {
            id: layerSwitch
            anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
            foreground: controls.foreground; accent: controls.accent
            checked: !!controls.placement && !!controls.placement.aboveWindows
            Accessible.name: Eitr.I18n.tr("Show above windows")
            onToggled: controls.change("toggle-layer")
        }
    }
    Divider {}
    PanelButton {
        width: controls.width; flat: true; textAlignment: Text.AlignLeft
        leadingIcon: String.fromCodePoint(0xF09E7)
        text: Eitr.I18n.tr("Remove from desktop"); foreground: controls.foreground
        onClicked: { controls.change("unplace"); controls.acted("remove"); }
    }
}

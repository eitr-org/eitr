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
    // A plugin's options, one row per `group` it names (ungrouped ones under Style).
    readonly property var optionGroups: {
        const names = [];
        for (const option of options) {
            const name = typeof option.group === "string" ? option.group : "";
            if (!names.includes(name)) names.push(name);
        }
        return names.map(name => ({label: name || Eitr.I18n.tr("Style"), options: options.filter(option => (typeof option.group === "string" ? option.group : "") === name)}));
    }
    // Each setting sits in a bordered row, like WiFi's network rows.
    readonly property real rowPadding: 6
    readonly property real controlWidth: width - 2 * rowPadding
    spacing: PanelStyle.selectionRowGap

    function change(action, settings) {
        PluginRegistry.change(action, entry, Object.assign({instance: instance}, settings || {}));
    }
    function act(action) { PluginRegistry.widgetAction(entry.plugin, entry.id, instance, action, false); }
    function screenOf(name) { return monitors.find(monitor => monitor.name === name) || null; }
    // A copy starts at the display's top left, so it reads as a new widget; the desktop
    // keeps it below the bar and inside the screen.
    function duplicate() {
        change("duplicate", {geometry: {x: 24, y: 24, width: placement.width, height: placement.height}});
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

    FontMetrics { id: controlMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }

    // A setting stacked in its bordered row: glyph and name, then its control across the
    // whole row, then a one-line description.
    component Setting: Rectangle {
        id: setting
        property string glyph: ""
        property string text: ""
        property string description: ""
        default property alias control: slot.data
        width: controls.width
        height: stack.implicitHeight + 2 * controls.rowPadding
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(controls.foreground, PanelStyle.selectionAlpha(false, false))
        border.width: PanelStyle.selectionBorderWidth(false)
        border.color: Qt.alpha(controls.foreground, PanelStyle.selectionBorderAlpha)
        Column {
            id: stack
            x: controls.rowPadding; y: controls.rowPadding
            width: controls.controlWidth; spacing: 6
            Item {
                visible: setting.text !== ""
                width: parent.width; height: 20
                Text {
                    width: 20; anchors.verticalCenter: parent.verticalCenter
                    text: setting.glyph; color: controls.foreground; opacity: 0.8
                    horizontalAlignment: Text.AlignHCenter
                    font.family: PanelStyle.fontFamily; font.pixelSize: 15
                }
                Text {
                    x: 26; width: parent.width - x; anchors.verticalCenter: parent.verticalCenter
                    text: setting.text; textFormat: Text.PlainText; elide: Text.ElideRight
                    color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
            }
            Item {
                id: slot
                width: parent.width; height: childrenRect.height
            }
            Text {
                visible: setting.description !== ""
                width: parent.width; wrapMode: Text.Wrap; textFormat: Text.PlainText
                text: setting.description; color: controls.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
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
        description: Eitr.I18n.tr("Shrink, grow or fill the screen width.")
        Row {
            spacing: PanelStyle.selectionActionGap
            FitButton { width: 36; text: "−"; Accessible.name: Eitr.I18n.tr("Smaller"); onClicked: controls.act("smaller") }
            FitButton { width: 36; text: "+"; Accessible.name: Eitr.I18n.tr("Larger"); onClicked: controls.act("larger") }
            FitButton { text: Eitr.I18n.tr("Full width"); onClicked: controls.act("full") }
        }
    }
    Setting {
        glyph: String.fromCodePoint(0xF0467); text: Eitr.I18n.tr("Rotation")
        description: Eitr.I18n.tr("Drag to any angle, or turn by 45°.")
        Column {
            width: parent.width; spacing: 4
            Item {
                width: parent.width; height: 30
                PanelSlider {
                    id: rotationSlider
                    width: parent.width
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
                // The angle shows while the slider is hovered or held.
                HoverHandler { id: rotationHover }
                BarTooltip {
                    target: rotationSlider; hovered: rotationHover.hovered || rotationSlider.pressed
                    text: Math.round(rotationSlider.value) + "°"
                    foreground: controls.foreground; background: controls.background
                }
            }
            Row {
                spacing: PanelStyle.selectionActionGap
                FitButton {
                    width: 36; text: String.fromCodePoint(0xF0465); textSize: 16; textAlignment: Text.AlignHCenter
                    Accessible.name: Eitr.I18n.tr("Turn left")
                    onClicked: controls.rotate(Math.round(controls.rotation / 45) * 45 - 45)
                }
                FitButton {
                    width: 36; text: String.fromCodePoint(0xF0467); textSize: 16; textAlignment: Text.AlignHCenter
                    Accessible.name: Eitr.I18n.tr("Turn right")
                    onClicked: controls.rotate(Math.round(controls.rotation / 45) * 45 + 45)
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
        // The outlined dropdown carries its own floating label and helper line, as in Settings.
        ChoiceDropdown {
            width: parent.width
            floatingLabel: Eitr.I18n.tr("Display")
            helperText: Eitr.I18n.tr("The screen that shows this copy.")
            foreground: controls.foreground; background: controls.background; gold: controls.accent
            accessibleName: Eitr.I18n.tr("Display")
            choices: controls.displayChoices
            current: controls.placement ? controls.placement.monitor : ""
            onChosen: value => controls.moveTo(value)
        }
    }
    Setting {
        glyph: String.fromCodePoint(0xF013A); text: Eitr.I18n.tr("Background")
        description: Eitr.I18n.tr("A panel behind the widget, or nothing.")
        ChoiceSegmented {
            width: parent.width; foreground: controls.foreground
            choices: [{id: "panel", label: Eitr.I18n.tr("Panel")}, {id: "none", label: Eitr.I18n.tr("Transparent")}]
            current: controls.surface
            onChosen: value => controls.change("surface", {surface: value})
        }
    }
    Repeater {
        model: controls.optionGroups
        Setting {
            id: optionRow
            required property var modelData
            glyph: String.fromCodePoint(0xF062E); text: modelData.label
            Flow {
            width: parent.width; spacing: PanelStyle.selectionActionGap
            Repeater {
                model: optionRow.modelData.options
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
    }
    Rectangle {
        width: controls.width; height: Math.max(PanelStyle.selectionRowHeight, layerLabel.implicitHeight + 2 * controls.rowPadding + 4)
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(controls.foreground, PanelStyle.selectionAlpha(false, false))
        border.width: PanelStyle.selectionBorderWidth(false)
        border.color: Qt.alpha(controls.foreground, PanelStyle.selectionBorderAlpha)
        Text {
            x: controls.rowPadding
            width: 20; anchors.verticalCenter: parent.verticalCenter
            text: String.fromCodePoint(0xF0328); color: controls.foreground; opacity: 0.8
            horizontalAlignment: Text.AlignHCenter
            font.family: PanelStyle.fontFamily; font.pixelSize: 15
        }
        Column {
            id: layerLabel
            x: controls.rowPadding + 26; width: layerSwitch.x - x - 8; anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text {
                width: parent.width; text: Eitr.I18n.tr("Show above windows"); textFormat: Text.PlainText; wrapMode: Text.Wrap
                color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
            Text {
                width: parent.width; text: Eitr.I18n.tr("Stays on top of open apps."); textFormat: Text.PlainText; wrapMode: Text.Wrap
                color: controls.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
        }
        PanelSwitch {
            id: layerSwitch
            anchors.right: parent.right; anchors.rightMargin: controls.rowPadding; anchors.verticalCenter: parent.verticalCenter
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

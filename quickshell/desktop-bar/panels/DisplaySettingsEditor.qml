import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Resolution, refresh rate, HDR, scale, rotation, position and mirroring for one display, inside
// the Display panel. Each setting is one row showing its current value; clicking
// it opens its choices. Choosing a value asks the panel to apply it
// (scripts/display-settings.py set); a new mode or HDR toggle reverts on its own unless kept.
Column {
    id: editor
    required property var monitor
    required property var others
    required property color foreground
    property color background: "transparent"
    property color accent: foreground
    // Displays this one may be placed beside (the panel leaves out those placed beside it).
    property var placeable: others
    // The main display holds the bar and stays put; the others are arranged around it.
    property bool isMain: false
    property bool busy: false
    property var pending: null
    // The setting whose choices are open; one at a time keeps the panel short.
    property string openSetting: ""
    signal tryChange(string key, string value)
    signal makeMain()
    spacing: 6

    readonly property var modes: (monitor.modes || []).map(mode => mode.replace(/Hz$/, ""))
    readonly property string currentResolution: (monitor.mode || "").split("@")[0]
    readonly property real currentRate: Number((monitor.mode || "@0").split("@")[1])
    readonly property var resolutions: modes.map(mode => mode.split("@")[0])
        .filter((resolution, index, all) => all.indexOf(resolution) === index)
    readonly property var rates: modes.filter(mode => mode.split("@")[0] === currentResolution)
        .map(mode => mode.split("@")[1])
        .filter((rate, index, all) => all.indexOf(rate) === index)
        .sort((first, second) => Number(second) - Number(first))
    readonly property var scales: ["1", "1.25", "1.5", "1.75", "2"]
    // How the screen itself is turned; the picture is drawn upright on it.
    readonly property var rotations: [
        {value: "0", label: Eitr.I18n.tr("Normal")}, {value: "180", label: Eitr.I18n.tr("Upside down")},
        {value: "90", label: Eitr.I18n.tr("Turned right")}, {value: "270", label: Eitr.I18n.tr("Turned left")}
    ]
    readonly property string rotation: ["0", "90", "180", "270"][Number(monitor.transform || 0) % 4]
    readonly property var sides: [{key: "left-of", label: Eitr.I18n.tr("Left of")}, {key: "right-of", label: Eitr.I18n.tr("Right of")},
                                  {key: "above", label: Eitr.I18n.tr("Above")}, {key: "below", label: Eitr.I18n.tr("Below")}]
    // Where this display is saved beside another one; the helper keeps it there when that one changes.
    readonly property var anchor: monitor.anchor || null
    readonly property bool sideBySide: !!anchor && (anchor.side === "left-of" || anchor.side === "right-of")
    readonly property var aligns: [{key: "start", label: sideBySide ? Eitr.I18n.tr("Top") : Eitr.I18n.tr("Left")},
                                   {key: "center", label: sideBySide ? Eitr.I18n.tr("Middle") : Eitr.I18n.tr("Center")},
                                   {key: "end", label: sideBySide ? Eitr.I18n.tr("Bottom") : Eitr.I18n.tr("Right")}]
    readonly property string positionValue: {
        if (isMain)
            return Eitr.I18n.tr("Main display · others go around it");
        if (!anchor)
            return Eitr.I18n.tr("At %1", [(monitor.position || "0x0").replace("x", ", ")]);
        const side = sides.find(item => item.key === anchor.side);
        const align = aligns.find(item => item.key === anchor.align);
        return (side ? side.label : anchor.side) + " " + anchor.of + " · " + (align ? align.label : anchor.align);
    }

    function toggle(setting) { openSetting = openSetting === setting ? "" : setting; }
    function choose(key, value) { if (key !== "position") openSetting = ""; tryChange(key, value); }

    // Inline components cannot see the editor's id; their colour and state are set where they are used.
    component Caption: Text {
        opacity: 0.65
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
    }

    component SettingRow: Rectangle {
        id: row
        required property string label
        required property string value
        required property color tint
        required property color chevron
        property bool open: false
        property bool interactive: true
        signal toggled()
        width: parent ? parent.width : 0
        height: PanelStyle.selectionRowHeight
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(tint, rowMouse.containsMouse ? 0.12 : open ? 0.07 : 0.04)
        Text {
            x: 10; anchors.verticalCenter: parent.verticalCenter
            text: row.label; color: row.tint
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        Text {
            anchors.right: arrow.left; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
            width: Math.max(0, row.width * 0.6)
            horizontalAlignment: Text.AlignRight
            elide: Text.ElideRight
            text: row.value; color: row.tint; opacity: 0.75
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        Text {
            id: arrow
            anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
            width: row.interactive ? implicitWidth : 0
            text: row.interactive ? (row.open ? "󰅀" : "󰅂") : ""; color: row.chevron
            font.family: DesktopFonts.family; font.pixelSize: 16
        }
        MouseArea {
            id: rowMouse
            anchors.fill: parent; enabled: row.interactive; hoverEnabled: true
            cursorShape: Qt.PointingHandCursor; onClicked: row.toggled()
        }
    }

    Rectangle {
        SettingsTarget { objectName: "setting-displays-main-display" }
        width: parent.width; height: PanelStyle.selectionRowHeight
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(editor.foreground, 0.04)
        Text {
            x: 10; anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Main display"); color: editor.foreground
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelSwitch {
            id: mainSwitch
            anchors.right: parent.right; anchors.rightMargin: 4; anchors.verticalCenter: parent.verticalCenter
            foreground: editor.foreground; accent: editor.accent
            checked: editor.isMain
            // One display is always main: choose another one to move it. When the main
            // display is unplugged, the next one takes over until it returns.
            enabled: !editor.isMain && !editor.busy
            onToggled: { if (checked) editor.makeMain(); checked = Qt.binding(() => editor.isMain); }
            HoverHandler { id: mainHover }
            BarTooltip {
                target: mainSwitch; hovered: mainHover.hovered
                text: Eitr.I18n.tr("The main display holds the bar, panels and notifications. Position only sets where a screen sits next to the others.")
                background: editor.background; foreground: editor.foreground
            }
        }
    }
    Column {
        SettingsTarget { objectName: "setting-displays-hdr" }
        visible: !!editor.monitor.hdr_capable
        width: parent.width
        spacing: 6
        Rectangle {
            width: parent.width; height: PanelStyle.selectionRowHeight
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(editor.foreground, 0.04)
            Text {
                x: 10; anchors.verticalCenter: parent.verticalCenter
                text: Eitr.I18n.tr("HDR"); color: editor.foreground
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
            PanelSwitch {
                objectName: "hdrSwitch"
                anchors.right: parent.right; anchors.rightMargin: 4; anchors.verticalCenter: parent.verticalCenter
                foreground: editor.foreground; accent: editor.accent
                checked: !!editor.monitor.hdr
                enabled: !editor.busy
                onToggled: {
                    editor.choose("hdr", checked ? "on" : "off");
                    checked = Qt.binding(() => !!editor.monitor.hdr);
                }
            }
            HoverHandler { id: hdrHover }
            BarTooltip {
                target: parent; hovered: hdrHover.hovered
                text: Eitr.I18n.tr("Shows the desktop in HDR. Games can use HDR even when this is off.")
                background: editor.background; foreground: editor.foreground
            }
        }
        Column {
            SettingsTarget { objectName: "setting-displays-sdr-content-brightness" }
            visible: !!editor.monitor.hdr
            width: parent.width
            spacing: 2
            Caption {
                color: editor.foreground
                text: Eitr.I18n.tr("SDR content brightness") + " · " + Number(editor.monitor.sdr_brightness || 1).toFixed(1) + "×"
            }
            PanelSlider {
                objectName: "sdrBrightness"
                width: parent.width
                foreground: editor.foreground; accent: editor.accent
                from: 1; to: 2; stepSize: 0.1; ticks: 11
                value: Number(editor.monitor.sdr_brightness || 1)
                enabled: !editor.busy
                onMoved: brightnessSettle.restart()
                Timer {
                    id: brightnessSettle
                    interval: 180
                    onTriggered: editor.tryChange("sdr_brightness", parent.value.toFixed(1))
                }
            }
        }
    }
    ChoiceDropdown { SettingsTarget { objectName: "setting-displays-resolution" } background: editor.background; gold: editor.accent; label: Eitr.I18n.tr("Resolution"); width: parent.width; foreground: editor.foreground; choices: editor.resolutions.map(resolution => ({id: resolution, label: resolution.replace("x", "×")})); current: editor.currentResolution; available: !editor.busy; onChosen: value => editor.choose("mode", editor.modes.filter(mode => mode.split("@")[0] === value).sort((first, second) => Number(second.split("@")[1]) - Number(first.split("@")[1]))[0]) }
    ChoiceDropdown { SettingsTarget { objectName: "setting-displays-refresh-rate" } background: editor.background; gold: editor.accent; label: Eitr.I18n.tr("Refresh rate"); width: parent.width; foreground: editor.foreground; choices: editor.rates.map(rate => ({id: rate, label: Eitr.I18n.tr("{rate} Hz", {rate: Math.round(Number(rate))})})); current: String(editor.rates.find(rate => Math.abs(Number(rate) - editor.currentRate) < 0.01) || ""); available: !editor.busy; onChosen: value => editor.choose("mode", editor.currentResolution + "@" + value) }
    ChoiceDropdown { SettingsTarget { objectName: "setting-displays-scale" } background: editor.background; gold: editor.accent; label: Eitr.I18n.tr("Scale"); width: parent.width; foreground: editor.foreground; choices: editor.scales.map(scale => ({id: scale, label: Math.round(Number(scale) * 100) + "%"})); current: String(editor.monitor.scale || 1); available: !editor.busy; onChosen: value => editor.choose("scale", value) }
    ChoiceDropdown { SettingsTarget { objectName: "setting-displays-rotation" } background: editor.background; gold: editor.accent; label: Eitr.I18n.tr("Rotation"); width: parent.width; foreground: editor.foreground; choices: editor.rotations; current: editor.rotation; available: !editor.busy; onChosen: value => editor.choose("rotation", value) }
    SettingRow {
        SettingsTarget { objectName: "setting-displays-position" }
        visible: editor.others.length > 0
        label: Eitr.I18n.tr("Position"); value: editor.positionValue
        tint: editor.foreground; chevron: editor.accent
        interactive: !editor.isMain
        open: editor.openSetting === "position" && !editor.isMain; onToggled: editor.toggle("position")
    }
    Column {
        visible: editor.openSetting === "position" && editor.others.length > 0 && !editor.isMain
        width: parent.width
        spacing: 8
        Repeater {
            model: editor.placeable
            Column {
                id: neighbour
                required property string modelData
                width: editor.width
                spacing: 6
                Caption { color: editor.foreground; text: Eitr.I18n.tr("Beside %1", [neighbour.modelData]) }
                ChoiceSegmented { width: parent.width; foreground: editor.foreground; choices: editor.sides; current: editor.anchor && editor.anchor.of === neighbour.modelData ? editor.anchor.side : ""; available: !editor.busy; onChosen: value => editor.choose("position", value + ":" + neighbour.modelData + ":" + (editor.anchor ? editor.anchor.align : "start")) }
            }
        }
        Caption { color: editor.foreground; visible: !!editor.anchor; text: Eitr.I18n.tr("Align with %1", [editor.anchor ? editor.anchor.of : ""]) }
        ChoiceSegmented { visible: !!editor.anchor; width: parent.width; foreground: editor.foreground; choices: editor.aligns; current: editor.anchor ? editor.anchor.align : ""; available: !editor.busy; onChosen: value => editor.choose("position", editor.anchor.side + ":" + editor.anchor.of + ":" + value) }
    }
    ChoiceDropdown { SettingsTarget { objectName: "setting-displays-mirror" } background: editor.background; gold: editor.accent; visible: editor.others.length > 0; label: Eitr.I18n.tr("Mirror"); width: parent.width; foreground: editor.foreground; choices: [{id: "none", label: Eitr.I18n.tr("Off")}].concat(editor.others.map(name => ({id: name, label: name}))); current: editor.monitor.mirror || "none"; available: !editor.busy; onChosen: value => editor.choose("mirror", value) }
}

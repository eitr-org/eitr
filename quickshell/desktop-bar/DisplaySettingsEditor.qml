import QtQuick
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

// Resolution, refresh rate, HDR, scale, position and mirroring for one display, inside
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
    function choose(key, value) { openSetting = key === "position" ? openSetting : ""; tryChange(key, value); }

    // Inline components cannot see the editor's id; their colour and state are set where they are used.
    component Caption: Text {
        opacity: 0.65
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
    }
    component Choice: PanelButton {
        height: 28
        outlined: true
        textSize: PanelStyle.captionSize
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
        height: 34
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
        width: parent.width; height: 34
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
        visible: !!editor.monitor.hdr_capable
        width: parent.width
        spacing: 6
        Rectangle {
            width: parent.width; height: 34
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
        }
        Caption {
            width: parent.width
            wrapMode: Text.WordWrap
            color: editor.foreground
            text: Eitr.I18n.tr("Shows the desktop in HDR. Games can use HDR even when this is off.")
        }
        Caption {
            visible: !!editor.monitor.hdr_peak
            width: parent.width
            wrapMode: Text.WordWrap
            color: editor.foreground
            text: Eitr.I18n.tr("Peak brightness: {nits} nits. Use it as the maximum in a game's HDR settings.", {nits: editor.monitor.hdr_peak || 0})
        }
        Column {
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
                from: 1; to: 2; stepSize: 0.1
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
    SettingRow {
        label: Eitr.I18n.tr("Resolution"); value: editor.currentResolution.replace("x", "×")
        tint: editor.foreground; chevron: editor.accent
        open: editor.openSetting === "resolution"; onToggled: editor.toggle("resolution")
    }
    Flow {
        id: resolutionFlow
        visible: editor.openSetting === "resolution"
        width: parent.width
        spacing: 6
        Repeater {
            model: editor.resolutions
            Choice {
                foreground: editor.foreground
                available: !editor.busy
                required property string modelData
                width: (resolutionFlow.width - resolutionFlow.spacing * 2) / 3
                text: modelData.replace("x", "×")
                selected: modelData === editor.currentResolution
                // The new resolution starts at its highest refresh rate.
                onClicked: if (!selected) editor.choose("mode",
                    editor.modes.filter(mode => mode.split("@")[0] === modelData)
                        .sort((first, second) => Number(second.split("@")[1]) - Number(first.split("@")[1]))[0])
            }
        }
    }
    SettingRow {
        label: Eitr.I18n.tr("Refresh rate"); value: Eitr.I18n.tr("{rate} Hz", {rate: Math.round(editor.currentRate)})
        tint: editor.foreground; chevron: editor.accent
        open: editor.openSetting === "rate"; onToggled: editor.toggle("rate")
    }
    Flow {
        id: rateFlow
        visible: editor.openSetting === "rate"
        width: parent.width
        spacing: 6
        Repeater {
            model: editor.rates
            Choice {
                foreground: editor.foreground
                available: !editor.busy
                required property string modelData
                width: (rateFlow.width - rateFlow.spacing * 3) / 4
                text: Eitr.I18n.tr("{rate} Hz", {rate: Math.round(Number(modelData))})
                selected: Math.abs(Number(modelData) - editor.currentRate) < 0.01
                onClicked: if (!selected) editor.choose("mode", editor.currentResolution + "@" + modelData)
            }
        }
    }
    SettingRow {
        label: Eitr.I18n.tr("Scale"); value: Math.round(Number(editor.monitor.scale || 1) * 100) + "%"
        tint: editor.foreground; chevron: editor.accent
        open: editor.openSetting === "scale"; onToggled: editor.toggle("scale")
    }
    Row {
        id: scaleRow
        visible: editor.openSetting === "scale"
        width: parent.width
        spacing: 6
        Repeater {
            model: editor.scales
            Choice {
                foreground: editor.foreground
                available: !editor.busy
                required property string modelData
                width: (scaleRow.width - scaleRow.spacing * 4) / 5
                text: Math.round(Number(modelData) * 100) + "%"
                selected: Math.abs(Number(modelData) - Number(editor.monitor.scale)) < 0.01
                onClicked: if (!selected) editor.choose("scale", modelData)
            }
        }
    }
    SettingRow {
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
                Row {
                    id: sideRow
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: editor.sides
                        Choice {
                            foreground: editor.foreground
                            available: !editor.busy
                            required property var modelData
                            width: (sideRow.width - sideRow.spacing * 3) / 4
                            text: modelData.label
                            selected: !!editor.anchor && editor.anchor.of === neighbour.modelData && editor.anchor.side === modelData.key
                            onClicked: if (!selected) editor.choose("position", modelData.key + ":" + neighbour.modelData
                                + ":" + (editor.anchor ? editor.anchor.align : "start"))
                        }
                    }
                }
            }
        }
        Caption { color: editor.foreground; visible: !!editor.anchor; text: Eitr.I18n.tr("Align with %1", [editor.anchor ? editor.anchor.of : ""]) }
        Row {
            id: alignRow
            visible: !!editor.anchor
            width: parent.width
            spacing: 6
            Repeater {
                model: editor.aligns
                Choice {
                    foreground: editor.foreground
                    available: !editor.busy
                    required property var modelData
                    width: (alignRow.width - alignRow.spacing * 2) / 3
                    text: modelData.label
                    selected: !!editor.anchor && editor.anchor.align === modelData.key
                    onClicked: if (!selected) editor.choose("position", editor.anchor.side + ":" + editor.anchor.of + ":" + modelData.key)
                }
            }
        }
    }
    SettingRow {
        visible: editor.others.length > 0
        label: Eitr.I18n.tr("Mirror"); value: editor.monitor.mirror || Eitr.I18n.tr("Off")
        tint: editor.foreground; chevron: editor.accent
        open: editor.openSetting === "mirror"; onToggled: editor.toggle("mirror")
    }
    Flow {
        id: mirrorFlow
        visible: editor.openSetting === "mirror" && editor.others.length > 0
        width: parent.width
        spacing: 6
        Repeater {
            model: ["none"].concat(editor.others)
            Choice {
                foreground: editor.foreground
                available: !editor.busy
                required property string modelData
                width: (mirrorFlow.width - mirrorFlow.spacing * 2) / 3
                text: modelData === "none" ? Eitr.I18n.tr("Off") : modelData
                selected: (editor.monitor.mirror || "none") === modelData
                onClicked: if (!selected) editor.choose("mirror", modelData)
            }
        }
    }
}

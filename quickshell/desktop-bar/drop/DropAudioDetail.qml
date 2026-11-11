import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import Quickshell.Services.Pipewire
import "../PanelStyle.js" as PanelStyle

// Sound or microphone opened in Drop's quick controls: the level, then every device as a
// row (a card's other ports too, such as a second monitor), so switching between headset and
// speakers is one click.
Column {
    id: detail
    required property bool microphone
    required property color foreground
    required property color background
    required property color accent
    readonly property PwNode current: microphone ? Pipewire.defaultAudioSource : Pipewire.defaultAudioSink
    readonly property var nodes: Pipewire.nodes.values.filter(node => node.audio && !node.isStream && node.isSink !== microphone)
    readonly property var devices: AudioDevices.choices(nodes, microphone)
    readonly property string currentValue: current ? String(current.id) : ""
    onVisibleChanged: AudioDevices.watch(visible)
    Component.onCompleted: if (visible) AudioDevices.watch(true)
    Component.onDestruction: if (visible) AudioDevices.watch(false)
    spacing: PanelStyle.selectionRowGap

    AudioLevelControl {
        width: parent.width
        node: detail.current; microphone: detail.microphone; showName: false; textSize: 12; iconSize: 16
        foreground: detail.foreground; background: detail.background; accent: detail.accent
    }
    Item { width: 1; height: 6 }
    Text {
        text: detail.microphone ? Eitr.I18n.tr("INPUT DEVICE") : Eitr.I18n.tr("OUTPUT DEVICE")
        color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    Text {
        visible: detail.devices.length === 0
        text: Eitr.I18n.tr("No device available")
        color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize
    }
    Repeater {
        model: detail.devices
        Rectangle {
            id: row
            required property var modelData
            readonly property bool chosen: modelData.value === detail.currentValue
            width: detail.width; height: PanelStyle.selectionRowHeight
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(detail.foreground, PanelStyle.selectionAlpha(chosen, mouse.containsMouse))
            border.width: PanelStyle.selectionBorderWidth(chosen)
            border.color: Qt.alpha(detail.foreground, PanelStyle.selectionBorderAlpha)
            Text {
                x: PanelStyle.selectionInset; width: 20; horizontalAlignment: Text.AlignHCenter
                anchors.verticalCenter: parent.verticalCenter
                text: row.modelData.glyph
                color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.selectionIconSize
            }
            Text {
                x: PanelStyle.selectionTextInset; width: parent.width - x - 36
                anchors.verticalCenter: parent.verticalCenter
                text: row.modelData.label; elide: Text.ElideRight; textFormat: Text.PlainText
                color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            }
            Text {
                visible: row.chosen
                anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter
                text: "\u{F00C}"; color: detail.accent
                font.family: DesktopFonts.family; font.pixelSize: 13
            }
            MouseArea {
                id: mouse
                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                enabled: !row.chosen
                onClicked: AudioDevices.choose(row.modelData.value, detail.nodes, detail.microphone)
            }
        }
    }
}

import Eitr as Eitr
import QtQuick
// Audio controls and the live input meter share this panel's lifecycle.
import "PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Services.Pipewire

ThemedPopup {
    id: menu
    property bool microphone: false
    property int maximumHeight: 700
    readonly property PwNode currentNode: microphone ? Pipewire.defaultAudioSource : Pipewire.defaultAudioSink
    readonly property var devices: Pipewire.nodes.values.filter(node => node.audio && !node.isStream && node.isSink !== microphone)
    readonly property var streams: microphone ? [] : Pipewire.nodes.values.filter(node => node.type === PwNodeType.AudioOutStream)
    PwNodePeakMonitor {
        id: inputPeak
        node: menu.microphone ? menu.currentNode : null
        enabled: menu.opened && menu.microphone && menu.currentNode !== null
    }

    implicitWidth: 428
    implicitHeight: Math.min(content.implicitHeight + verticalContentInset, maximumHeight)

    Flickable {
        anchors.fill: parent
        anchors.margins: 0
        contentHeight: content.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: content
            width: parent.width
            spacing: 12
            PanelHeading {
                text: menu.microphone ? Eitr.I18n.tr("Microphone") : Eitr.I18n.tr("Volume")
                foreground: menu.foreground; accent: menu.accent; rune: "audio"
            }
            AudioLevelControl {
                width: parent.width
                node: menu.currentNode
                microphone: menu.microphone
                name: node ? (node.description || node.nickname || node.name) : "No device available"
                accent: menu.accent
                foreground: menu.foreground
                background: menu.background
            }
            MicrophoneMeter {
                visible: menu.microphone
                width: parent.width
                peak: inputPeak.peak
                muted: !menu.currentNode || !menu.currentNode.audio || menu.currentNode.audio.muted
                foreground: menu.foreground
                accent: menu.accent
            }
            PanelDivider {
                width: parent.width
                height: 8
                foreground: menu.foreground
            }
            Text {
                text: menu.microphone ? Eitr.I18n.tr("Input device") : Eitr.I18n.tr("Output device")
                color: menu.foreground
                opacity: 0.65
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.secondarySize
            }
            Column {
                width: parent.width
                spacing: PanelStyle.selectionRowGap
                Repeater {
                    model: menu.devices
                    Rectangle {
                        id: device
                        required property PwNode modelData
                        width: content.width
                        height: PanelStyle.selectionRowHeight
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        color: Qt.alpha(menu.foreground, PanelStyle.selectionAlpha(menu.currentNode === modelData, deviceMouse.containsMouse))
                        border.width: PanelStyle.selectionBorderWidth(menu.currentNode === modelData)
                        border.color: Qt.alpha(menu.foreground, PanelStyle.selectionBorderAlpha)
                        Text {
                            x: PanelStyle.selectionInset
                            anchors.verticalCenter: parent.verticalCenter
                            text: menu.currentNode === device.modelData ? "" : ""
                            color: menu.accent
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.selectionIconSize
                        }
                        Text {
                            x: PanelStyle.selectionTextInset
                            width: parent.width - x - PanelStyle.selectionInset
                            anchors.verticalCenter: parent.verticalCenter
                            text: device.modelData.description || device.modelData.nickname || device.modelData.name
                            elide: Text.ElideRight
                            color: menu.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                        }
                        MouseArea {
                            id: deviceMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (menu.microphone) Pipewire.preferredDefaultAudioSource = device.modelData;
                                else Pipewire.preferredDefaultAudioSink = device.modelData;
                            }
                        }
                    }
                }
                Text {
                    visible: menu.devices.length === 0
                    text: Eitr.I18n.tr("No devices available")
                    color: menu.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
            }
            PanelDivider {
                visible: !menu.microphone
                width: parent.width
                height: 8
                foreground: menu.foreground
            }
            Text {
                visible: !menu.microphone
                text: Eitr.I18n.tr("Applications")
                color: menu.foreground
                opacity: 0.65
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.secondarySize
            }
            Repeater {
                model: menu.streams
                AudioLevelControl {
                    required property PwNode modelData
                    width: content.width
                    node: modelData
                    accent: menu.accent
                    foreground: menu.foreground
                    background: menu.background
                }
            }
            Text {
                visible: !menu.microphone && menu.streams.length === 0
                text: Eitr.I18n.tr("No playback applications")
                color: menu.foreground
                opacity: 0.65
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
        }
    }
}

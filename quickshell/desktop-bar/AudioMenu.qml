import Eitr as Eitr
import QtQuick
// Audio controls and the live input meter share this panel's lifecycle.
import "PanelStyle.js" as PanelStyle
import Quickshell.Services.Pipewire

ThemedPopup {
    id: menu
    property int maximumHeight: 700
    property bool microphone: false
    implicitWidth: 428
    implicitHeight: Math.min(content.implicitHeight + verticalContentInset, maximumHeight)
    function scrollToSelection() {
        scroll.contentY = microphone ? Math.min(inputSection.y, Math.max(0, scroll.contentHeight - scroll.height)) : 0;
    }
    onOpenedChanged: if (opened) Qt.callLater(scrollToSelection)
    onMicrophoneChanged: if (opened) Qt.callLater(scrollToSelection)

    component AudioSection: Column {
        id: section
        required property bool microphone
        required property bool active
        required property color foreground
        required property color accent
        required property color background
        property var nodes: Pipewire.nodes.values
        property PwNode currentNode: microphone ? Pipewire.defaultAudioSource : Pipewire.defaultAudioSink
        readonly property var devices: nodes.filter(node => node.audio && !node.isStream && node.isSink !== microphone)
        readonly property var streams: microphone ? [] : nodes.filter(node => node.type === PwNodeType.AudioOutStream)
        spacing: 12
        PwNodePeakMonitor {
            id: inputPeak
            node: section.microphone ? section.currentNode : null
            enabled: section.active && section.microphone && section.currentNode !== null
        }
        PanelHeading {
            text: section.microphone ? Eitr.I18n.tr("Microphone") : Eitr.I18n.tr("Volume")
            foreground: section.foreground; accent: section.accent; rune: "audio"
        }
        AudioLevelControl {
            width: parent.width
            node: section.currentNode
            microphone: section.microphone
            name: node ? (node.description || node.nickname || node.name) : Eitr.I18n.tr("No device available")
            accent: section.accent
            foreground: section.foreground
            background: section.background
        }
        MicrophoneMeter {
            visible: section.microphone
            width: parent.width
            peak: inputPeak.peak
            muted: !section.currentNode || !section.currentNode.audio || section.currentNode.audio.muted
            foreground: section.foreground
            accent: section.accent
        }
        PanelDivider {
            width: parent.width
            height: 8
            foreground: section.foreground
        }
        Text {
            text: section.microphone ? Eitr.I18n.tr("Input device") : Eitr.I18n.tr("Output device")
            color: section.foreground
            opacity: 0.65
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.secondarySize
        }
        Column {
            width: parent.width
            spacing: PanelStyle.selectionRowGap
            Repeater {
                model: section.devices
                Rectangle {
                    id: device
                    required property PwNode modelData
                    width: section.width
                    height: PanelStyle.selectionRowHeight
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    color: Qt.alpha(section.foreground, PanelStyle.selectionAlpha(section.currentNode === modelData, deviceMouse.containsMouse))
                    border.width: PanelStyle.selectionBorderWidth(section.currentNode === modelData)
                    border.color: Qt.alpha(section.foreground, PanelStyle.selectionBorderAlpha)
                    Text {
                        x: PanelStyle.selectionInset
                        anchors.verticalCenter: parent.verticalCenter
                        text: section.currentNode === device.modelData ? "" : ""
                        color: section.accent
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.selectionIconSize
                    }
                    Text {
                        x: PanelStyle.selectionTextInset
                        width: parent.width - x - PanelStyle.selectionInset
                        anchors.verticalCenter: parent.verticalCenter
                        text: device.modelData.description || device.modelData.nickname || device.modelData.name
                        elide: Text.ElideRight
                        color: section.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.bodySize
                    }
                    MouseArea {
                        id: deviceMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (section.microphone) Pipewire.preferredDefaultAudioSource = device.modelData;
                            else Pipewire.preferredDefaultAudioSink = device.modelData;
                        }
                    }
                }
            }
            Text {
                visible: section.devices.length === 0
                text: Eitr.I18n.tr("No devices available")
                color: section.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
        }
        PanelDivider {
            visible: !section.microphone
            width: parent.width
            height: 8
            foreground: section.foreground
        }
        Text {
            visible: !section.microphone
            text: Eitr.I18n.tr("Applications")
            color: section.foreground
            opacity: 0.65
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.secondarySize
        }
        Repeater {
            model: section.streams
            AudioLevelControl {
                required property PwNode modelData
                width: section.width
                node: modelData
                accent: section.accent
                foreground: section.foreground
                background: section.background
            }
        }
        Text {
            visible: !section.microphone && section.streams.length === 0
            text: Eitr.I18n.tr("No playback applications")
            color: section.foreground
            opacity: 0.65
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
        }
    }

    Flickable {
        id: scroll
        anchors.fill: parent
        anchors.margins: 0
        contentHeight: content.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: content
            width: parent.width
            spacing: 18
            AudioSection {
                width: parent.width
                microphone: false
                active: menu.opened
                foreground: menu.foreground
                accent: menu.accent
                background: menu.background
            }
            PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
            AudioSection {
                id: inputSection
                width: parent.width
                microphone: true
                active: menu.opened
                foreground: menu.foreground
                accent: menu.accent
                background: menu.background
            }
        }
    }
}

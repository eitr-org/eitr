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
    onOpenedChanged: if (opened) scrollToSelection()
    onMicrophoneChanged: if (opened) Qt.callLater(scrollToSelection)

    component AudioSection: Column {
        id: section
        required property bool microphone
        required property bool active
        required property color foreground
        required property color accent
        required property color background
        property var nodes: []
        readonly property var availableNodes: Pipewire.nodes.values
        onAvailableNodesChanged: menu.updateContent(function() {
            const next = section.availableNodes;
            if (section.nodes.length !== next.length || section.nodes.some((node, index) => node !== next[index])) section.nodes = next;
        })
        Component.onCompleted: nodes = availableNodes
        property PwNode currentNode: microphone ? Pipewire.defaultAudioSource : Pipewire.defaultAudioSink
        property bool picking: false
        onActiveChanged: if (!active) picking = false
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
            showName: false
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
        // The current device, as a compact picker: the full list unfolds on click.
        Rectangle {
            id: picker
            width: parent.width
            height: PanelStyle.selectionRowHeight
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(section.foreground, PanelStyle.selectionAlpha(false, pickerMouse.containsMouse || picker.activeFocus))
            border.width: PanelStyle.selectionBorderWidth(false)
            border.color: Qt.alpha(section.foreground, PanelStyle.selectionBorderAlpha)
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: section.microphone ? Eitr.I18n.tr("Input device") : Eitr.I18n.tr("Output device")
            Keys.onPressed: function(event) {
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) { section.picking = !section.picking; event.accepted = true; }
            }
            Text {
                width: PanelStyle.selectionTextInset
                anchors.verticalCenter: parent.verticalCenter
                horizontalAlignment: Text.AlignHCenter
                text: AudioDevices.glyph(section.currentNode, section.microphone)
                color: section.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.selectionIconSize
            }
            Text {
                x: PanelStyle.selectionTextInset
                width: parent.width - x - 32
                anchors.verticalCenter: parent.verticalCenter
                text: section.currentNode ? AudioDevices.label(section.currentNode) : Eitr.I18n.tr("No device available")
                elide: Text.ElideRight
                color: section.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
            Text {
                anchors.right: parent.right
                anchors.rightMargin: PanelStyle.selectionInset
                anchors.verticalCenter: parent.verticalCenter
                visible: section.devices.length > 1 || section.picking
                text: section.picking ? "\u{F0143}" : "\u{F0140}"
                color: section.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: 16
            }
            MouseArea {
                id: pickerMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: section.picking = !section.picking
            }
        }
        Column {
            visible: section.picking
            width: parent.width
            spacing: PanelStyle.selectionRowGap
            Repeater {
                model: section.devices
                Rectangle {
                    id: device
                    required property PwNode modelData
                    readonly property bool current: section.currentNode === modelData
                    property bool editing: false
                    width: section.width
                    height: PanelStyle.selectionRowHeight
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    color: Qt.alpha(section.foreground, PanelStyle.selectionAlpha(current, deviceMouse.containsMouse))
                    border.width: PanelStyle.selectionBorderWidth(current)
                    border.color: Qt.alpha(section.foreground, PanelStyle.selectionBorderAlpha)
                    function finishRename(save) {
                        if (save) AudioDevices.rename(device.modelData, nameInput.text);
                        editing = false;
                    }
                    Text {
                        width: PanelStyle.selectionTextInset
                        anchors.verticalCenter: parent.verticalCenter
                        horizontalAlignment: Text.AlignHCenter
                        text: device.current ? "\u{F012C}" : AudioDevices.glyph(device.modelData, section.microphone)
                        color: device.current ? section.accent : section.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.selectionIconSize
                    }
                    Text {
                        visible: !device.editing
                        x: PanelStyle.selectionTextInset
                        width: parent.width - x - PanelStyle.selectionActionWidth - 2 * PanelStyle.selectionActionInset
                        anchors.verticalCenter: parent.verticalCenter
                        text: AudioDevices.label(device.modelData)
                        elide: Text.ElideRight
                        color: section.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.bodySize
                    }
                    TextInput {
                        id: nameInput
                        visible: device.editing
                        x: PanelStyle.selectionTextInset
                        width: parent.width - x - PanelStyle.selectionActionWidth - 2 * PanelStyle.selectionActionInset
                        anchors.verticalCenter: parent.verticalCenter
                        color: section.foreground
                        selectionColor: Qt.alpha(section.accent, 0.4)
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.bodySize
                        clip: true
                        Keys.onReturnPressed: device.finishRename(true)
                        Keys.onEnterPressed: device.finishRename(true)
                        Keys.onEscapePressed: function(event) { device.finishRename(false); event.accepted = true; }
                        onActiveFocusChanged: if (!activeFocus && device.editing) device.finishRename(true)
                    }
                    MouseArea {
                        id: deviceMouse
                        anchors.fill: parent
                        enabled: !device.editing
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (section.microphone) Pipewire.preferredDefaultAudioSource = device.modelData;
                            else Pipewire.preferredDefaultAudioSink = device.modelData;
                            section.picking = false;
                        }
                    }
                    PanelButton {
                        id: renameButton
                        anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter
                        width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
                        visible: deviceMouse.containsMouse || renameHover.hovered || device.editing
                        icon: true; text: device.editing ? "\u{F012C}" : "\u{F03EB}"; iconSize: 14; foreground: section.foreground
                        Accessible.name: Eitr.I18n.tr("Rename")
                        onClicked: {
                            if (device.editing) { device.finishRename(true); return; }
                            nameInput.text = AudioDevices.label(device.modelData);
                            device.editing = true;
                            nameInput.forceActiveFocus();
                            nameInput.selectAll();
                        }
                        HoverHandler { id: renameHover }
                        BarTooltip { target: renameButton; hovered: renameHover.hovered; text: device.editing ? Eitr.I18n.tr("Save") : Eitr.I18n.tr("Rename"); foreground: section.foreground; background: section.background }
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
            opacity: PanelStyle.secondaryTextOpacity
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
            opacity: PanelStyle.secondaryTextOpacity
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
                active: menu.opened && menu.revealProgress === 1
                foreground: menu.foreground
                accent: menu.accent
                background: menu.background
            }
            PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
            AudioSection {
                id: inputSection
                width: parent.width
                microphone: true
                active: menu.opened && menu.revealProgress === 1
                foreground: menu.foreground
                accent: menu.accent
                background: menu.background
            }
        }
    }
}

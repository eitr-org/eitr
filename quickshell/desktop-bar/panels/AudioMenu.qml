import ".."
import Eitr as Eitr
import QtQuick
// Audio controls and the live input meter share this panel's lifecycle.
import "../PanelStyle.js" as PanelStyle
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
        property PwNode renaming: null
        onActiveChanged: if (!active) { picker.expanded = false; renaming = null; }
        function deviceFor(value) { return devices.find(node => String(node.id) === value) || null; }
        function startRename(node) {
            if (!node) return;
            renaming = node;
            nameInput.text = AudioDevices.label(node);
            nameInput.forceActiveFocus();
            nameInput.selectAll();
        }
        function finishRename(save) {
            const node = renaming;
            renaming = null;
            if (save && node) AudioDevices.rename(node, nameInput.text);
            picker.forceActiveFocus();
        }
        readonly property var devices: nodes.filter(node => node.audio && !node.isStream && node.isSink !== microphone)
        readonly property var streams: microphone ? [] : nodes.filter(node => node.type === PwNodeType.AudioOutStream)
        spacing: 12
        PwNodePeakMonitor {
            id: inputPeak
            node: section.microphone ? section.currentNode : null
            enabled: section.active && section.microphone && section.currentNode !== null
        }
        PanelHeading { compact: menu.embedded; visible: !menu.embedded;
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
        // The current device; the other devices float over the panel on click, each with Rename.
        ChoiceDropdown {
            id: picker
            visible: section.renaming === null
            width: parent.width
            foreground: section.foreground; background: section.background; gold: section.accent
            floatingLabel: section.microphone ? Eitr.I18n.tr("Input device") : Eitr.I18n.tr("Output device")
            placeholder: Eitr.I18n.tr("No device available")
            choices: section.devices.map(node => ({value: String(node.id), label: AudioDevices.label(node), glyph: AudioDevices.glyph(node, section.microphone)}))
            current: section.currentNode ? String(section.currentNode.id) : ""
            actionGlyph: "\u{F03EB}"; actionName: Eitr.I18n.tr("Rename")
            onChosen: value => {
                const node = section.deviceFor(value);
                if (!node) return;
                if (section.microphone) Pipewire.preferredDefaultAudioSource = node;
                else Pipewire.preferredDefaultAudioSink = node;
            }
            onActionTriggered: value => section.startRename(section.deviceFor(value))
        }
        // Renaming replaces the picker row with a text field: Enter saves, Escape cancels.
        Rectangle {
            visible: section.renaming !== null
            width: parent.width
            height: PanelStyle.selectionRowHeight
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(section.foreground, PanelStyle.selectionAlpha(true, false))
            border.width: PanelStyle.selectionBorderWidth(true)
            border.color: Qt.alpha(section.foreground, PanelStyle.selectionBorderAlpha)
            Text {
                width: PanelStyle.selectionTextInset
                anchors.verticalCenter: parent.verticalCenter
                horizontalAlignment: Text.AlignHCenter
                text: AudioDevices.glyph(section.renaming, section.microphone)
                color: section.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.selectionIconSize
            }
            TextInput {
                id: nameInput
                objectName: "audioDeviceName"
                x: PanelStyle.selectionTextInset
                width: parent.width - x - PanelStyle.selectionActionWidth - 2 * PanelStyle.selectionActionInset
                anchors.verticalCenter: parent.verticalCenter
                color: section.foreground
                selectionColor: Qt.alpha(section.accent, 0.4)
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                clip: true
                Accessible.name: Eitr.I18n.tr("Rename")
                Keys.onReturnPressed: section.finishRename(true)
                Keys.onEnterPressed: section.finishRename(true)
                Keys.onEscapePressed: function(event) { section.finishRename(false); event.accepted = true; }
                onActiveFocusChanged: if (!activeFocus && section.renaming !== null) section.finishRename(true)
            }
            PanelButton {
                id: saveName
                anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter
                width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
                icon: true; text: "\u{F012C}"; iconSize: 14; foreground: section.foreground
                Accessible.name: Eitr.I18n.tr("Save")
                onClicked: section.finishRename(true)
                HoverHandler { id: saveHover }
                BarTooltip { target: saveName; hovered: saveHover.hovered; text: Eitr.I18n.tr("Save"); foreground: section.foreground; background: section.background }
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

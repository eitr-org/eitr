import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell.Services.Pipewire
import Eitr as Eitr

ControlCard {
    id: card
    required property color background
    required property color accent
    required property var nodes
    required property bool microphone
    property bool active: false
    property bool live: true
    readonly property var devices: nodes.filter(node => node.audio && !node.isStream && node.isSink !== microphone)
    readonly property PwNode currentNode: microphone ? Pipewire.defaultAudioSource : Pipewire.defaultAudioSink
    property PwNode renaming: null
    title: microphone ? Eitr.I18n.tr("Input") : Eitr.I18n.tr("Output")
    surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
    ChoiceDropdown {
        floatingLabel: card.microphone ? Eitr.I18n.tr("Input device") : Eitr.I18n.tr("Output device")
        helperText: card.microphone ? Eitr.I18n.tr("Choose the microphone used to record sound.") : Eitr.I18n.tr("Choose where sound is played.")
        width: Math.min(parent.width, 460)
        SettingsTarget { objectName: card.microphone ? "setting-sound-input-device" : "setting-sound-output-device" }
        SettingsTarget { objectName: card.microphone ? "setting-sound-input-rename" : "setting-sound-output-rename" }
        visible: !card.renaming
        foreground: card.foreground; background: card.background; gold: SettingsInk.gold
        accessibleName: card.microphone ? Eitr.I18n.tr("Input device") : Eitr.I18n.tr("Output device")
        choices: card.devices.map(node => ({value: String(node.id), label: AudioDevices.label(node), glyph: AudioDevices.glyph(node, card.microphone)}))
        current: card.currentNode ? String(card.currentNode.id) : ""
        actionGlyph: "\u{F03EB}"; actionName: Eitr.I18n.tr("Rename")
        onChosen: value => {
            if (!card.live) return;
            const node = card.devices.find(device => String(device.id) === value);
            if (card.microphone) Pipewire.preferredDefaultAudioSource = node;
            else Pipewire.preferredDefaultAudioSink = node;
        }
        onActionTriggered: value => {
            card.renaming = card.devices.find(device => String(device.id) === value);
            nameInput.text = AudioDevices.label(card.renaming);
            nameInput.forceActiveFocus(); nameInput.selectAll();
        }
    }
    OutlinedTextField {
        id: nameInput
        visible: !!card.renaming
        width: Math.min(parent.width, 460)
        foreground: card.foreground; accent: SettingsInk.gold
        label: Eitr.I18n.tr("Name")
        helperText: Eitr.I18n.tr("Enter saves the new name; Esc cancels.")
        onAccepted: { if (card.live && card.renaming) AudioDevices.rename(card.renaming, text); card.renaming = null; }
        onCancelled: card.renaming = null
    }
    ControlRow {
        SettingsTarget { objectName: card.microphone ? "setting-sound-input-volume" : "setting-sound-output-volume" }
        SettingsTarget { objectName: card.microphone ? "setting-sound-input-mute" : "setting-sound-output-mute" }
        text: Eitr.I18n.tr("Volume")
        description: Eitr.I18n.tr("Adjust the volume or mute this device.")
        foreground: card.foreground
        controlWidth: Math.min(460, width * 0.65)
        AudioLevelControl {
            width: parent.width
            node: card.currentNode; microphone: card.microphone; showName: false
            enabled: card.live
            foreground: card.foreground; background: card.background; accent: card.accent
        }
    }
    PwNodePeakMonitor {
        id: inputPeak
        node: card.microphone ? card.currentNode : null
        enabled: card.live && card.active && card.microphone && card.currentNode !== null
    }
    ControlRow {
        visible: card.microphone
        text: Eitr.I18n.tr("Input level")
        description: Eitr.I18n.tr("See how much sound the microphone picks up.")
        foreground: card.foreground
        controlWidth: Math.min(360, width * 0.5)
        MicrophoneMeter {
            width: parent.width; peak: inputPeak.peak
            muted: !card.currentNode || !card.currentNode.audio || card.currentNode.audio.muted
            foreground: card.foreground; accent: card.accent
        }
    }
}

import ".."
import QtQuick
import Quickshell.Services.Pipewire
import Eitr as Eitr

Column {
    id: page
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    readonly property var nodes: Pipewire.nodes.values
    readonly property var streams: nodes.filter(node => node.type === PwNodeType.AudioOutStream)
    width: parent ? parent.width : 0
    spacing: 18
    Repeater {
        model: [false, true]
        SettingsAudioDeviceCard {
            required property bool modelData
            width: page.width
            microphone: modelData
            nodes: page.nodes
            foreground: page.foreground; background: page.background; accent: page.accent
            active: page.active; live: page.live
        }
    }
    ControlCard {
        title: Eitr.I18n.tr("Applications")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        Repeater {
            model: page.streams
            ControlRow {
                id: appRow
                required property PwNode modelData
                text: modelData.properties["application.name"] || AudioDevices.label(modelData)
                description: ""
                foreground: page.foreground
                controlWidth: Math.min(460, width * 0.65)
                AudioLevelControl {
                    width: parent.width; node: appRow.modelData
                    showName: false
                    enabled: page.live
                    foreground: page.foreground; background: page.background; accent: page.accent
                }
            }
        }
        SettingsText { visible: !page.streams.length; text: Eitr.I18n.tr("No applications are playing audio.") }
    }
    ControlCard {
        title: Eitr.I18n.tr("Event sounds")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        EventSoundSettings {
            width: parent.width
            foreground: page.foreground; accent: page.accent; live: page.live
            hasBattery: page.active && PowerService.battery.available
        }
    }
}

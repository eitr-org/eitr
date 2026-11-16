import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import Quickshell.Services.Pipewire
import QtQuick.Layouts
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "general"
    width: parent.width; spacing: 12
    ControlCenterSection { centerRef: section.centerRef; text: Eitr.I18n.tr("Sound"); width: parent.width }
    // Sound and Microphone open their devices in place; the switch there mutes or unmutes.
    readonly property var sink: Pipewire.defaultAudioSink
    readonly property var source: Pipewire.defaultAudioSource
    PwObjectTracker { objects: [section.sink, section.source] }
    GridLayout {
        width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
        ControlCenterToggleTile { centerRef: section.centerRef
            title: Eitr.I18n.tr("Sound"); glyph: section.sink && section.sink.audio && section.sink.audio.muted ? "󰖁" : "󰕾"
            selected: !!section.sink && !!section.sink.audio && !section.sink.audio.muted
            details: true
            onClicked: section.centerRef.detail = "sound"
            onDetailsRequested: section.centerRef.detail = "sound"
        }
        ControlCenterToggleTile { centerRef: section.centerRef
            title: Eitr.I18n.tr("Microphone"); glyph: section.source && section.source.audio && section.source.audio.muted ? "󰍭" : "󰍬"
            selected: !!section.source && !!section.source.audio && !section.source.audio.muted
            details: true
            onClicked: section.centerRef.detail = "microphone"
            onDetailsRequested: section.centerRef.detail = "microphone"
        }
    }
    AudioLevelControl { width: parent.width; node: Pipewire.defaultAudioSink; showName: false; textSize: 12; iconSize: 16; foreground: section.centerRef.foreground; background: section.centerRef.background; accent: section.centerRef.accent }
    AudioLevelControl { width: parent.width; node: Pipewire.defaultAudioSource; microphone: true; showName: false; textSize: 12; iconSize: 16; foreground: section.centerRef.foreground; background: section.centerRef.background; accent: section.centerRef.accent }
    EventSoundSettings {
        width: parent.width
        foreground: section.centerRef.foreground; accent: section.centerRef.accent
        hasBattery: !!(section.centerRef.battery && section.centerRef.battery.available)
    }
    ControlCenterSection { centerRef: section.centerRef; visible: section.centerRef.displayControl.state.kind === "backlight"; text: Eitr.I18n.tr("Display"); width: parent.width }
    BrightnessSlider {
        width: parent.width
        displayControl: section.centerRef.displayControl
        foreground: section.centerRef.foreground; accent: section.centerRef.accent
    }
    // Drop has its own Media page, so the embedded Control Center leaves this out.
    ControlCenterSection { centerRef: section.centerRef; visible: !!section.centerRef.mediaPlayer && !section.centerRef.embedded; text: Eitr.I18n.tr("Media"); width: parent.width }
    MediaCard { compact: true; visible: !!section.centerRef.mediaPlayer && !section.centerRef.embedded; width: parent.width; player: section.centerRef.mediaPlayer; active: section.centerRef.opened && section.centerRef.page === "general"; foreground: section.centerRef.foreground; accent: section.centerRef.accent }
}

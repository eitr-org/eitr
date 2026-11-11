import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import Quickshell.Services.Pipewire
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "general"
    width: parent.width; spacing: 12
    ControlCenterSection { centerRef: section.centerRef; text: Eitr.I18n.tr("Sound"); width: parent.width }
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
    ControlCenterSection { centerRef: section.centerRef; visible: !!section.centerRef.mediaPlayer; text: Eitr.I18n.tr("Media"); width: parent.width }
    MediaCard { compact: true; visible: !!section.centerRef.mediaPlayer; width: parent.width; player: section.centerRef.mediaPlayer; active: section.centerRef.opened && section.centerRef.page === "general"; foreground: section.centerRef.foreground; accent: section.centerRef.accent }
}

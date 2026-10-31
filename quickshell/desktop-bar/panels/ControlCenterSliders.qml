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
    ControlCenterSection { centerRef: section.centerRef; visible: section.centerRef.displayControl.state.kind === "backlight"; text: Eitr.I18n.tr("Display"); width: parent.width }
    Row {
        visible: section.centerRef.displayControl.state.kind === "backlight"
        width: parent.width; spacing: 10
        Text { width: 30; height: 30; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; text: "󰃟"; color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: 16 }
        PanelSlider {
            id: brightnessSlider
            width: parent.width - 100; from: 1; to: 100
            foreground: section.centerRef.foreground; accent: section.centerRef.accent
            enabled: !!section.centerRef.displayControl.state.available
            Binding { target: brightnessSlider; property: "value"; value: section.centerRef.displayControl.state.value; when: !brightnessSlider.pressed }
            onMoved: brightnessSettle.restart()
            Timer { id: brightnessSettle; interval: 120; onTriggered: section.centerRef.displayControl.applyValue(Math.round(brightnessSlider.value)) }
        }
        Text { width: 50; height: 30; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignRight; text: section.centerRef.displayControl.state.available ? section.centerRef.displayControl.state.value + "%" : "--"; color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize; font.features: PanelStyle.tabularFigures }
    }
    ControlCenterSection { centerRef: section.centerRef; visible: !!section.centerRef.mediaPlayer; text: Eitr.I18n.tr("Media"); width: parent.width }
    MediaCard { compact: true; visible: !!section.centerRef.mediaPlayer; width: parent.width; player: section.centerRef.mediaPlayer; active: section.centerRef.opened && section.centerRef.page === "general"; foreground: section.centerRef.foreground; accent: section.centerRef.accent }
}

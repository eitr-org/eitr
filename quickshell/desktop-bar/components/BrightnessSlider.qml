import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// The built-in screen's brightness (backlight displays only), applied a moment after the
// slider settles. Shared by the Control Center and Drop's quick controls.
Row {
    id: brightness
    required property var displayControl
    required property color foreground
    required property color accent
    visible: displayControl.state.kind === "backlight"
    spacing: 10
    Text { width: 30; height: 30; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; text: "󰃟"; color: brightness.foreground; font.family: DesktopFonts.family; font.pixelSize: 16 }
    PanelSlider {
        id: slider
        width: brightness.width - 100; from: 1; to: 100
        valueText: Math.round(value) + "%"
        foreground: brightness.foreground; accent: brightness.accent
        enabled: !!brightness.displayControl.state.available
        Binding { target: slider; property: "value"; value: brightness.displayControl.state.value; when: !slider.pressed }
        onMoved: settle.restart()
        Timer { id: settle; interval: 120; onTriggered: brightness.displayControl.applyValue(Math.round(slider.value)) }
    }
    Text { width: 50; height: 30; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignRight; text: brightness.displayControl.state.available ? brightness.displayControl.state.value + "%" : "--"; color: brightness.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize; font.features: PanelStyle.tabularFigures }
}

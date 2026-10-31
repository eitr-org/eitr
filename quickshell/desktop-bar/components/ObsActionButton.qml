import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

PanelButton {
    id: button
    required property var controller
    required property string action
    required property string description
    required property string glyph
    foreground: controller.foreground
    icon: true
    compactIconBackground: true
    text: ""
    height: 34
    available: controller.controlsReady
    loading: controller.pendingAction === action
    onClicked: controller.run(action)
    TextMetrics {
        id: glyphMetrics
        text: button.glyph
        font.family: DesktopFonts.family
        font.pixelSize: 18
    }
    Text {
        visible: !button.loading
        text: button.glyph
        font: glyphMetrics.font
        color: button.foreground
        x: (button.width - glyphMetrics.tightBoundingRect.width) / 2 - glyphMetrics.tightBoundingRect.x
        y: (button.height - glyphMetrics.tightBoundingRect.height) / 2 - glyphMetrics.tightBoundingRect.y - baselineOffset
    }
    HoverHandler { id: hover }
    BarTooltip {
        target: button
        hovered: hover.hovered
        text: button.description
        foreground: button.controller.foreground
        background: button.controller.background
    }
}

import "../.."
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle

// Drop's Performance page: one ring per component, from the Hardware panel's data. The
// hardware domain is observed only while this page is showing.
Row {
    id: page
    required property color foreground
    required property color accent
    required property bool watching
    property string token: ""
    readonly property var hardware: DesktopData.topics["hardware.details"]
    readonly property var sections: hardware && hardware.data && hardware.data.sections ? hardware.data.sections : []
    onWatchingChanged: {
        if (watching) token = DesktopData.observe("hardware.details", page);
        else if (token) { DesktopData.release(token); token = ""; }
    }
    Component.onDestruction: DesktopData.releaseOwner(page)
    spacing: 10
    Repeater {
        model: page.sections
        DropCard {
            id: ring
            required property var modelData
            foreground: page.foreground
            readonly property real share: Math.max(0, Math.min(1, (parseFloat(modelData.usage) || 0) / 100))
            width: (page.width - page.spacing * (page.sections.length - 1)) / Math.max(1, page.sections.length)
            height: 160
            Canvas {
                id: arc
                anchors.horizontalCenter: parent.horizontalCenter
                y: 16; width: 92; height: 92
                readonly property real share: ring.share
                onShareChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d");
                    context.reset();
                    context.lineWidth = 7; context.lineCap = "round";
                    context.strokeStyle = Qt.alpha(page.foreground, 0.15);
                    context.beginPath(); context.arc(46, 46, 40, 0, Math.PI * 2); context.stroke();
                    context.strokeStyle = page.accent;
                    context.beginPath(); context.arc(46, 46, 40, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * share); context.stroke();
                }
            }
            Text {
                anchors.centerIn: arc
                text: ring.modelData.usage
                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 16; font.weight: Font.DemiBold
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                y: arc.y + arc.height + 12
                text: ring.modelData.title
                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
        }
    }
    Text {
        visible: page.sections.length === 0
        text: Eitr.I18n.tr("Loading…")
        color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
}

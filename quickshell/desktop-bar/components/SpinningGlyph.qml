import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// A glyph that can spin in place. The text is centred in a square box and the box turns
// around its own centre, so the icon never drifts up and down while it spins (a Text
// item turns around its line box, which is taller than the glyph).
Item {
    id: spinner
    property string glyph: ""
    property color color: "white"
    property int size: 16
    property bool spinning: false
    width: size + 2
    height: width
    Text {
        id: glyphText
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        text: spinner.glyph
        color: spinner.color
        font.family: PanelStyle.fontFamily
        font.pixelSize: spinner.size
        RotationAnimator on rotation {
            from: 0
            to: 360
            duration: 900
            loops: Animation.Infinite
            running: !DesktopStyle.reduceMotion && spinner.visible && spinner.spinning
            onStopped: glyphText.rotation = 0
        }
    }
}

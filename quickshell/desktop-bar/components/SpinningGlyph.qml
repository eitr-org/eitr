import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// A glyph that can spin in place. Icon fonts draw a glyph off the centre of its line box,
// so the text is placed by its drawn shape (the font's tight bounding box) at the centre of
// a square, and the square turns: the icon stays put instead of circling while it spins.
Item {
    id: spinner
    property string glyph: ""
    property color color: "white"
    property int size: 16
    property bool spinning: false
    width: size + 2
    height: width
    TextMetrics {
        id: ink
        text: spinner.glyph
        font: glyphText.font
    }
    Item {
        id: turner
        anchors.fill: parent
        Text {
            id: glyphText
            // tightBoundingRect is measured from the baseline origin of the glyph.
            x: turner.width / 2 - (ink.tightBoundingRect.x + ink.tightBoundingRect.width / 2)
            y: turner.height / 2 - (baselineOffset + ink.tightBoundingRect.y + ink.tightBoundingRect.height / 2)
            text: spinner.glyph
            color: spinner.color
            font.family: PanelStyle.fontFamily
            font.pixelSize: spinner.size
        }
        RotationAnimator on rotation {
            from: 0
            to: 360
            duration: 900
            loops: Animation.Infinite
            running: !DesktopStyle.reduceMotion && spinner.visible && spinner.spinning
            onStopped: turner.rotation = 0
        }
    }
}
